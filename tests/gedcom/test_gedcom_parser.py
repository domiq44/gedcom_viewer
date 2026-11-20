"""Tests du parseur GEDCOM : parsing, extraction et cache des lignes."""

import threading
import unittest

from gedcom.errors import GedcomLoadCancelled
from gedcom.models.entity import GedcomEntity
from gedcom.parser import GedcomParser
from tests.gedcom.test_gedcom_parser_common import (
    MALFORMED_HEAD_TRLR_GEDCOM,
    MISSING_TRLR_GEDCOM,
    SAMPLE_GEDCOM,
)
from tests.temp_file_factory import write_temp_bytes, write_temp_text


class TestGedcomParser(unittest.TestCase):
    """Vérifie le parsing, l'extraction et le cache des lignes GEDCOM."""

    # Vérifie parse entities and pointers.
    def test_parse_entities_and_pointers(self):
        parser = GedcomParser()
        parser.lines = SAMPLE_GEDCOM.splitlines()
        parser._parse_entities()

        self.assertIn("INDI", parser.entities)
        self.assertIn("FAM", parser.entities)
        self.assertEqual(parser.get_entity("@I1@").tag, "INDI")
        self.assertEqual(parser.get_entity("@F1@").tag, "FAM")

    # Vérifie extract head.
    def test_extract_head(self):
        parser = GedcomParser()
        parser.lines = SAMPLE_GEDCOM.splitlines()
        parser._parse_entities()

        head = parser.extract_head()
        self.assertIn("0 HEAD", head)
        self.assertIn("1 SOUR GEDCOM", head)

    # Vérifie extract head falls back to lines without head entity.
    def test_extract_head_falls_back_to_lines_without_head_entity(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "invalid", "1 SOUR X", "0 @I1@ INDI"]

        self.assertEqual(parser.extract_head(), "0 HEAD\n1 SOUR X")

    # Vérifie extract head has same format with and without head entity.
    def test_extract_head_has_same_format_with_and_without_head_entity(self):
        # Given un parseur avec un enregistrement HEAD indexé
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "1 SOUR X", "0 TRLR"]
        parser._parse_entities()

        # When on extrait le bloc HEAD
        block = parser.extract_head()

        # Then le format est identique à celui d'une reconstruction sans entité
        parser.entities.clear()
        self.assertEqual(block, parser.extract_head())

    # Vérifie load from file.
    def test_load_from_file(self):
        temp_path = write_temp_text(self, SAMPLE_GEDCOM)

        parser = GedcomParser()
        parser.load(temp_path)

        self.assertEqual(parser.get_entity("@I1@").tag, "INDI")
        self.assertEqual(parser.get_entity("@F1@").tag, "FAM")
        self.assertIn("0 HEAD", parser.extract_head())

    # Vérifie load raises when cancelled.
    def test_load_raises_when_cancelled(self):
        # Given un fichier GEDCOM et une annulation déjà demandée
        temp_path = write_temp_text(self, SAMPLE_GEDCOM)
        cancel_event = threading.Event()
        cancel_event.set()

        # When on charge le fichier avec annulation
        # Then le chargement s'interrompt immédiatement
        parser = GedcomParser()
        with self.assertRaises(GedcomLoadCancelled):
            parser.load(temp_path, cancel_event=cancel_event)

    # Vérifie loaded entities share parser line store.
    def test_loaded_entities_share_parser_line_store(self):
        content = "0 HEAD\n0 @I1@ INDI\n1 NAME John /Doe/\n0 TRLR"
        temp_path = write_temp_text(self, content)

        parser = GedcomParser()
        parser.load(temp_path)

        entity = parser.get_entity("@I1@")
        self.assertIs(entity._source_lines, parser.lines)
        self.assertEqual(entity.lines[0], parser.lines[1])
        self.assertEqual(entity.raw_block(), "0 @I1@ INDI\n1 NAME John /Doe/\n")

    # Vérifie entity lines are cached after first access.
    def test_entity_lines_are_cached_after_first_access(self):
        # Given une entité construite depuis les lignes du parseur
        parser = GedcomParser()
        parser.lines = SAMPLE_GEDCOM.splitlines()
        parser._parse_entities()
        entity = parser.get_entity("@I1@")

        # When on accède deux fois à ses lignes
        first_access = entity.lines
        second_access = entity.lines

        # Then la même liste est renvoyée
        self.assertIs(first_access, second_access)

    # Vérifie entity raw block omits malformed lines.
    def test_entity_raw_block_omits_malformed_lines(self):
        parser = GedcomParser()
        parser.lines = [
            "0 HEAD",
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "malformed line",
            "0 TRLR",
        ]
        parser._parse_entities()

        self.assertEqual(
            parser.get_entity("@I1@").raw_block(),
            "0 @I1@ INDI\n1 NAME John /Doe/\n",
        )

    # Vérifie white box malformed entity lines are loaded lazily.
    def test_white_box_malformed_entity_lines_are_loaded_lazily(self):
        # Given une entité contenant une ligne malformée
        parser = GedcomParser()
        parser.lines = [
            "0 HEAD",
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "malformed line",
            "0 TRLR",
        ]
        parser._parse_entities()
        entity = parser.get_entity("@I1@")

        # When on n'accède pas encore aux lignes
        # Then le filtrage n'a pas été matérialisé
        self.assertIsNone(entity._lines)

        # When on accède aux lignes
        lines = entity.lines

        # Then les lignes malformées sont exclues
        self.assertEqual(lines, ["0 @I1@ INDI\n", "1 NAME John /Doe/\n"])

    # Vérifie malformed lines are recorded and logged.
    def test_malformed_lines_are_recorded_and_logged(self):
        parser = GedcomParser()
        private_content = "private data: John /Doe/"
        parser.lines = ["0 @I1@ INDI", private_content, "1 NAME John /Doe/"]

        with self.assertLogs("gedcom.parser", level="WARNING") as logs:
            parser._parse_entities()

        self.assertEqual(parser.malformed_lines, [2])
        self.assertEqual(len(logs.output), 1)
        self.assertIn("malformée", logs.output[0])
        self.assertIn("(2)", logs.output[0])
        self.assertNotIn(private_content, logs.output[0])

    # Vérifie le bornage et l'agrégation des lignes malformées.
    def test_malformed_lines_are_capped_and_aggregated(self):
        # Given un enregistrement suivi de nombreuses lignes malformées
        parser = GedcomParser()
        parser.lines = ["0 @I1@ INDI"] + ["invalid"] * 150

        # When on analyse les lignes
        with self.assertLogs("gedcom.parser", level="WARNING") as logs:
            parser._parse_entities()

        # Then le rapport est borné et un seul avertissement est émis
        self.assertEqual(len(parser.malformed_lines), GedcomParser.MAX_MALFORMED_LINES)
        self.assertEqual(parser.malformed_count, 150)
        self.assertEqual(len(logs.output), 1)

    # Vérifie extract head skips following records.
    def test_extract_head_skips_following_records(self):
        parser = GedcomParser()
        parser.lines = MALFORMED_HEAD_TRLR_GEDCOM.splitlines()
        parser._parse_entities()

        head = parser.extract_head()
        self.assertIn("0 HEAD", head)
        self.assertIn("1 SOUR GEDCOM", head)
        self.assertNotIn("0 @I11@ INDI", head)

    # Vérifie extract trailer returns empty when missing.
    def test_extract_trailer_returns_empty_when_missing(self):
        parser = GedcomParser()
        parser.lines = MISSING_TRLR_GEDCOM.splitlines()
        parser._parse_entities()

        self.assertEqual(parser.extract_trailer(), "")

    # Vérifie extract trailer returns normalized block for known trailer.
    def test_extract_trailer_returns_normalized_block_for_known_trailer(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "0 TRLR"]
        parser._parse_entities()

        self.assertEqual(parser.extract_trailer(), "0 TRLR")

    # Vérifie extract trailer falls back to lines without trailer entity.
    def test_extract_trailer_falls_back_to_lines_without_trailer_entity(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "invalid", "0 TRLR", "0 @I1@ INDI"]

        self.assertEqual(parser.extract_trailer(), "0 TRLR")

    # Vérifie extract trailer falls back to lines with sublines.
    def test_extract_trailer_falls_back_to_lines_with_sublines(self):
        parser = GedcomParser()
        parser.lines = ["0 TRLR", "1 NOTE ignored"]

        self.assertEqual(parser.extract_trailer(), "0 TRLR\n1 NOTE ignored")

    # Vérifie register entity ignores entity without tag white box.
    def test_register_entity_ignores_entity_without_tag_white_box(self):
        # Given un parseur et une entité sans tag
        parser = GedcomParser()

        # When on enregistre l'entité
        with self.assertLogs("gedcom.parser", level="WARNING") as logs:
            parser._register_entity(GedcomEntity(None, None, 0, []))

        # Then l'entité est ignorée avec un avertissement
        self.assertEqual(parser.entities, {})
        self.assertIn("sans tag", logs.output[0])

    # Vérifie invalid encoding is counted and logged.
    def test_invalid_encoding_is_counted_and_logged(self):
        temp_path = write_temp_bytes(self, b"0 @I1@ INDI\n1 NAME John \xffDoe\n")

        parser = GedcomParser()
        with self.assertLogs("gedcom.parser", level="WARNING") as logs:
            parser.load(temp_path)

        self.assertEqual(parser.encoding_replacements, 1)
        self.assertIn("caractère(s) invalide(s) remplacé(s)", logs.output[0])
        self.assertNotIn(temp_path, logs.output[0])

    # Vérifie valid replacement character is not counted as decode error.
    def test_valid_replacement_character_is_not_counted_as_decode_error(self):
        temp_path = write_temp_bytes(
            self, b"0 @I1@ INDI\n1 NAME A\xef\xbf\xbd \xff B\n"
        )

        parser = GedcomParser()
        parser.load(temp_path)

        self.assertEqual(parser.encoding_replacements, 1)
        self.assertEqual(
            parser.get_entity("@I1@").get_tag_value("NAME"), "A\ufffd \ufffd B"
        )


if __name__ == "__main__":
    unittest.main()
