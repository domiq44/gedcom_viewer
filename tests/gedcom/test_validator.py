"""Tests de validation de structure, en-têtes, pointeurs et références."""

import threading
import unittest

from gedcom.errors import GedcomLoadCancelled
from gedcom.line_parser import parse_line
from gedcom.validator import GedcomValidator
from tests.gedcom.test_validator_common import VALID_GEDCOM, load_parser, validate_text


class TestGedcomValidator(unittest.TestCase):
    """Vérifie la validation de la structure, des en-têtes, des pointeurs et des références."""

    # Vérifie valid gedcom has no errors.
    def test_valid_gedcom_has_no_errors(self):
        # Given (Arrange) un GEDCOM valide
        text = VALID_GEDCOM
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) aucune erreur n'est remontée
        self.assertEqual(errors, [])

    # Vérifie chan is accepted at level one.
    def test_chan_is_accepted_at_level_one(self):
        # Given (Arrange) un individu avec un CHAN valide
        text = VALID_GEDCOM.replace(
            "1 FAMS @F1@",
            "1 CHAN\n2 DATE 1 JAN 2020\n1 FAMS @F1@",
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) aucun tag inconnu n'est signalé
        self.assertEqual(errors, [])

    # Vérifie calendar escape date is accepted.
    def test_calendar_escape_date_is_accepted(self):
        # Given (Arrange) une date avec un échappement de calendrier
        text = VALID_GEDCOM.replace(
            "1 FAMS @F1@",
            "1 BIRT\n2 DATE @#DGREGORIAN@ 1 JAN 1900\n1 FAMS @F1@",
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) la date est acceptée
        self.assertEqual(errors, [])

    # Vérifie validate raises when cancelled.
    def test_validate_raises_when_cancelled(self):
        # Given un GEDCOM chargé et une annulation demandée
        parser = load_parser(VALID_GEDCOM)
        validator = GedcomValidator(parse_line)
        cancel_event = threading.Event()
        cancel_event.set()

        # When on valide avec annulation
        # Then la validation s'interrompt immédiatement
        with self.assertRaises(GedcomLoadCancelled):
            validator.validate(
                parser.lines, parser._by_pointer, cancel_event=cancel_event
            )

    # Vérifie malformed line without level.
    def test_malformed_line_without_level(self):
        # Given (Arrange) un GEDCOM contenant une ligne sans niveau
        text = "0 @I1@ INDI\nPAS UN NIVEAU\n1 NAME X\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) une ligne malformée est signalée
        self.assertTrue(any("malformée" in error for error in errors))

    # Vérifie negative level is reported.
    def test_negative_level_is_reported(self):
        # Given (Arrange) un GEDCOM avec un niveau négatif
        text = "0 HEAD\n1 SOUR X\n-1 INVALID\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le niveau négatif est signalé
        self.assertTrue(any("niveau négatif" in error for error in errors))

    # Vérifie level jump is reported.
    def test_level_jump_is_reported(self):
        # Given (Arrange) un GEDCOM sautant un niveau
        text = "0 HEAD\n2 SOUR X\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le saut de niveau est signalé
        self.assertTrue(any("saut de niveau" in error for error in errors))

    # Vérifie missing pointer for record is reported.
    def test_missing_pointer_for_record_is_reported(self):
        # Given (Arrange) un enregistrement INDI sans pointeur
        text = "0 INDI\n1 NAME X\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le pointeur manquant est signalé
        self.assertTrue(any("pointeur manquant" in error for error in errors))

    # Vérifie pointer on head is reported.
    def test_pointer_on_head_is_reported(self):
        # Given (Arrange) un HEAD portant un pointeur
        text = "0 @X@ HEAD\n1 SOUR X\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le pointeur inattendu est signalé
        self.assertTrue(any("pointeur inattendu" in error for error in errors))

    # Vérifie missing head is reported.
    def test_missing_head_is_reported(self):
        # Given (Arrange) un GEDCOM sans HEAD
        text = "0 @I1@ INDI\n1 NAME X\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'absence de HEAD est signalée
        self.assertTrue(any("HEAD absent ou multiple" in error for error in errors))

    # Vérifie multiple head is reported.
    def test_multiple_head_is_reported(self):
        # Given (Arrange) un GEDCOM avec deux HEAD
        text = "0 HEAD\n1 SOUR X\n0 HEAD\n1 SOUR Y\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) la multiplicité de HEAD est signalée
        self.assertTrue(any("HEAD absent ou multiple" in error for error in errors))

    # Vérifie missing trailer is reported.
    def test_missing_trailer_is_reported(self):
        # Given (Arrange) un GEDCOM sans TRLR
        text = "0 HEAD\n1 SOUR X\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'absence de TRLR est signalée
        self.assertTrue(any("TRLR absent ou multiple" in error for error in errors))

    # Vérifie head not first is reported.
    def test_head_not_first_is_reported(self):
        # Given (Arrange) un GEDCOM où HEAD n'est pas premier
        text = "0 @I1@ INDI\n1 NAME X\n0 HEAD\n1 SOUR X\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le placement de HEAD est signalé
        self.assertTrue(any("HEAD doit être le premier" in error for error in errors))

    # Vérifie trailer not last is reported.
    def test_trailer_not_last_is_reported(self):
        # Given (Arrange) un GEDCOM où TRLR n'est pas dernier
        text = "0 HEAD\n1 SOUR X\n0 TRLR\n0 @I1@ INDI\n1 NAME X\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le placement de TRLR est signalé
        self.assertTrue(any("TRLR doit être le dernier" in error for error in errors))

    # Vérifie trailer with sublines is reported.
    def test_trailer_with_sublines_is_reported(self):
        # Given (Arrange) un TRLR avec des sous-lignes
        text = "0 HEAD\n1 SOUR X\n0 TRLR\n1 EXTRA value\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) la présence de sous-lignes sous TRLR est signalée
        self.assertTrue(
            any("TRLR ne doit pas contenir de sous-lignes" in e for e in errors)
        )

    # Vérifie head with value is reported.
    def test_head_with_value_is_reported(self):
        # Given (Arrange) un HEAD avec une valeur
        text = "0 HEAD value\n1 SOUR X\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) la valeur sur HEAD est signalée
        self.assertTrue(any("HEAD ne doit pas avoir de valeur" in e for e in errors))

    # Vérifie invalid pointer format is reported.
    def test_invalid_pointer_format_is_reported(self):
        # Given (Arrange) un pointeur au format invalide
        text = "0 @I1 INDI\n1 NAME X\n0 HEAD\n1 SOUR X\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le format invalide est signalé
        self.assertTrue(any("pointeur invalide" in error for error in errors))

    # Vérifie duplicate pointer is reported.
    def test_duplicate_pointer_is_reported(self):
        # Given (Arrange) deux enregistrements partageant le même pointeur
        text = (
            "0 HEAD\n1 SOUR X\n0 @I1@ INDI\n1 NAME A\n"
            "0 @I1@ INDI\n1 NAME B\n0 TRLR\n"
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le pointeur dupliqué est signalé
        self.assertTrue(any("pointeur dupliqué" in error for error in errors))

    # Vérifie unknown reference is reported.
    def test_unknown_reference_is_reported(self):
        # Given (Arrange) une référence vers un pointeur inexistant
        text = "0 HEAD\n1 SOUR X\n0 @I1@ INDI\n1 NAME A\n1 FAMS @F9@\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) la référence inconnue est signalée
        self.assertTrue(any("référence inconnue" in error for error in errors))

    # Vérifie reference type mismatch is reported.
    def test_reference_type_mismatch_is_reported(self):
        # Given (Arrange) un HUSB pointant vers une FAM au lieu d'un INDI
        text = (
            "0 HEAD\n1 SOUR X\n0 @I1@ INDI\n1 NAME A\n"
            "0 @F1@ FAM\n1 HUSB @F1@\n0 TRLR\n"
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'incompatibilité de type est signalée
        self.assertTrue(any("incompatible" in error for error in errors))

    # Vérifie missing reference pointer is reported.
    def test_missing_reference_pointer_is_reported(self):
        # Given (Arrange) un FAMS sans pointeur
        text = "0 HEAD\n1 SOUR X\n0 @I1@ INDI\n1 NAME A\n1 FAMS\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le pointeur de référence manquant est signalé
        self.assertTrue(
            any("pointeur de référence manquant" in error for error in errors)
        )

    # Vérifie gedc vers missing is reported.
    def test_gedc_vers_missing_is_reported(self):
        # Given (Arrange) un HEAD.GEDC sans VERS
        text = "0 HEAD\n1 SOUR X\n1 GEDC\n2 FORM LINEAGE-LINKED\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'absence de VERS est signalée
        self.assertTrue(any("HEAD.GEDC.VERS manquant" in error for error in errors))

    # Vérifie gedc vers empty is reported.
    def test_gedc_vers_empty_is_reported(self):
        # Given (Arrange) un HEAD.GEDC.VERS vide
        text = "0 HEAD\n1 GEDC\n2 VERS \n2 FORM LINEAGE-LINKED\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le VERS vide est signalé
        self.assertTrue(
            any("HEAD.GEDC.VERS ne doit pas être vide" in error for error in errors)
        )

    # Vérifie gedc form missing is reported.
    def test_gedc_form_missing_is_reported(self):
        # Given (Arrange) un HEAD.GEDC sans FORM
        text = "0 HEAD\n1 GEDC\n2 VERS 5.5.1\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'absence de FORM est signalée
        self.assertTrue(any("HEAD.GEDC.FORM manquant" in error for error in errors))

    # Vérifie gedcom 551 requires sour.
    def test_gedcom_551_requires_sour(self):
        # Given (Arrange) un GEDCOM 5.5.1 sans HEAD.SOUR
        text = "0 HEAD\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'absence de SOUR est signalée
        self.assertTrue(any("HEAD.SOUR manquant" in error for error in errors))

    # Vérifie gedcom 551 requires char.
    def test_gedcom_551_requires_char(self):
        # Given (Arrange) un GEDCOM 5.5.1 sans HEAD.CHAR
        text = "0 HEAD\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'absence de CHAR est signalée
        self.assertTrue(any("HEAD.CHAR manquant" in error for error in errors))

    # Vérifie gedcom 551 requires subm.
    def test_gedcom_551_requires_subm(self):
        # Given (Arrange) un GEDCOM 5.5.1 sans HEAD.SUBM
        text = "0 HEAD\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'absence de SUBM est signalée
        self.assertTrue(any("HEAD.SUBM manquant" in error for error in errors))

    # Vérifie missing gedc is reported.
    def test_missing_gedc_is_reported(self):
        # Given (Arrange) un HEAD sans GEDC
        text = VALID_GEDCOM.replace("1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n", "")
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'absence de GEDC est signalée
        self.assertTrue(any("HEAD.GEDC manquant" in error for error in errors))

    # Vérifie first line must be level zero.
    def test_first_line_must_be_level_zero(self):
        # Given (Arrange) un fichier commençant par une ligne de niveau 1
        text = "1 SOUR X\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) la première ligne est signalée
        self.assertTrue(
            any(
                "première ligne doit être un enregistrement de niveau 0" in e
                for e in errors
            )
        )

    # Vérifie invalid level format is reported.
    def test_invalid_level_format_is_reported(self):
        # Given (Arrange) un niveau avec un zéro initial
        text = "0 HEAD\n01 SOUR X\n0 TRLR\n"
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le format du niveau est signalé
        self.assertTrue(any("niveau invalide" in error for error in errors))

    # Vérifie invalid sex value is reported.
    def test_invalid_sex_value_is_reported(self):
        # Given (Arrange) un individu avec une valeur SEX inconnue
        text = VALID_GEDCOM.replace("1 SEX M", "1 SEX Z")
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) la valeur SEX est signalée
        self.assertTrue(any("valeur SEX invalide" in error for error in errors))

    # Vérifie invalid date value is reported.
    def test_invalid_date_value_is_reported(self):
        # Given (Arrange) un individu avec une date invalide
        text = VALID_GEDCOM.replace(
            "1 SEX M",
            "1 SEX M\n1 BIRT\n2 DATE not-a-date",
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) la date est signalée
        self.assertTrue(any("date invalide" in error for error in errors))

    # Vérifie date directement sous indi est rejetée (validation contextuelle).
    def test_date_level_one_under_indi_is_rejected(self):
        # Given (Arrange) un individu avec une DATE directement au niveau 1
        text = VALID_GEDCOM.replace(
            "1 SEX M",
            "1 SEX M\n1 DATE 1 JAN 1900",
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'erreur contextuelle est remontée
        self.assertTrue(
            any("DATE ne doit pas être au niveau 1 sous INDI" in e for e in errors)
        )

    # Vérifie plac directement sous indi est rejetée (validation contextuelle).
    def test_plac_level_one_under_indi_is_rejected(self):
        # Given (Arrange) un individu avec une PLAC directement au niveau 1
        text = VALID_GEDCOM.replace(
            "1 SEX M",
            "1 SEX M\n1 PLAC Paris",
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'erreur contextuelle est remontée
        self.assertTrue(
            any("PLAC ne doit pas être au niveau 1 sous INDI" in e for e in errors)
        )

    # Vérifie titl directement sous indi est rejeté (validation contextuelle).
    def test_titl_level_one_under_indi_is_rejected(self):
        # Given (Arrange) un individu avec un TITL directement au niveau 1
        text = VALID_GEDCOM.replace(
            "1 SEX M",
            "1 SEX M\n1 TITL Monsieur",
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'erreur contextuelle est remontée
        self.assertTrue(
            any("TITL ne doit pas être au niveau 1 sous INDI" in e for e in errors)
        )

    # Vérifie date au niveau 2 sous BIRT est acceptée (pas de régression).
    def test_date_level_two_under_birt_under_indi_is_accepted(self):
        # Given (Arrange) un individu avec une DATE de naissance valide
        text = VALID_GEDCOM.replace(
            "1 SEX M",
            "1 SEX M\n1 BIRT\n2 DATE 1 JAN 1900",
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) aucune erreur contextuelle n'est remontée
        self.assertEqual(errors, [])

    # Vérifie multiple sex in indi is reported.
    def test_multiple_sex_in_indi_is_reported(self):
        # Given (Arrange) un individu avec deux valeurs SEX
        text = VALID_GEDCOM.replace("1 SEX M", "1 SEX M\n1 SEX F")
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) la cardinalité de SEX est signalée
        self.assertTrue(any("SEX multiple" in error for error in errors))

    # Vérifie missing indi name is reported.
    def test_missing_indi_name_is_reported(self):
        # Given (Arrange) un individu sans NAME
        text = VALID_GEDCOM.replace(
            "0 @I1@ INDI\n1 NAME John /Doe/\n1 SEX M", "0 @I1@ INDI\n1 SEX M"
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) l'absence de NAME est signalée
        self.assertTrue(any("INDI NAME manquant" in error for error in errors))

    # Vérifie gedcom 551 rejects multiple char.
    def test_gedcom_551_rejects_multiple_char(self):
        # Given (Arrange) un GEDCOM 5.5.1 avec deux HEAD.CHAR
        text = (
            "0 HEAD\n1 SOUR X\n1 CHAR UTF-8\n1 CHAR ANSI\n1 SUBM @U1@\n"
            "1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
            "0 @U1@ SUBM\n1 NAME A\n0 TRLR\n"
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) la multiplicité de CHAR est signalée
        self.assertTrue(any("HEAD.CHAR multiple" in error for error in errors))

    # Vérifie reference source tag context is enforced.
    def test_reference_source_tag_context_is_enforced(self):
        # Given (Arrange) un FAMC placé sous une FAM au lieu d'un INDI
        text = (
            "0 HEAD\n1 SOUR X\n0 @I1@ INDI\n1 NAME A\n"
            "0 @F1@ FAM\n1 HUSB @I1@\n1 FAMC @F1@\n0 TRLR\n"
        )
        # When (Act) on le valide
        errors = validate_text(text)
        # Then (Assert) le contexte du tag FAMC est signalé
        self.assertTrue(
            any(
                "FAMC doit être au niveau 1 d'un enregistrement INDI" in e
                for e in errors
            )
        )

    # Vérifie negative level reference tag reports only level error.
    def test_negative_level_reference_tag_reports_only_level_error(self):
        # Given (Arrange) un GEDCOM valide avec une ligne à niveau négatif
        text = (
            "0 HEAD\n1 SOUR X\n1 GEDC\n2 VERS 5.5.1\n"
            "2 FORM LINEAGE-LINKED\n1 CHAR UTF-8\n1 SUBM @U1@\n"
            "0 @U1@ SUBM\n1 NAME A\n-1 HUSB @I1@\n0 TRLR\n"
        )
        # When (Act) on valide le texte
        errors = validate_text(text)
        # Then (Assert) seule l'erreur de niveau négatif est signalée
        self.assertEqual(errors, ["niveau négatif ligne 10"])


if __name__ == "__main__":
    unittest.main()
