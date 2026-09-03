import unittest
import tempfile
from gedcom.parser import GedcomEntity, GedcomParser
from gedcom.models.individual import Individual
from gedcom.models.note import Note
from gedcom.models.source import Source
from gedcom.models.submitter import Submitter
from gedcom.models.family import Family
from gedcom.models.event import Event

SAMPLE_GEDCOM = """0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 BIRT
2 DATE 1 JAN 1900
2 PLAC Paris
1 FAMS @F1@
0 @I2@ INDI
1 NAME Jane /Smith/
1 SEX F
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 MARR
2 DATE 12 JUN 1920
1 NOTE Example note
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

MULTILINE_BIRT_PLAC_SUBTAG_GEDCOM = """0 @I7@ INDI
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

MULTILINE_BIRT_DATE_BEFORE_PLAC_GEDCOM = """0 @I12@ INDI
1 NAME Eleanor /Frost/
1 BIRT
2 DATE 15 APR 1950
2 PLAC New York
3 CONT NY
3 CONC , USA
1 SEX F
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_DEEPER_SUBTAG_LEVEL_GEDCOM = """0 @I13@ INDI
1 NAME Greta /Winter/
1 BIRT
2 DATE 15 APR 1950
3 PLAC New York
4 CONT NY
4 CONC , USA
1 SEX F
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_MULTIPLE_BIRT_PLAC_GEDCOM = """0 @I7@ INDI
1 NAME David /Gray/
1 BIRT
2 PLAC New York
3 CONT NY
3 CONC , USA
2 DATE 15 APR 1950
1 MARR
2 DATE 1 JAN 1970
1 BIRT
2 PLAC Boston
1 SEX M
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_ADDR_PHONE_GEDCOM = """0 @I8@ INDI
1 NAME Emma /Black/
1 ADDR 123 Main Street
2 CONT Apt 4B
2 CONC , New York
1 PHON +1 555 1234
2 CONT ext 567
2 CONC , mobile
1 SEX F
0 HEAD
1 SOUR GEDCOM
"""

MALFORMED_HEAD_TRLR_GEDCOM = """0 @I10@ INDI
1 NAME Ivan /Silver/
0 HEAD
1 SOUR GEDCOM
0 @I11@ INDI
1 NAME John /Gold/
0 TRLR
"""

MISSING_TRLR_GEDCOM = """0 @I10@ INDI
1 NAME Ivan /Silver/
0 HEAD
1 SOUR GEDCOM
0 @I11@ INDI
1 NAME John /Gold/
"""

MULTIPLE_PHON_EMAIL_GEDCOM = """0 @I9@ INDI
1 NAME Fiona /Green/
1 PHON +1 555 0001
2 CONT ext 101
1 PHON +1 555 0002
2 CONC , work
1 EMAIL fiona@example.com
2 CONT secondary@example.com
1 SEX F
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_BIG_LEVEL_GEDCOM = """0 @I10@ INDI
1 NAME Grant /Blue/
2 NOTE Hello
10 CONT world
11 CONC !
1 SEX M
0 HEAD
1 SOUR GEDCOM
"""


