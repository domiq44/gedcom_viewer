"""Tests du résumé d'en-tête des entités."""

import os
import tempfile
import unittest

from controllers.gedcom_service import GedcomService
from controllers.presentation_controller import PresentationController
from ui.i18n import Translator

GEDCOM_HEAD = (
    """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
1 SUBM @U1@
0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 BIRT
2 DATE 12 JAN 1900
2 PLAC Paris, France
1 DEAT
2 DATE 1980
1 OCCU Boulanger
0 @I2@ INDI
1 NAME Jane /Doe/
0 @I3@ INDI
1 NAME Child /One/
0 @I4@ INDI
1 NAME Child /Two/
0 @I5@ INDI
1 NAME Child /Three/
1 DEAT
2 DATE 1990
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 CHIL @I4@
1 MARR
2 DATE 1920
2 PLAC Lyon
0 @S1@ SOUR
1 TITL Acte de naissance
1 ABBR ADX
1 AUTH Archives de Paris
0 @R1@ REPO
1 NAME Archives
1 ADDR 1 rue des Archives
2 CITY Paris
2 CTRY France
0 @N1@ NOTE
1 CONT Une note sur John
0 @O1@ OBJE
1 FILE photo.jpg
1 TITL Portrait
0 @U1@ SUBM
1 NAME John /Doe/
1 EMAIL john@example.com
0 @U2@ SUBM
1 NAME Jane /Doe/
0 @I6@ INDI
1 NAME Child /Four/
1 BIRT
2 DATE 1850
0 @N2@ NOTE
1 CONT """
    + ("x" * 130)
    + """
0 @N3@ NOTE
1 CONT
0 @N4@ NOTE
1 CONT"""
    + (" " * 4)
    + """
0 TRLR
"""
)


