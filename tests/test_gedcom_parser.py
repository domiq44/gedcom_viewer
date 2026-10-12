import unittest
import tempfile
from gedcom.parser import GedcomEntity, GedcomParser
from gedcom.models.individual import Individual
from gedcom.models.note import Note
from gedcom.models.source import Source
from gedcom.models.submitter import Submitter
from gedcom.models.family import Family
from gedcom.models.event import Event
from gedcom.models.object import MultimediaObject
from gedcom.models.repository import Repository

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

    def test_loaded_entities_reuse_parser_line_strings(self):
        content = "0 HEAD\n0 @I1@ INDI\n1 NAME John /Doe/\n0 TRLR"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as temp_file:
            temp_file.write(content)
            temp_file.flush()

            parser = GedcomParser()
            parser.load(temp_file.name)

        entity = parser.get_entity("@I1@")
        self.assertIs(entity.lines[0], parser.lines[1])
        self.assertEqual(entity.raw_block(), "0 @I1@ INDI\n1 NAME John /Doe/\n")

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

    def test_load_records_validation_errors(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as temp_file:
            temp_file.write("0 HEAD\n1 SOUR TEST\n")
            temp_file.flush()
            parser = GedcomParser()
            parser.load(temp_file.name)

        self.assertIn("TRLR absent ou multiple", parser.validation_errors)

    def test_validate_requires_head_first_and_trlr_last(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "0 HEAD",
            "0 TRLR",
            "0 @I2@ INDI",
        ]
        parser._parse_entities()

        errors = parser.validate()

        self.assertIn("HEAD doit être le premier enregistrement", errors)
        self.assertIn("TRLR doit être le dernier enregistrement ligne 4", errors)

    def test_validate_rejects_nested_head_and_trailer_tags(self):
        invalid_contexts = [
            ("1 HEAD", "HEAD doit être au niveau 0 ligne 3"),
            ("1 TRLR", "TRLR doit être au niveau 0 ligne 3"),
        ]

        for nested_record, expected_error in invalid_contexts:
            with self.subTest(nested_record=nested_record):
                parser = GedcomParser()
                parser.lines = [
                    "0 HEAD",
                    "0 @I1@ INDI",
                    nested_record,
                    "0 TRLR",
                ]
                parser._parse_entities()

                self.assertIn(expected_error, parser.validate())

    def test_validate_requires_pointers_for_indexed_record_types(self):
        record_types = ("INDI", "FAM", "SOUR", "REPO", "SUBM", "OBJE")
        for record_type in record_types:
            with self.subTest(record_type=record_type):
                parser = GedcomParser()
                parser.lines = ["0 HEAD", f"0 {record_type}", "0 TRLR"]
                parser._parse_entities()

                self.assertIn(
                    f"pointeur manquant pour l'enregistrement {record_type} ligne 2",
                    parser.validate(),
                )

        inline_note_parser = GedcomParser()
        inline_note_parser.lines = ["0 HEAD", "0 NOTE Inline note", "0 TRLR"]
        inline_note_parser._parse_entities()
        self.assertEqual(inline_note_parser.validate(), [])

    def test_strict_load_rejects_trailer_subrecords(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as temp_file:
            temp_file.write("0 HEAD\n0 TRLR\n1 NOTE invalid\n")
            temp_file.flush()
            parser = GedcomParser()

            with self.assertRaisesRegex(ValueError, "TRLR ne doit pas contenir"):
                parser.load(temp_file.name, strict=True)

    def test_duplicate_pointer_keeps_first_entity_for_resolution(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @I1@ INDI",
            "1 NAME First /Person/",
            "0 @I1@ INDI",
            "1 NAME Second /Person/",
        ]

        with self.assertLogs("gedcom.parser", level="WARNING") as logs:
            parser._parse_entities()

        self.assertEqual(
            parser.get_entity("@I1@").get_tag_value("NAME"), "First /Person/"
        )
        self.assertIn("Pointeur GEDCOM dupliqué", logs.output[0])

    def test_validate_reports_duplicate_pointer(self):
        parser = GedcomParser()
        parser.lines = [
            "0 HEAD",
            "0 @I1@ INDI",
            "0 @I1@ INDI",
            "0 TRLR",
        ]
        parser._parse_entities()

        self.assertIn("pointeur dupliqué @I1@", parser.validate())

    def test_validate_reports_unknown_pointer_reference(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @F1@ FAM",
            "1 HUSB @I404@",
            "0 HEAD",
            "1 SOUR GEDCOM",
            "0 TRLR",
        ]
        parser._parse_entities()

        self.assertIn("référence inconnue @I404@ ligne 2", parser.validate())

    def test_validate_reports_malformed_reference_pointer(self):
        parser = GedcomParser()
        parser.lines = [
            "0 HEAD",
            "0 @F1@ FAM",
            "1 HUSB @I1",
            "0 TRLR",
        ]
        parser._parse_entities()

        self.assertIn("pointeur de référence invalide @I1 ligne 3", parser.validate())

    def test_validate_reports_missing_required_reference_pointer(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "0 @F1@ FAM", "1 HUSB", "0 TRLR"]
        parser._parse_entities()

        self.assertIn(
            "pointeur de référence manquant pour HUSB ligne 3", parser.validate()
        )

    def test_validate_reports_reference_with_unexpected_entity_type(self):
        parser = GedcomParser()
        parser.lines = [
            "0 HEAD",
            "0 @F1@ FAM",
            "1 HUSB @F1@",
            "0 TRLR",
        ]
        parser._parse_entities()

        self.assertIn(
            "référence @F1@ de type FAM incompatible avec HUSB "
            "(type INDI attendu) ligne 3",
            parser.validate(),
        )

    def test_validate_checks_alias_reference(self):
        def validate_alias(alias_pointer, target_record=None):
            parser = GedcomParser()
            parser.lines = [
                "0 HEAD",
                "0 @I1@ INDI",
                f"1 ALIA {alias_pointer}",
                *([target_record] if target_record else []),
                "0 TRLR",
            ]
            parser._parse_entities()
            return parser.validate()

        self.assertIn(
            "référence inconnue @I404@ ligne 3",
            validate_alias("@I404@"),
        )
        self.assertIn(
            "référence @F1@ de type FAM incompatible avec ALIA "
            "(type INDI attendu) ligne 3",
            validate_alias("@F1@", "0 @F1@ FAM"),
        )
        self.assertIn(
            "pointeur de référence manquant pour ALIA ligne 3",
            validate_alias(""),
        )
        self.assertEqual(
            validate_alias("@I2@", "0 @I2@ INDI"),
            [],
        )

    def test_validate_rejects_alias_outside_level_one_indi(self):
        invalid_contexts = [
            [
                "0 HEAD",
                "0 @I1@ INDI",
                "0 @F1@ FAM",
                "1 ALIA @I1@",
                "0 TRLR",
            ],
            [
                "0 HEAD",
                "0 @I1@ INDI",
                "1 NAME Jane /Doe/",
                "2 ALIA @I1@",
                "0 TRLR",
            ],
        ]

        for lines in invalid_contexts:
            with self.subTest(lines=lines):
                parser = GedcomParser()
                parser.lines = lines
                parser._parse_entities()

                self.assertTrue(
                    any(
                        "ALIA doit être au niveau 1 d'un enregistrement INDI" in e
                        for e in parser.validate()
                    )
                )

    def test_validate_rejects_family_links_outside_source_records(self):
        invalid_contexts = [
            (
                [
                    "0 HEAD",
                    "0 @I1@ INDI",
                    "1 HUSB @I2@",
                    "0 @I2@ INDI",
                    "0 TRLR",
                ],
                "HUSB",
                "FAM",
            ),
            (
                [
                    "0 HEAD",
                    "0 @I1@ INDI",
                    "1 WIFE @I2@",
                    "0 @I2@ INDI",
                    "0 TRLR",
                ],
                "WIFE",
                "FAM",
            ),
            (
                [
                    "0 HEAD",
                    "0 @I1@ INDI",
                    "1 CHIL @I2@",
                    "0 @I2@ INDI",
                    "0 TRLR",
                ],
                "CHIL",
                "FAM",
            ),
            (
                [
                    "0 HEAD",
                    "0 @F1@ FAM",
                    "1 FAMC @F2@",
                    "0 @F2@ FAM",
                    "0 TRLR",
                ],
                "FAMC",
                "INDI",
            ),
            (
                [
                    "0 HEAD",
                    "0 @F1@ FAM",
                    "1 FAMS @F2@",
                    "0 @F2@ FAM",
                    "0 TRLR",
                ],
                "FAMS",
                "INDI",
            ),
        ]

        for lines, reference_tag, expected_source in invalid_contexts:
            with self.subTest(reference_tag=reference_tag):
                parser = GedcomParser()
                parser.lines = lines
                parser._parse_entities()

                self.assertTrue(
                    any(
                        f"{reference_tag} doit être au niveau 1 d'un enregistrement "
                        f"{expected_source}" in error
                        for error in parser.validate()
                    )
                )

    def test_validate_distinguishes_submitter_and_repository_records(self):
        parser = GedcomParser()
        parser.lines = [
            "0 HEAD",
            "1 SUBM @M1@",
            "0 @M1@ SUBM",
            "1 NAME Submitter",
            "0 @R1@ REPO",
            "1 NAME Repository",
            "0 @S1@ SOUR",
            "1 REPO @R1@",
            "0 TRLR",
        ]
        parser._parse_entities()

        self.assertEqual(parser.validate(), [])

        parser.lines = [
            "0 HEAD",
            "1 SUBM @M1@",
            "0 @M1@ SUBM",
            "0 @I1@ INDI",
            "1 SUBM @M1@",
            "0 TRLR",
        ]
        parser._parse_entities()

        self.assertIn(
            "SUBM doit être au niveau 1 d'un enregistrement HEAD ligne 5",
            parser.validate(),
        )

    def test_validate_checks_association_and_repository_contexts(self):
        valid_parser = GedcomParser()
        valid_parser.lines = [
            "0 HEAD",
            "0 @I1@ INDI",
            "1 ASSO @I2@",
            "0 @I2@ INDI",
            "0 @R1@ REPO",
            "0 @S1@ SOUR",
            "1 REPO @R1@",
            "0 TRLR",
        ]
        valid_parser._parse_entities()

        self.assertEqual(valid_parser.validate(), [])

        invalid_contexts = [
            (
                [
                    "0 HEAD",
                    "0 @F1@ FAM",
                    "1 ASSO @I1@",
                    "0 @I1@ INDI",
                    "0 TRLR",
                ],
                "ASSO",
                "INDI",
            ),
            (
                [
                    "0 HEAD",
                    "0 @I1@ INDI",
                    "1 REPO @R1@",
                    "0 @R1@ REPO",
                    "0 TRLR",
                ],
                "REPO",
                "SOUR",
            ),
        ]

        for lines, reference_tag, expected_source in invalid_contexts:
            with self.subTest(reference_tag=reference_tag):
                parser = GedcomParser()
                parser.lines = lines
                parser._parse_entities()

                self.assertTrue(
                    any(
                        f"{reference_tag} doit être au niveau 1 d'un enregistrement "
                        f"{expected_source}" in error
                        for error in parser.validate()
                    )
                )

    def test_validate_accepts_reference_with_expected_entity_type(self):
        parser = GedcomParser()
        parser.lines = [
            "0 HEAD",
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "0 @I1@ INDI",
            "0 TRLR",
        ]
        parser._parse_entities()

        self.assertEqual(parser.validate(), [])

    def test_strict_load_rejects_reference_with_unexpected_entity_type(self):
        content = "0 HEAD\n0 @F1@ FAM\n1 HUSB @F1@\n0 TRLR\n"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as temp_file:
            temp_file.write(content)
            temp_file.flush()
            parser = GedcomParser()

            with self.assertRaisesRegex(ValueError, "type INDI attendu"):
                parser.load(temp_file.name, strict=True)

    def test_strict_load_rejects_malformed_reference_pointer(self):
        content = "0 HEAD\n0 @F1@ FAM\n1 HUSB @I1\n0 TRLR\n"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as temp_file:
            temp_file.write(content)
            temp_file.flush()
            parser = GedcomParser()

            with self.assertRaisesRegex(ValueError, "pointeur de référence invalide"):
                parser.load(temp_file.name, strict=True)

    def test_strict_load_rejects_missing_required_reference_pointer(self):
        content = "0 HEAD\n0 @F1@ FAM\n1 HUSB\n0 TRLR\n"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as temp_file:
            temp_file.write(content)
            temp_file.flush()
            parser = GedcomParser()

            with self.assertRaisesRegex(ValueError, "pointeur de référence manquant"):
                parser.load(temp_file.name, strict=True)

    def test_strict_load_rejects_invalid_structure(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as temp_file:
            temp_file.write("0 HEAD\n1 SOUR TEST\n")
            temp_file.flush()
            parser = GedcomParser()

            with self.assertRaises(ValueError):
                parser.load(temp_file.name, strict=True)

    def test_strict_load_rejects_blank_lines(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as temp_file:
            temp_file.write("0 HEAD\n\n0 TRLR\n")
            temp_file.flush()
            parser = GedcomParser()

            with self.assertRaisesRegex(ValueError, "ligne 2 malformée"):
                parser.load(temp_file.name, strict=True)

    def test_strict_load_rejects_values_on_head_and_trailer(self):
        invalid_records = (
            ("0 HEAD extra\n0 TRLR\n", "HEAD ne doit pas avoir de valeur ligne 1"),
            ("0 HEAD\n0 TRLR value\n", "TRLR ne doit pas avoir de valeur ligne 2"),
        )

        for content, expected_error in invalid_records:
            with self.subTest(expected_error=expected_error):
                with tempfile.NamedTemporaryFile("w", encoding="utf-8") as temp_file:
                    temp_file.write(content)
                    temp_file.flush()
                    parser = GedcomParser()

                    with self.assertRaisesRegex(ValueError, expected_error):
                        parser.load(temp_file.name, strict=True)

    def test_validate_reports_malformed_line(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "invalid GEDCOM line", "0 TRLR"]
        parser._parse_entities()

        self.assertIn("ligne 2 malformée", parser.validate())

    def test_validate_reports_blank_line(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "", "0 TRLR"]
        parser._parse_entities()

        self.assertIn("ligne 2 malformée", parser.validate())

    def test_validate_reports_line_without_tag(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "1", "0 TRLR"]
        parser._parse_entities()

        self.assertIn("ligne 2 malformée", parser.validate())

    def test_malformed_lines_are_recorded_and_logged(self):
        parser = GedcomParser()
        private_content = "private data: John /Doe/"
        parser.lines = ["0 @I1@ INDI", private_content, "1 NAME John /Doe/"]

        with self.assertLogs("gedcom.parser", level="WARNING") as logs:
            parser._parse_entities()

        self.assertEqual(parser.malformed_lines, [2])
        self.assertIn("Ligne GEDCOM malformée", logs.output[0])
        self.assertIn("(2)", logs.output[0])
        self.assertNotIn(private_content, logs.output[0])

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
        self.assertNotIn(temp_path, logs.output[0])

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

    def test_empty_individual_lists_are_lazy_and_mutable(self):
        class DummyEntity:
            pointer = "@I100@"
            lines = ["0 @I100@ INDI", "1 NAME Jane /Doe/"]

        individual = Individual(DummyEntity())

        self.assertIsNone(individual._notes)
        notes = individual.notes
        self.assertEqual(notes, [])
        self.assertIs(individual.notes, notes)
        notes.append("Research note")
        self.assertEqual(individual.notes, ["Research note"])

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

    def test_empty_note_lists_are_lazy_and_mutable(self):
        note = Note(
            GedcomEntity(
                "@N20@",
                "NOTE",
                0,
                ["0 @N20@ NOTE Archival note text"],
            )
        )

        self.assertFalse(hasattr(note, "__dict__"))
        self.assertIsNone(note._sources)
        sources = note.sources
        self.assertEqual(sources, [])
        self.assertIs(note.sources, sources)
        sources.append("@S1@")
        self.assertEqual(note.sources, ["@S1@"])

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

    def test_source_data_events_are_loaded_lazily(self):
        source = Source(
            GedcomEntity(
                "@S11@",
                "SOUR",
                0,
                [
                    "0 @S11@ SOUR",
                    "1 DATA",
                    "2 AGNC Registry",
                    "2 EVEN Census",
                    "2 DATE 1900",
                    "2 AGNC Event agency",
                ],
            )
        )

        self.assertFalse(source._data_events_loaded)
        self.assertIsNone(source._data_events)
        self.assertEqual(source.agency, "Registry")
        self.assertEqual(source.text, None)

        self.assertEqual(
            source.data_events,
            [
                {
                    "value": "Census",
                    "details": [("DATE", "1900"), ("AGNC", "Event agency")],
                }
            ],
        )
        self.assertTrue(source._data_events_loaded)

    def test_empty_repository_lists_are_lazy_and_mutable(self):
        repository = Repository(
            GedcomEntity(
                "@R20@",
                "REPO",
                0,
                ["0 @R20@ REPO", "1 NAME City archive"],
            )
        )

        self.assertFalse(hasattr(repository, "__dict__"))
        self.assertIsNone(repository._references)
        references = repository.references
        self.assertEqual(references, [])
        self.assertIs(repository.references, references)
        references.append("@S1@")
        self.assertEqual(repository.references, ["@S1@"])

    def test_empty_source_lists_are_lazy_and_mutable(self):
        source = Source(
            GedcomEntity(
                "@S20@",
                "SOUR",
                0,
                ["0 @S20@ SOUR", "1 TITL Parish register"],
            )
        )

        self.assertFalse(hasattr(source, "__dict__"))
        self.assertIsNone(source._notes)
        notes = source.notes
        self.assertEqual(notes, [])
        self.assertIs(source.notes, notes)
        notes.append("Reference note")
        self.assertEqual(source.notes, ["Reference note"])

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
        self.assertEqual(submitter.emails, ["first@example.org", "second@example.org"])
        self.assertEqual(submitter.phone, "06 07 08 09 10")
        self.assertEqual(submitter.email, "second@example.org")

    def test_empty_submitter_lists_are_lazy_and_mutable(self):
        submitter = Submitter(
            GedcomEntity(
                "@M20@",
                "SUBM",
                0,
                ["0 @M20@ SUBM", "1 NAME Archive office"],
            )
        )

        self.assertFalse(hasattr(submitter, "__dict__"))
        self.assertIsNone(submitter._phones)
        phones = submitter.phones
        self.assertEqual(phones, [])
        self.assertIs(submitter.phones, phones)
        phones.append("555-0100")
        self.assertEqual(submitter.phones, ["555-0100"])

    def test_multimedia_object_uses_slots_and_preserves_fields(self):
        multimedia = MultimediaObject(
            GedcomEntity(
                "@O20@",
                "OBJE",
                0,
                [
                    "0 @O20@ OBJE",
                    "1 FILE family-photo.jpg",
                    "1 TITL Family photo",
                    "1 FORM jpeg",
                ],
            )
        )

        self.assertFalse(hasattr(multimedia, "__dict__"))
        self.assertEqual(multimedia.pointer, "@O20@")
        self.assertEqual(multimedia.file, "family-photo.jpg")
        self.assertEqual(multimedia.title, "Family photo")
        self.assertEqual(multimedia.format, "jpeg")

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

        self.assertFalse(family._event_models_loaded)
        self.assertIsNone(family._marriages)
        self.assertIsNone(family._divorces)
        self.assertIsNone(family._events)
        self.assertIsInstance(family.marriages[0], Event)
        self.assertTrue(family._event_models_loaded)
        self.assertEqual(family.marriages[0].get("details"), [("DATE", "1 JAN 1900")])
        self.assertIsInstance(family.divorces[0], Event)
        self.assertIsInstance(family.events[0], Event)
        self.assertEqual(family.events[0].value, "Reunion familiale")

    def test_event_details_are_lazy_and_mutable(self):
        event = Event("MARR")

        self.assertFalse(hasattr(event, "__dict__"))
        self.assertIsNone(event._details)
        details = event.details
        self.assertEqual(details, [])
        self.assertIs(event.get("details"), details)
        details.append(("DATE", "1 JAN 1900"))
        self.assertEqual(event.details, [("DATE", "1 JAN 1900")])

    def test_empty_family_lists_are_lazy_and_mutable(self):
        family = Family(
            GedcomEntity(
                "@F20@",
                "FAM",
                0,
                ["0 @F20@ FAM", "1 HUSB @I1@", "1 WIFE @I2@"],
            )
        )

        self.assertFalse(hasattr(family, "__dict__"))
        self.assertIsNone(family._notes)
        notes = family.notes
        self.assertEqual(notes, [])
        self.assertIs(family.notes, notes)
        notes.append("Research note")
        self.assertEqual(family.notes, ["Research note"])

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

    def test_individual_builds_nested_event_tree(self):
        individual = Individual(
            GedcomEntity(
                "@I22@",
                "INDI",
                0,
                [
                    "0 @I22@ INDI",
                    "1 NAME John /Doe/",
                    "1 SEX M",
                    "1 FAMC @F1@",
                    "1 BAPM",
                    "2 DATE 22 JUN 1963",
                    "2 PLAC Paris",
                    "3 MAP",
                    "4 LATI N48.85",
                    "1 FACT Premiers pas",
                    "2 TYPE Croissance",
                ],
            )
        )

        self.assertIsNone(individual._events)
        tags = [event["tag"] for event in individual.events]
        self.assertIs(individual.events, individual._events)
        self.assertEqual(tags, ["NAME", "BAPM", "FACT"])

        # Les tags avec un affichage dédié (SEX, FAMC, FAMS, OBJE, NOTE)
        # ne doivent pas apparaître dans l'arbre générique.
        self.assertNotIn("SEX", tags)
        self.assertNotIn("FAMC", tags)

        bapm_event = individual.events[1]
        date_node, plac_node = bapm_event["children"]
        self.assertEqual(
            (date_node["tag"], date_node["value"]), ("DATE", "22 JUN 1963")
        )
        self.assertEqual((plac_node["tag"], plac_node["value"]), ("PLAC", "Paris"))
        map_node = plac_node["children"][0]
        self.assertEqual(map_node["tag"], "MAP")
        self.assertEqual(map_node["children"][0]["tag"], "LATI")
        self.assertEqual(map_node["children"][0]["value"], "N48.85")

        fact_event = individual.events[2]
        self.assertEqual(fact_event["value"], "Premiers pas")
        self.assertEqual(
            fact_event["children"],
            [{"tag": "TYPE", "value": "Croissance", "children": []}],
        )

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