class TestGedcomParser(unittest.TestCase):
    def test_parse_entities_and_pointers(self):
        parser = GedcomParser()
        parser.lines = SAMPLE_GEDCOM.splitlines()
        parser._parse_entities()

        self.assertIn("INDI", parser.entities)
        self.assertIn("FAM", parser.entities)
        self.assertEqual(parser.get_entity("@I1@").tag, "INDI")
        self.assertEqual(parser.get_entity("@F1@").tag, "FAM")

    def test_extract_head(self):
        parser = GedcomParser()
        parser.lines = SAMPLE_GEDCOM.splitlines()
        parser._parse_entities()

        head = parser.extract_head()
        self.assertIn("0 HEAD", head)
        self.assertIn("1 SOUR GEDCOM", head)

    def test_load_from_file(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(SAMPLE_GEDCOM)
            temp_path = temp_file.name

        parser = GedcomParser()
        parser.load(temp_path)

        self.assertEqual(parser.get_entity("@I1@").tag, "INDI")
        self.assertEqual(parser.get_entity("@F1@").tag, "FAM")
        self.assertIn("0 HEAD", parser.extract_head())

    def test_malformed_lines_are_recorded_and_logged(self):
        parser = GedcomParser()
        parser.lines = ["0 @I1@ INDI", "not a GEDCOM line", "1 NAME John /Doe/"]

        with self.assertLogs("gedcom.parser", level="WARNING") as logs:
            parser._parse_entities()

        self.assertEqual(parser.malformed_lines, [2])
        self.assertIn("Ligne GEDCOM malformée", logs.output[0])

    def test_invalid_encoding_is_counted_and_logged(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"0 @I1@ INDI\n1 NAME John \xffDoe\n")
            temp_file.flush()
            temp_path = temp_file.name

            parser = GedcomParser()
            with self.assertLogs("gedcom.parser", level="WARNING") as logs:
                parser.load(temp_path)

        self.assertEqual(parser.encoding_replacements, 1)
        self.assertIn("caractère(s) invalide(s) remplacé(s)", logs.output[0])

    def test_multiline_name_conc_cont(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_NAME_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I3@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(entity.get_tag_value("NAME"), "John /William/\nDoe")

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

    def test_individual_text_falls_back_when_entity_has_no_parser_helper(self):
        class DummyEntity:
            pointer = "@I99@"
            lines = [
                "1 TEXT This is the first line",
                "2 CONT continued on next line",
                "2 CONC  and still same paragraph",
            ]

        individual = Individual(DummyEntity())

        self.assertEqual(
            individual.texts,
            ["This is the first line\ncontinued on next line and still same paragraph"],
        )

    def test_note_entity_keeps_continuations(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @N10@ NOTE Première ligne",
            "1 CONT seconde ligne",
            "1 CONC  et encore plus",
            "1 SOUR @S1@",
            "0 HEAD",
            "1 SOUR GEDCOM",
        ]
        parser._parse_entities()

        entity = parser.get_entity("@N10@")
        self.assertIsNotNone(entity)

        note = Note(entity)
        self.assertEqual(
            note.text,
            "Première ligne\nseconde ligne et encore plus",
        )

    def test_source_keeps_notes_separately_from_text(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @S10@ SOUR",
            "1 TITL Source de test",
            "1 NOTE Première ligne",
            "2 CONT seconde ligne",
            "2 CONC , suite",
        ]
        parser._parse_entities()

        source = Source(parser.get_entity("@S10@"))

        self.assertIsNone(source.text)
        self.assertEqual(source.notes, ["Première ligne\nseconde ligne, suite"])

    def test_submitter_keeps_multiple_phones_and_emails(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @M10@ SUBM",
            "1 NAME Submitter",
            "1 PHON 01 02 03 04 05",
            "1 PHON 06 07 08 09 10",
            "1 EMAIL first@example.org",
            "1 EMAIL second@example.org",
        ]
        parser._parse_entities()

        submitter = Submitter(parser.get_entity("@M10@"))

        self.assertEqual(submitter.phones, ["01 02 03 04 05", "06 07 08 09 10"])
        self.assertEqual(
            submitter.emails, ["first@example.org", "second@example.org"]
        )
        self.assertEqual(submitter.phone, "06 07 08 09 10")
        self.assertEqual(submitter.email, "second@example.org")

    def test_family_events_use_event_model(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @F10@ FAM",
            "1 MARR",
            "2 DATE 1 JAN 1900",
            "1 DIV",
            "2 DATE 1 JAN 1910",
            "1 EVEN Reunion familiale",
            "2 TYPE Reunion",
        ]
        parser._parse_entities()

        family = Family(parser.get_entity("@F10@"))

        self.assertIsInstance(family.marriages[0], Event)
        self.assertEqual(family.marriages[0].get("details"), [("DATE", "1 JAN 1900")])
        self.assertIsInstance(family.divorces[0], Event)
        self.assertIsInstance(family.events[0], Event)
        self.assertEqual(family.events[0].value, "Reunion familiale")

    def test_death_confirmation_requires_y_value(self):
        without_confirmation = Individual(
            GedcomEntity(
                "@I20@", "INDI", 0, ["0 @I20@ INDI", "1 DEAT", "2 DATE 1 JAN 1900"]
            )
        )
        with_confirmation = Individual(
            GedcomEntity("@I21@", "INDI", 0, ["0 @I21@ INDI", "1 DEAT Y"])
        )

        self.assertFalse(without_confirmation.death_confirmed)
        self.assertTrue(with_confirmation.death_confirmed)

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
                "Second note line continuing text",
            ],
        )

    def test_birt_place_continuation_under_birth(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_BIRT_PLACE_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I7@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(entity.get_tag_values("PLAC"), ["New York\nNY, USA"])

    def test_birt_subtag_values_for_birth_place(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_BIRT_PLAC_SUBTAG_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I7@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_subtag_values("BIRT", "PLAC"), ["New York\nNY, USA"]
        )

    def test_multiple_birt_subtag_values_continue_scanning(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_MULTIPLE_BIRT_PLAC_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I7@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_subtag_values("BIRT", "PLAC"), ["New York\nNY, USA", "Boston"]
        )

    def test_birt_subtag_values_with_date_before_plac(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_BIRT_DATE_BEFORE_PLAC_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I12@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_subtag_values("BIRT", "PLAC"), ["New York\nNY, USA"]
        )

    def test_subtag_values_accept_deeper_nested_level(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_DEEPER_SUBTAG_LEVEL_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I13@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_subtag_values("BIRT", "PLAC"), ["New York\nNY, USA"]
        )

    def test_address_and_phone_continuation(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_ADDR_PHONE_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I8@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_tag_values("ADDR"), ["123 Main Street\nApt 4B, New York"]
        )
        self.assertEqual(
            entity.get_tag_values("PHON"), ["+1 555 1234\next 567, mobile"]
        )

    def test_multiple_phone_and_email_continuation(self):
        parser = GedcomParser()
        parser.lines = MULTIPLE_PHON_EMAIL_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I9@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_tag_values("PHON"), ["+1 555 0001\next 101", "+1 555 0002, work"]
        )
        self.assertEqual(
            entity.get_tag_values("EMAIL"), ["fiona@example.com\nsecondary@example.com"]
        )

    def test_extract_head_skips_following_records(self):
        parser = GedcomParser()
        parser.lines = MALFORMED_HEAD_TRLR_GEDCOM.splitlines()
        parser._parse_entities()

        head = parser.extract_head()
        self.assertIn("0 HEAD", head)
        self.assertIn("1 SOUR GEDCOM", head)
        self.assertNotIn("0 @I11@ INDI", head)

    def test_extract_trailer_returns_empty_when_missing(self):
        parser = GedcomParser()
        parser.lines = MISSING_TRLR_GEDCOM.splitlines()
        parser._parse_entities()

        self.assertEqual(parser.extract_trailer(), "")

    def test_multiline_big_level_continuation(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_BIG_LEVEL_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I10@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(entity.get_tag_values("NOTE"), ["Hello\nworld!"])


if __name__ == "__main__":
    unittest.main()
