"""Tests des collections paresseuses et leurs setters de l'individu."""

import unittest
from types import SimpleNamespace

from gedcom.models.entity import GedcomEntity
from gedcom.models.individual import Individual


def make_individual(lines):
    """Construit un individu à partir de lignes GEDCOM."""
    entity = GedcomEntity("@I1@", "INDI", 0, lines=lines)
    return Individual(entity)


class TestIndividualLazyCollections(unittest.TestCase):
    """Vérifie les collections paresseuses et leurs setters."""

    # Vérifie notes setter accepts none.
    def test_notes_setter_accepts_none(self):
        # Given un individu
        individual = make_individual(["0 @I1@ INDI\n"])
        # When on définit les notes à None
        individual.notes = None
        # Then la propriété retourne une liste vide
        self.assertEqual(individual.notes, [])

    # Vérifie texts setter accepts none.
    def test_texts_setter_accepts_none(self):
        # Given un individu
        individual = make_individual(["0 @I1@ INDI\n"])
        # When on définit les textes à None
        individual.texts = None
        # Then la propriété retourne une liste vide
        self.assertEqual(individual.texts, [])

    # Vérifie occupations setter accepts none.
    def test_occupations_setter_accepts_none(self):
        # Given un individu
        individual = make_individual(["0 @I1@ INDI\n"])
        # When on définit les professions à None
        individual.occupations = None
        # Then la propriété retourne une liste vide
        self.assertEqual(individual.occupations, [])

    # Vérifie properties setter accepts none.
    def test_properties_setter_accepts_none(self):
        # Given un individu
        individual = make_individual(["0 @I1@ INDI\n"])
        # When on définit les propriétés à None
        individual.properties = None
        # Then la propriété retourne une liste vide
        self.assertEqual(individual.properties, [])

    # Vérifie fams setter accepts none.
    def test_fams_setter_accepts_none(self):
        # Given un individu
        individual = make_individual(["0 @I1@ INDI\n"])
        # When on définit les familles à None
        individual.fams = None
        # Then la propriété retourne une liste vide
        self.assertEqual(individual.fams, [])

    # Vérifie obje setter accepts none.
    def test_obje_setter_accepts_none(self):
        # Given un individu
        individual = make_individual(["0 @I1@ INDI\n"])
        # When on définit les objets à None
        individual.obje = None
        # Then la propriété retourne une liste vide
        self.assertEqual(individual.obje, [])

    # Vérifie fams are collected.
    def test_fams_are_collected(self):
        # Given un individu avec deux FAMS
        individual = make_individual(
            ["0 @I1@ INDI\n", "1 FAMS @F1@\n", "1 FAMS @F2@\n"]
        )
        # When on lit les familles
        # Then les deux pointeurs sont retournés
        self.assertEqual(individual.fams, ["@F1@", "@F2@"])

    # Vérifie obje skips inline placeholder.
    def test_obje_skips_inline_placeholder(self):
        # Given un individu avec un OBJE inline et un OBJE par pointeur
        individual = make_individual(["0 @I1@ INDI\n", "1 OBJE *\n", "1 OBJE @O1@\n"])
        # When on lit les objets
        # Then seul le pointeur est conservé
        self.assertEqual(individual.obje, ["@O1@"])

    # Vérifie occupations are collected with dates.
    def test_occupations_are_collected_with_dates(self):
        # Given un individu avec une profession datée
        individual = make_individual(
            ["0 @I1@ INDI\n", "1 OCCU farmer\n", "2 DATE 1900\n"]
        )
        # When on lit les professions
        # Then la profession et sa date sont retournées
        self.assertEqual(
            individual.occupations, [{"occupation": "farmer", "date": "1900"}]
        )

    # Vérifie properties are collected.
    def test_properties_are_collected(self):
        # Given un individu avec une propriété
        individual = make_individual(["0 @I1@ INDI\n", "1 PROP xyz\n"])
        # When on lit les propriétés
        # Then la valeur est retournée
        self.assertEqual(individual.properties, ["xyz"])

    # Vérifie events setter.
    def test_events_setter(self):
        # Given un individu
        individual = make_individual(["0 @I1@ INDI\n"])
        events = [{"tag": "BIRT", "value": "", "children": []}]
        # When on définit les événements
        individual.events = events
        # Then la propriété retourne la valeur définie
        self.assertEqual(individual.events, events)

    # Vérifie events build tree with excluded tags.
    def test_events_build_tree_with_excluded_tags(self):
        # Given un individu avec des tags exclus et un événement
        individual = make_individual(
            [
                "0 @I1@ INDI\n",
                "1 SEX M\n",
                "1 NAME John /Doe/\n",
                "1 OCCU farmer\n",
                "1 PROP land\n",
                "1 TEXT biography\n",
                "1 BIRT\n",
                "2 DATE 1900\n",
                "2 PLAC Paris\n",
                "1 NOTE note\n",
            ]
        )
        # When on lit les événements
        events = individual.events
        # Then seuls les tags non exclus sont conservés avec leurs enfants
        self.assertEqual([event["tag"] for event in events], ["BIRT"])
        self.assertEqual(
            events[0]["children"],
            [
                {"tag": "DATE", "value": "1900", "children": []},
                {"tag": "PLAC", "value": "Paris", "children": []},
            ],
        )

    # Vérifie texts use get tag values when available.
    def test_texts_use_get_tag_values_when_available(self):
        # Given un individu avec un TEXT suivi d'un CONT
        individual = make_individual(
            ["0 @I1@ INDI\n", "1 TEXT hello\n", "2 CONT world\n"]
        )
        # When on lit les textes
        # Then le parseur fusionne la continuation
        self.assertEqual(individual.texts, ["hello\nworld"])

    # Vérifie simple tag lists use parsed lines fallback.
    def test_simple_tag_lists_use_parsed_lines_fallback(self):
        # Given une entité sans get_tag_values
        entity = SimpleNamespace(
            pointer="@I1@",
            parsed_lines=lambda: [
                (0, "@I1@", "INDI", ""),
                (1, None, "FAMS", "@F1@"),
                (1, None, "OBJE", "@O1@"),
                (1, None, "PROP", "Nationality"),
            ],
        )
        individual = Individual(entity)
        # When on lit les listes simples
        # Then le balayage de repli les collecte
        self.assertEqual(individual.fams, ["@F1@"])
        self.assertEqual(individual.obje, ["@O1@"])
        self.assertEqual(individual.properties, ["Nationality"])


if __name__ == "__main__":
    unittest.main()