class TestFormatEntitySummary(unittest.TestCase):
    """Vérifie le résumé d'en-tête construit pour chaque type d'entité."""

    def setUp(self):
        """Charge un fichier GEDCOM de test et construit le contrôleur."""
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".ged", delete=False
        )
        handle.write(GEDCOM_HEAD)
        handle.close()
        self.path = handle.name
        self.service = GedcomService()
        self.service.load_file(self.path)
        self.entity_controller = self.service.create_entity_controller()
        self.translator = Translator()
        self.presentation = PresentationController(
            self.service, self.entity_controller, translator=self.translator
        )

    def tearDown(self):
        """Supprime le fichier temporaire."""
        os.unlink(self.path)

    # Vérifie le résumé d'un individu porte son nom et sa plage d'années.
    def test_individual_summary_has_name_and_life_span(self):
        # Given un individu avec dates de naissance et de décès
        individual = self.presentation.get_individual("@I1@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("INDI", individual)

        # Then le titre et le sous-titre décrivent la personne
        self.assertEqual(summary["title"], "Doe, John")
        self.assertEqual(summary["subtitle"], "1900 – 1980")

    # Vérifie le résumé d'un individu liste ses faits principaux.
    def test_individual_summary_lists_facts(self):
        # Given un individu avec naissance, décès et profession
        individual = self.presentation.get_individual("@I1@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("INDI", individual)

        # Then les faits sont traduits et renseignés
        self.assertEqual(
            summary["facts"],
            [
                ("Birth date", "12 JAN 1900"),
                ("Birth place", "Paris, France"),
                ("Death date", "1980"),
                ("Occupations", "Boulanger"),
            ],
        )

    # Vérifie le résumé d'une famille compte ses enfants.
    def test_family_summary_counts_children(self):
        # Given une famille de deux enfants
        family = self.presentation.get_family("@F1@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("FAM", family)

        # Then le nombre d'enfants est exposé comme fait
        self.assertEqual(summary["title"], "Family")
        self.assertEqual(summary["subtitle"], "@F1@")
        self.assertIn(("Number of children", "2"), summary["facts"])

    # Vérifie le résumé d'une source utilise son titre et son abréviation.
    def test_source_summary_uses_title_and_abbreviation(self):
        # Given une source titrée et abrégée
        source = self.presentation.get_source("@S1@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("SOUR", source)

        # Then le titre et l'abréviation sont réutilisés
        self.assertEqual(summary["title"], "Acte de naissance")
        self.assertEqual(summary["subtitle"], "ADX")
        self.assertIn(("Author", "Archives de Paris"), summary["facts"])

    # Vérifie le résumé est vide sans entité.
    def test_summary_without_entity_is_empty(self):
        # Given aucune entité

        # When on construit le résumé
        summary = self.presentation.format_entity_summary("INDI", None)

        # Then aucun contenu n'est produit
        self.assertEqual(summary, {"title": "", "subtitle": "", "facts": []})

    # Vérifie les libellés restent des clés sans traducteur.
    def test_summary_without_translator_returns_keys(self):
        # Given un contrôleur sans traducteur
        presentation = PresentationController(self.service, self.entity_controller)
        individual = presentation.get_individual("@I1@")

        # When on construit son résumé
        summary = presentation.format_entity_summary("INDI", individual)

        # Then les libellés sont les clés de locale
        self.assertEqual(summary["facts"][0][0], "view.birth_date")

    # Vérifie un type inconnu retombe sur le pointeur.
    def test_summary_for_unknown_type_falls_back_to_pointer(self):
        # Given une entité et un type non géré
        individual = self.presentation.get_individual("@I1@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("XXXX", individual)

        # Then le pointeur sert de titre
        self.assertEqual(summary, {"title": "@I1@", "subtitle": "", "facts": []})

    # Vérifie le résumé d'un dépôt d'archives nomme et localise le lieu.
    def test_repository_summary_uses_name_and_address(self):
        # Given un dépôt d'archives avec adresse
        repository = self.presentation.get_repository("@R1@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("REPO", repository)

        # Then le nom et l'adresse sont exposés
        self.assertEqual(summary["title"], "Archives")
        self.assertEqual(summary["subtitle"], "@R1@")
        self.assertIn(("Address", "1 rue des Archives"), summary["facts"])

    # Vérifie le résumé d'une note reprend sa première ligne.
    def test_note_summary_uses_first_line(self):
        # Given une note d'une seule ligne
        note = self.presentation.get_note("@N1@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("NOTE", note)

        # Then le texte est résumé en un fait
        self.assertEqual(summary["facts"], [("Text", "Une note sur John")])

    # Vérifie le résumé d'une note tronque un texte trop long.
    def test_note_summary_truncates_long_text(self):
        # Given une note dont la première ligne dépasse la limite
        note = self.presentation.get_note("@N2@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("NOTE", note)

        # Then le texte est tronqué avec une ellipse
        self.assertTrue(summary["facts"][0][1].endswith("…"))
        self.assertEqual(len(summary["facts"][0][1]), 120)

    # Vérifie le résumé d'un objet multimédia nomme le fichier.
    def test_multimedia_summary_uses_title_and_file(self):
        # Given un objet multimédia avec fichier et titre
        multimedia = self.presentation.get_object("@O1@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("OBJE", multimedia)

        # Then le titre et le fichier sont exposés
        self.assertEqual(summary["title"], "Portrait")
        self.assertIn(("File", "photo.jpg"), summary["facts"])

    # Vérifie le résumé d'un soumissionnaire expose son courriel.
    def test_submitter_summary_uses_email(self):
        # Given un soumissionnaire avec un courriel
        submitter = self.presentation.get_submitter("@U1@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("SUBM", submitter)

        # Then le courriel devient un fait
        self.assertEqual(summary["title"], "John /Doe/")
        self.assertIn(("Email", "john@example.com"), summary["facts"])

    # Vérifie le résumé d'un individu sans dates n'a pas de sous-titre.
    def test_individual_summary_without_dates_has_empty_subtitle(self):
        # Given un individu sans date
        individual = self.presentation.get_individual("@I2@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("INDI", individual)

        # Then le sous-titre reste vide
        self.assertEqual(summary["subtitle"], "")

    # Vérifie le résumé d'un individu sans naissance n'affiche que le décès.
    def test_individual_summary_without_birth_shows_death_only(self):
        # Given un individu avec un décès mais sans naissance
        individual = self.presentation.get_individual("@I5@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("INDI", individual)

        # Then le sous-titre indique une naissance inconnue
        self.assertEqual(summary["subtitle"], "? – 1990")

    # Vérifie le résumé d'un individu sans décès n'affiche que la naissance.
    def test_individual_summary_without_death_shows_birth_only(self):
        # Given un individu avec une naissance mais sans décès
        individual = self.presentation.get_individual("@I6@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("INDI", individual)

        # Then le sous-titre ne contient que l'année de naissance
        self.assertEqual(summary["subtitle"], "1850")

    # Vérifie le résumé d'une note vide n'expose aucun fait.
    def test_note_summary_without_text_has_no_facts(self):
        # Given une note sans texte
        note = self.presentation.get_note("@N3@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("NOTE", note)

        # Then aucun fait n'est produit
        self.assertEqual(summary["facts"], [])

    # Vérifie le résumé d'une note blanche n'expose aucun fait.
    def test_note_summary_with_blank_text_has_no_facts(self):
        # Given une note dont le texte n'est composé que d'espaces
        note = self.presentation.get_note("@N4@")

        # When on construit son résumé
        summary = self.presentation.format_entity_summary("NOTE", note)

        # Then aucun fait n'est produit
        self.assertEqual(summary["facts"], [])


if __name__ == "__main__":
    unittest.main()
