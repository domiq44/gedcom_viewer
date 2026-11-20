"""Tests d'intégration chargement + validation du validateur."""

import unittest

from gedcom.parser import GedcomParser
from tests.temp_file_factory import write_temp_text


class TestGedcomValidation(unittest.TestCase):
    """Vérifie la validation structurelle et référentielle du GEDCOM."""

    # Vérifie load records validation errors.
    def test_load_records_validation_errors(self):
        temp_path = write_temp_text(self, "0 HEAD\n1 SOUR TEST\n")

        parser = GedcomParser()
        parser.load(temp_path)

        self.assertIn("TRLR absent ou multiple", parser.validation_errors)

    # Vérifie validate requires head first and trlr last.
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

    # Vérifie validate rejects nested head and trailer tags.
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

    # Vérifie validate checks gedc header contexts.
    def test_validate_checks_gedc_header_contexts(self):
        valid_parser = GedcomParser()
        valid_parser.lines = [
            "0 HEAD",
            "1 SOUR Ancestris",
            "2 VERS 1.0",
            "1 SUBM @S1@",
            "1 GEDC",
            "2 VERS 5.5.1",
            "2 FORM LINEAGE-LINKED",
            "1 CHAR UTF-8",
            "2 VERS 1",
            "2 FORM UTF-8",
            "1 PLAC",
            "2 FORM City, County, State, Country",
            "0 @S1@ SUBM",
            "1 NAME Submitter",
            "0 TRLR",
        ]
        valid_parser._parse_entities()
        self.assertEqual(valid_parser.validate(), [])

        invalid_contexts = [
            (
                ["0 HEAD", "1 GEDC", "2 VERS", "2 FORM X", "0 TRLR"],
                "HEAD.GEDC.VERS ne doit pas être vide ligne 3",
            ),
            (
                ["0 HEAD", "1 GEDC", "2 VERS 5.5.1", "2 FORM", "0 TRLR"],
                "HEAD.GEDC.FORM ne doit pas être vide ligne 4",
            ),
            (
                [
                    "0 HEAD",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "2 VERS 5.5.1",
                    "0 TRLR",
                ],
                "HEAD.GEDC.VERS multiple",
            ),
            (
                [
                    "0 HEAD",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "0 TRLR",
                ],
                "HEAD.GEDC multiple",
            ),
            (
                [
                    "0 HEAD",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "1 CHAR UTF-8",
                    "0 TRLR",
                ],
                "HEAD.SOUR manquant pour GEDCOM 5.5.1",
            ),
            (
                [
                    "0 HEAD",
                    "1 SOUR App",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "0 TRLR",
                ],
                "HEAD.CHAR manquant pour GEDCOM 5.5.1",
            ),
            (
                [
                    "0 HEAD",
                    "1 SOUR",
                    "1 CHAR UTF-8",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "0 TRLR",
                ],
                "HEAD.SOUR ne doit pas être vide ligne 2",
            ),
            (
                [
                    "0 HEAD",
                    "1 SOUR App",
                    "1 CHAR",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "0 TRLR",
                ],
                "HEAD.CHAR ne doit pas être vide ligne 3",
            ),
            (
                [
                    "0 HEAD",
                    "1 SOUR App",
                    "1 CHAR UTF-8",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "0 TRLR",
                ],
                "HEAD.SUBM manquant pour GEDCOM 5.5.1",
            ),
            (
                [
                    "0 HEAD",
                    "1 SOUR App",
                    "1 SUBM @S1@",
                    "1 SUBM @S2@",
                    "1 CHAR UTF-8",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "0 @S1@ SUBM",
                    "0 @S2@ SUBM",
                    "0 TRLR",
                ],
                "HEAD.SUBM multiple pour GEDCOM 5.5.1",
            ),
            (
                [
                    "0 HEAD",
                    "1 SOUR App",
                    "1 SOUR Other App",
                    "1 SUBM @S1@",
                    "1 CHAR UTF-8",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "0 @S1@ SUBM",
                    "0 TRLR",
                ],
                "HEAD.SOUR multiple pour GEDCOM 5.5.1",
            ),
            (
                [
                    "0 HEAD",
                    "1 SOUR App",
                    "1 SUBM @S1@",
                    "1 CHAR UTF-8",
                    "1 CHAR ANSEL",
                    "1 GEDC",
                    "2 VERS 5.5.1",
                    "2 FORM LINEAGE-LINKED",
                    "0 @S1@ SUBM",
                    "0 TRLR",
                ],
                "HEAD.CHAR multiple pour GEDCOM 5.5.1",
            ),
            (
                ["0 HEAD", "1 GEDC", "2 FORM LINEAGE-LINKED", "0 TRLR"],
                "HEAD.GEDC.VERS manquant ligne 2",
            ),
            (
                ["0 HEAD", "1 GEDC", "2 VERS 5.5.1", "0 TRLR"],
                "HEAD.GEDC.FORM manquant ligne 2",
            ),
            (
                ["0 HEAD", "1 VERS 5.5.1", "0 TRLR"],
                "VERS doit être au niveau 2 de HEAD.GEDC ou HEAD.SOUR ligne 2",
            ),
            (
                ["0 HEAD", "1 FORM LINEAGE-LINKED", "0 TRLR"],
                "FORM doit être au niveau 2 de HEAD.GEDC ou HEAD.CHAR ligne 2",
            ),
            (
                ["0 @I1@ INDI", "1 GEDC", "0 HEAD", "0 TRLR"],
                "GEDC doit être au niveau 1 de HEAD ligne 2",
            ),
        ]

        for lines, expected_error in invalid_contexts:
            with self.subTest(expected_error=expected_error):
                parser = GedcomParser()
                parser.lines = lines
                parser._parse_entities()

                self.assertIn(expected_error, parser.validate())

    # Vérifie validate requires pointers for indexed record types.
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
        inline_note_parser.lines = [
            "0 HEAD",
            "1 SOUR X",
            "1 GEDC",
            "2 VERS 5.5.1",
            "2 FORM LINEAGE-LINKED",
            "1 CHAR UTF-8",
            "1 SUBM @U1@",
            "0 @U1@ SUBM",
            "1 NAME A",
            "0 NOTE Inline note",
            "0 TRLR",
        ]
        inline_note_parser._parse_entities()
        self.assertEqual(inline_note_parser.validate(), [])

    # Vérifie strict load rejects trailer subrecords.
    def test_strict_load_rejects_trailer_subrecords(self):
        temp_path = write_temp_text(self, "0 HEAD\n0 TRLR\n1 NOTE invalid\n")
        parser = GedcomParser()

        with self.assertRaisesRegex(ValueError, "TRLR ne doit pas contenir"):
            parser.load(temp_path, strict=True)

    # Vérifie duplicate pointer keeps first entity for resolution.
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
        self.assertEqual(len(parser.entities["INDI"]), 1)
        self.assertIn("Pointeur GEDCOM dupliqué", logs.output[0])

    # Vérifie validate reports duplicate pointer.
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

    # Vérifie validate reports unknown pointer reference.
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

    # Vérifie validate reports malformed reference pointer.
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

    # Vérifie validate reports missing required reference pointer.
    def test_validate_reports_missing_required_reference_pointer(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "0 @F1@ FAM", "1 HUSB", "0 TRLR"]
        parser._parse_entities()

        self.assertIn(
            "pointeur de référence manquant pour HUSB ligne 3", parser.validate()
        )

    # Vérifie validate reports reference with unexpected entity type.
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

    # Vérifie validate checks alias reference.
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
        self.assertFalse(
            any("ALIA" in error for error in validate_alias("@I2@", "0 @I2@ INDI"))
        )

    # Vérifie validate rejects alias outside level one indi.
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

    # Vérifie validate rejects family links outside source records.
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

    # Vérifie validate distinguishes submitter and repository records.
    def test_validate_distinguishes_submitter_and_repository_records(self):
        parser = GedcomParser()
        parser.lines = [
            "0 HEAD",
            "1 SOUR X",
            "1 GEDC",
            "2 VERS 5.5.1",
            "2 FORM LINEAGE-LINKED",
            "1 CHAR UTF-8",
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

    # Vérifie validate checks association and repository contexts.
    def test_validate_checks_association_and_repository_contexts(self):
        valid_parser = GedcomParser()
        valid_parser.lines = [
            "0 HEAD",
            "1 SOUR X",
            "1 GEDC",
            "2 VERS 5.5.1",
            "2 FORM LINEAGE-LINKED",
            "1 CHAR UTF-8",
            "1 SUBM @U1@",
            "0 @U1@ SUBM",
            "1 NAME A",
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "1 ASSO @I2@",
            "0 @I2@ INDI",
            "1 NAME Jane /Doe/",
            "0 @R1@ REPO",
            "1 NAME Repository",
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

    # Vérifie validate accepts reference with expected entity type.
    def test_validate_accepts_reference_with_expected_entity_type(self):
        parser = GedcomParser()
        parser.lines = [
            "0 HEAD",
            "1 SOUR X",
            "1 GEDC",
            "2 VERS 5.5.1",
            "2 FORM LINEAGE-LINKED",
            "1 CHAR UTF-8",
            "1 SUBM @U1@",
            "0 @U1@ SUBM",
            "1 NAME A",
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "0 TRLR",
        ]
        parser._parse_entities()

        self.assertEqual(parser.validate(), [])

    # Vérifie strict load rejects reference with unexpected entity type.
    def test_strict_load_rejects_reference_with_unexpected_entity_type(self):
        content = "0 HEAD\n0 @F1@ FAM\n1 HUSB @F1@\n0 TRLR\n"
        temp_path = write_temp_text(self, content)
        parser = GedcomParser()

        with self.assertRaisesRegex(ValueError, "type INDI attendu"):
            parser.load(temp_path, strict=True)

    # Vérifie strict load rejects malformed reference pointer.
    def test_strict_load_rejects_malformed_reference_pointer(self):
        content = "0 HEAD\n0 @F1@ FAM\n1 HUSB @I1\n0 TRLR\n"
        temp_path = write_temp_text(self, content)
        parser = GedcomParser()

        with self.assertRaisesRegex(ValueError, "pointeur de référence invalide"):
            parser.load(temp_path, strict=True)

    # Vérifie strict load rejects missing required reference pointer.
    def test_strict_load_rejects_missing_required_reference_pointer(self):
        content = "0 HEAD\n0 @F1@ FAM\n1 HUSB\n0 TRLR\n"
        temp_path = write_temp_text(self, content)
        parser = GedcomParser()

        with self.assertRaisesRegex(ValueError, "pointeur de référence manquant"):
            parser.load(temp_path, strict=True)

    # Vérifie strict load rejects invalid structure.
    def test_strict_load_rejects_invalid_structure(self):
        temp_path = write_temp_text(self, "0 HEAD\n1 SOUR TEST\n")
        parser = GedcomParser()

        with self.assertRaises(ValueError):
            parser.load(temp_path, strict=True)

    # Vérifie strict load rejects blank lines.
    def test_strict_load_rejects_blank_lines(self):
        temp_path = write_temp_text(self, "0 HEAD\n\n0 TRLR\n")
        parser = GedcomParser()

        with self.assertRaisesRegex(ValueError, "ligne 2 malformée"):
            parser.load(temp_path, strict=True)

    # Vérifie strict load rejects values on head and trailer.
    def test_strict_load_rejects_values_on_head_and_trailer(self):
        invalid_records = (
            ("0 HEAD extra\n0 TRLR\n", "HEAD ne doit pas avoir de valeur ligne 1"),
            ("0 HEAD\n0 TRLR value\n", "TRLR ne doit pas avoir de valeur ligne 2"),
        )

        for content, expected_error in invalid_records:
            with self.subTest(expected_error=expected_error):
                temp_path = write_temp_text(self, content)
                parser = GedcomParser()

                with self.assertRaisesRegex(ValueError, expected_error):
                    parser.load(temp_path, strict=True)

    # Vérifie validate reports malformed line.
    def test_validate_reports_malformed_line(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "invalid GEDCOM line", "0 TRLR"]
        parser._parse_entities()

        self.assertIn("ligne 2 malformée", parser.validate())

    # Vérifie validate reports blank line.
    def test_validate_reports_blank_line(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "", "0 TRLR"]
        parser._parse_entities()

        self.assertIn("ligne 2 malformée", parser.validate())

    # Vérifie validate reports line without tag.
    def test_validate_reports_line_without_tag(self):
        parser = GedcomParser()
        parser.lines = ["0 HEAD", "1", "0 TRLR"]
        parser._parse_entities()

        self.assertIn("ligne 2 malformée", parser.validate())

    # Vérifie les valeurs en ligne de SOUR, NOTE et OBJE restent acceptées.
    def test_validate_accepts_inline_sour_note_and_obje_values(self):
        # Given un individu portant des valeurs en ligne (non pointeurs)
        gedcom = (
            "0 HEAD\n"
            "1 SOUR TEST\n"
            "1 GEDC\n"
            "2 VERS 5.5.1\n"
            "2 FORM LINEAGE-LINKED\n"
            "1 CHAR UTF-8\n"
            "1 SUBM @U1@\n"
            "0 @U1@ SUBM\n"
            "1 NAME A\n"
            "0 @I1@ INDI\n"
            "1 NAME A /B/\n"
            "1 SOUR Description de source\n"
            "1 NOTE Note en ligne\n"
            "1 OBJE photo.jpg\n"
            "0 TRLR\n"
        )
        temp_path = write_temp_text(self, gedcom)
        parser = GedcomParser()
        # When on charge et valide l'enregistrement
        parser.load(temp_path)
        # Then les valeurs en ligne ne produisent aucune erreur
        self.assertEqual(parser.validation_errors, [])


if __name__ == "__main__":
    unittest.main()
