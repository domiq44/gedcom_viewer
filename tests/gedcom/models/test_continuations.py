"""Tests des continuations GEDCOM : CONT et CONC."""

import unittest

from gedcom.models.note import Note
from gedcom.parser import GedcomParser

MULTILINE_BIG_LEVEL_GEDCOM = """0 @I10@ INDI
1 NAME Grant /Blue/
2 NOTE Hello
10 CONT world
11 CONC !
1 SEX M
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_BIRT_PLACE_GEDCOM = """0 @I7@ INDI
1 NAME David /Gray/
1 BIRT
2 DATE 15 APR 1950
2 PLAC New York
3 CONT NY
3 CONC , USA
1 SEX M
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_BIRT_PLAC_WITH_NESTED_TAG_GEDCOM = """0 @I15@ INDI
1 NAME Test /Nested/
1 BIRT
2 PLAC New York
3 SOUR @S1@
4 CONT source detail
3 CONT NY
1 SEX M
0 @S1@ SOUR
1 TITL Source
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_MULTIPLE_NOTES_GEDCOM = """0 @I6@ INDI
1 NAME Carol /White/
1 NOTE First note line
2 CONT continued line
2 CONC , more text
1 NOTE Second note line
2 CONC continuing text
1 SEX F
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_NAME_GEDCOM = """0 @I3@ INDI
1 NAME John
2 CONC /William/
2 CONT Doe
1 SEX M
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_NOTE_GEDCOM = """0 @I4@ INDI
1 NAME Alice /Smith/
1 NOTE Note first line
2 CONT second line
2 CONC  continuation
1 SEX F
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_NOTE_WITH_NESTED_CONTINUATION_GEDCOM = """0 @I16@ INDI
1 NAME Test /Nested/
1 NOTE Main note
2 SOUR @S1@
3 CONT source detail
2 CONT note detail
1 SEX M
0 @S1@ SOUR
1 TITL Source
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_NOTE_WITH_NESTED_TAG_GEDCOM = """0 @I14@ INDI
1 NAME Test /Nested/
1 NOTE Main note
2 SOUR @S1@
2 CONT continued after source
1 SEX M
0 @S1@ SOUR
1 TITL Source
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_PLACE_GEDCOM = """0 @I5@ INDI
1 NAME Bob /Brown/
1 BIRT
2 PLAC Paris
2 CONT Île-de-France
2 CONC , France
1 SEX M
0 HEAD
1 SOUR GEDCOM
"""


class TestGedcomContinuations(unittest.TestCase):
    """Vérifie la fusion des continuations CONT et CONC."""

    # Vérifie multiline name conc cont.
    def test_multiline_name_conc_cont(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_NAME_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I3@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(entity.get_tag_value("NAME"), "John/William/\nDoe")

    # Vérifie multiline note conc cont.
    def test_multiline_note_conc_cont(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_NOTE_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I4@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_tag_value("NOTE"), "Note first line\nsecond line continuation"
        )

    # Vérifie continuation under nested tag does not leak.
    def test_continuation_under_nested_tag_does_not_leak(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @I1@ INDI",
            "1 TEXT hello",
            "2 NOTE note",
            "3 CONT more",
            "1 NAME John",
            "0 TRLR",
        ]
        parser._parse_entities()

        entity = parser.get_entity("@I1@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.get_tag_values("TEXT"), ["hello"])
        self.assertEqual(entity.get_tag_values("NOTE"), ["note\nmore"])

    # Vérifie subtag continuation under nested tag does not leak.
    def test_subtag_continuation_under_nested_tag_does_not_leak(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @I1@ INDI",
            "1 BIRT",
            "2 PLAC New York",
            "3 NOTE note",
            "4 CONT more",
            "1 NAME John",
            "0 TRLR",
        ]
        parser._parse_entities()

        entity = parser.get_entity("@I1@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.get_subtag_values("BIRT", "PLAC"), ["New York"])

    # Vérifie note preserves repeated spaces in value.
    def test_note_preserves_repeated_spaces_in_value(self):
        parser = GedcomParser()
        parser.lines = [
            "0 HEAD",
            "0 @N20@ NOTE First  second",
            "0 TRLR",
        ]
        parser._parse_entities()

        note = Note(parser.get_entity("@N20@"))
        self.assertEqual(note.text, "First  second")

    # Vérifie multiline place conc cont.
    def test_multiline_place_conc_cont(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_PLACE_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I5@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_tag_values("PLAC"), ["Paris\nÎle-de-France, France"]
        )

    # Vérifie multiple note blocks with continuation.
    def test_multiple_note_blocks_with_continuation(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_MULTIPLE_NOTES_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I6@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_tag_values("NOTE"),
            [
                "First note line\ncontinued line, more text",
                "Second note linecontinuing text",
            ],
        )

    # Vérifie birt place continuation under birth.
    def test_birt_place_continuation_under_birth(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_BIRT_PLACE_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I7@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(entity.get_tag_values("PLAC"), ["New York\nNY, USA"])

    # Vérifie multiline big level continuation.
    def test_multiline_big_level_continuation(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_BIG_LEVEL_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I10@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(entity.get_tag_values("NOTE"), ["Hello\nworld!"])

    # Vérifie note continuation after nested tag is not absorbed.
    def test_note_continuation_after_nested_tag_is_preserved(self):
        # Given une note dont la continuation suit un tag imbriqué
        parser = GedcomParser()
        parser.lines = MULTILINE_NOTE_WITH_NESTED_TAG_GEDCOM.splitlines()
        parser._parse_entities()

        # When on extrait la note
        values = parser.get_entity("@I14@").get_tag_values("NOTE")

        # Then la continuation après un tag frère n'est pas absorbée par la note
        self.assertEqual(values, ["Main note"])

    # Vérifie note continuation does not absorb nested tag continuation.
    def test_note_continuation_does_not_absorb_nested_tag_continuation(self):
        # Given une note avec une continuation imbriquée et une continuation de note
        parser = GedcomParser()
        parser.lines = MULTILINE_NOTE_WITH_NESTED_CONTINUATION_GEDCOM.splitlines()
        parser._parse_entities()

        # When on extrait la note
        values = parser.get_entity("@I16@").get_tag_values("NOTE")

        # Then seule la continuation directe de la note est fusionnée ; celle après un tag frère ne l'est pas
        self.assertEqual(values, ["Main note"])

    # Vérifie subtag continuation after nested tag is not absorbed.
    def test_subtag_continuation_after_nested_tag_is_preserved(self):
        # Given un PLAC dont la continuation suit un tag imbriqué
        parser = GedcomParser()
        parser.lines = MULTILINE_BIRT_PLAC_WITH_NESTED_TAG_GEDCOM.splitlines()
        parser._parse_entities()

        # When on extrait les sous-tags PLAC de BIRT
        values = parser.get_entity("@I15@").get_subtag_values("BIRT", "PLAC")

        # Then la continuation après un tag frère n'est pas absorbée par le PLAC
        self.assertEqual(values, ["New York"])
