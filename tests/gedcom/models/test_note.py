"""Tests du modèle de note : texte, sources, références et métadonnées."""

import os
import tempfile
import unittest

from gedcom.models.note import Note
from gedcom.parser import GedcomParser

HEAD = (
    "0 HEAD\n1 SOUR T\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "1 CHAR UTF-8\n1 SUBM @U1@\n0 @U1@ SUBM\n1 NAME A\n0 @S1@ SOUR\n1 TITL X\n"
)


def build_note(record_block):
    """Charge un GEDCOM et retourne l'objet Note de l'enregistrement @N1@."""
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".ged", delete=False
    ) as handle:
        handle.write(HEAD + record_block + "0 TRLR\n")
        path = handle.name
    try:
        parser = GedcomParser()
        parser.load(path)
        return Note(parser.get_entity("@N1@"))
    finally:
        os.unlink(path)


class TestNote(unittest.TestCase):
    """Vérifie le texte, les sources, les références et les métadonnées d'une note."""

    # Vérifie text with continuations.
    def test_text_with_continuations(self):
        # Given (Arrange) une note avec CONT et CONC
        note = build_note("0 @N1@ NOTE Main text\n1 CONT line two\n1 CONC end\n")
        # When (Act) on lit le texte
        text = note.text
        # Then (Assert) les continuations sont fusionnées
        self.assertEqual(text, "Main text\nline twoend")

    # Vérifie source continuation does not leak into text.
    def test_source_continuation_does_not_leak_into_text(self):
        # Given une note avec une source et une continuation sous celle-ci
        note = build_note("0 @N1@ NOTE hello\n1 SOUR @S1@\n2 CONT page\n")
        # When on lit le texte
        text = note.text
        # Then le CONT de la source n'est pas ajouté au texte
        self.assertEqual(text, "hello")
        self.assertEqual(note.sources, ["@S1@"])

    # Vérifie sources.
    def test_sources(self):
        # Given (Arrange) une note avec une source
        note = build_note("0 @N1@ NOTE body\n1 SOUR @S1@\n")
        # When (Act) on lit les sources
        sources = note.sources
        # Then (Assert) la source est collectée
        self.assertEqual(sources, ["@S1@"])

    # Vérifie references and record id.
    def test_references_and_record_id(self):
        # Given (Arrange) une note avec REFN et RIN
        note = build_note("0 @N1@ NOTE body\n1 REFN RefA\n1 RIN RIN1\n")
        # When (Act) on lit références et identifiant
        references = note.references
        record_id = note.record_id
        # Then (Assert) les deux sont renseignés
        self.assertEqual(references, ["RefA"])
        self.assertEqual(record_id, "RIN1")

    # Vérifie submitters.
    def test_submitters(self):
        # Given (Arrange) une note avec un soumetteur
        note = build_note("0 @N1@ NOTE body\n1 SUBM @U1@\n")
        # When (Act) on lit les soumetteurs
        submitters = note.submitters
        # Then (Assert) le soumetteur est collecté
        self.assertEqual(submitters, ["@U1@"])

    # Vérifie change date and time.
    def test_change_date_and_time(self):
        # Given (Arrange) une note avec CHAN/DATE/TIME
        note = build_note("0 @N1@ NOTE body\n1 CHAN\n2 DATE 1 JAN 2020\n2 TIME 12:00\n")
        # When (Act) on lit la date et l'heure de modification
        date = note.change_date
        time = note.change_time
        # Then (Assert) les deux sont renseignés
        self.assertEqual(date, "1 JAN 2020")
        self.assertEqual(time, "12:00")

    # Vérifie additional fields with details.
    def test_additional_fields_with_details(self):
        # Given (Arrange) une note avec un champ additionnel et un détail
        note = build_note("0 @N1@ NOTE body\n1 EXTRA custom\n2 CHILD detail\n")
        # When (Act) on lit les champs additionnels
        fields = note.additional_fields
        # Then (Assert) le champ et son détail sont collectés
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["tag"], "EXTRA")
        self.assertEqual(fields[0]["details"], [("CHILD", "detail")])

    # Vérifie malformed line is ignored.
    def test_malformed_line_is_ignored(self):
        # Given une note contenant une ligne malformée
        note = build_note("0 @N1@ NOTE body\nmalformed line\n")

        # When on lit le texte
        # Then la ligne malformée est ignorée
        self.assertEqual(note.text, "body")

    # Vérifie continuation under note tag is appended.
    def test_continuation_under_note_tag_is_appended(self):
        # Given une note avec une continuation sous un tag NOTE
        note = build_note("0 @N1@ NOTE body\n1 NOTE extra\n2 CONT more\n")

        # When on lit le texte
        # Then la continuation est fusionnée
        self.assertEqual(note.text, "body\nextra\nmore")

    # Vérifie level one continuation after source is not appended to note.
    def test_level_one_continuation_after_source_is_appended(self):
        # Given une note avec une continuation de niveau 1 après une source
        note = build_note("0 @N1@ NOTE hello\n1 SOUR @S1@\n1 CONT page\n")

        # When on lit le texte
        text = note.text

        # Then la continuation après un tag frère n'est pas ajoutée au texte de la note
        self.assertEqual(text, "hello")


if __name__ == "__main__":
    unittest.main()
