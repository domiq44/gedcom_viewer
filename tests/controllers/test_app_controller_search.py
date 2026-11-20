"""Tests de recherche et de listage du contrôleur applicatif."""

import unittest

from controllers.app_controller import AppController
from gedcom.models.entity import GedcomEntity
from gedcom.models.family import Family
from gedcom.models.individual import Individual
from gedcom.models.multimedia import MultimediaObject
from gedcom.models.note import Note
from gedcom.models.repository import Repository
from gedcom.models.source import Source
from gedcom.models.submitter import Submitter
from tests.controllers.app_controller_test_case import AppControllerTestMixin
from tests.temp_file_factory import write_temp_text


class TestAppControllerSearch(AppControllerTestMixin, unittest.TestCase):
    """Vérifie la recherche et le listage des entités."""

    # Vérifie citation category lists searches and labels linked source.
    def test_citation_category_lists_searches_and_labels_linked_source(self):
        content = """0 HEAD
1 SOUR TEST
0 @I1@ INDI
1 NAME Ada /Lovelace/
1 BIRT
2 SOUR @S1@
3 PAGE 17
0 @F1@ FAM
1 SOUR @S2@
0 @I2@ INDI
1 NAME Grace /Hopper/
1 BIRT
2 SOUR @S3@
0 @S1@ SOUR
1 TITL Parish register
1 REPO @R2@
0 @S2@ SOUR
1 TITL Another parish register
1 REPO @R2@
0 @S3@ SOUR
1 TITL Other archive
1 REPO @R3@
0 @R2@ REPO
1 NAME Repository Two
0 @R3@ REPO
1 NAME Repository Three
0 TRLR
"""
        temp_path = write_temp_text(self, content)

        controller = AppController()
        controller.load_file(temp_path)

        self.assertIn("CITE", controller.get_entity_types())
        items = controller.get_entity_list_items("CITE")
        self.assertEqual(len(items), 3)
        citation, label = items[0]
        self.assertEqual(citation.pointer, "@S1@")
        self.assertIn("Parish register", label)
        self.assertIn("Lovelace, Ada", label)
        self.assertIn("BIRT", label)
        self.assertIn("17", label)
        self.assertEqual(controller.search_entities("CITE", "Lovelace"), [citation])
        self.assertEqual(
            [
                item.source_pointer
                for item in controller.search_entities("CITE", "@R2@")
            ],
            ["@S1@", "@S2@"],
        )
        self.assertEqual(
            [
                item.source_pointer
                for item in controller.search_entities("CITE", "@R3@")
            ],
            ["@S3@"],
        )

    # Vérifie get entity list items.
    def test_get_entity_list_items(self):
        items = self.controller.get_entity_list_items("INDI")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "@I1@")

        items = self.controller.get_entity_list_items("FAM", "F1")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "@F1@ – Famille sans membres")

        no_items = self.controller.get_entity_list_items("FAM", "X1")
        self.assertEqual(no_items, [])

    # Vérifie search entities by query.
    def test_search_entities_by_query(self):
        individuals = self.controller.search_entities("INDI", "I1")
        self.assertEqual(len(individuals), 1)
        self.assertEqual(individuals[0].pointer, "@I1@")

        families = self.controller.search_entities("FAM", "F1")
        self.assertEqual(len(families), 1)
        self.assertEqual(families[0].pointer, "@F1@")

        no_match = self.controller.search_entities("FAM", "X1")
        self.assertEqual(no_match, [])

        all_families = self.controller.search_entities("FAM", "")
        self.assertEqual(len(all_families), 1)

    # Vérifie search individuals ignores case and accents.
    def test_search_individuals_ignores_case_and_accents(self):
        individual = Individual(
            GedcomEntity("@I2@", "INDI", 0, ["0 @I2@ INDI\n", "1 NAME Léon /Crétel/\n"])
        )
        self.controller.entity_controller.individuals[individual.pointer] = individual

        for query in ("cretel", "crétel", "Crétel", "Cretel"):
            with self.subTest(query=query):
                results = self.controller.search_entities("INDI", query)
                self.assertEqual([item.pointer for item in results], ["@I2@"])

    # Vérifie search families ignores case and accents in member names.
    def test_search_families_ignores_case_and_accents_in_member_names(self):
        individual = Individual(
            GedcomEntity("@I2@", "INDI", 0, ["0 @I2@ INDI\n", "1 NAME Léon /Crétel/\n"])
        )
        family = Family(
            GedcomEntity(
                "@F2@",
                "FAM",
                0,
                ["0 @F2@ FAM\n", "1 HUSB @I2@\n"],
            )
        )
        self.controller.entity_controller.individuals[individual.pointer] = individual
        self.controller.entity_controller.families[family.pointer] = family

        for query in ("cretel", "crétel", "Crétel", "Cretel"):
            with self.subTest(query=query):
                results = self.controller.search_entities("FAM", query)
                self.assertEqual([item.pointer for item in results], ["@F2@"])

    # Vérifie search repositories ignores case and accents.
    def test_search_repositories_ignores_case_and_accents(self):
        repository = Repository(
            GedcomEntity(
                "@R2@",
                "REPO",
                0,
                ["0 @R2@ REPO\n", "1 NAME Dépôt Crétel\n"],
            )
        )
        self.controller.entity_controller.repositories[repository.pointer] = repository

        for query in ("cretel", "crétel", "Crétel", "Cretel"):
            with self.subTest(query=query):
                results = self.controller.search_entities("REPO", query)
                self.assertEqual([item.pointer for item in results], ["@R2@"])

    # Vérifie search sources ignores case and accents.
    def test_search_sources_ignores_case_and_accents(self):
        source = Source(
            GedcomEntity(
                "@S2@",
                "SOUR",
                0,
                [
                    "0 @S2@ SOUR\n",
                    "1 TITL Archives de Crétel\n",
                    "1 REPO @R2@\n",
                ],
            )
        )
        other_source = Source(
            GedcomEntity(
                "@S3@",
                "SOUR",
                0,
                ["0 @S3@ SOUR\n", "1 TITL Other archive\n", "1 REPO @R2@\n"],
            )
        )
        unrelated_source = Source(
            GedcomEntity(
                "@S4@",
                "SOUR",
                0,
                ["0 @S4@ SOUR\n", "1 TITL Unrelated archive\n", "1 REPO @R3@\n"],
            )
        )
        self.controller.entity_controller.sources[source.pointer] = source
        self.controller.entity_controller.sources[other_source.pointer] = other_source
        self.controller.entity_controller.sources[unrelated_source.pointer] = (
            unrelated_source
        )

        for query in ("cretel", "crétel", "Crétel", "Cretel"):
            with self.subTest(query=query):
                results = self.controller.search_entities("SOUR", query)
                self.assertEqual([item.pointer for item in results], ["@S2@"])

        results = self.controller.search_entities("SOUR", "@R2@")
        self.assertEqual([item.pointer for item in results], ["@S2@", "@S3@"])

    # Vérifie search notes ignores case and accents.
    def test_search_notes_ignores_case_and_accents(self):
        note = Note(
            GedcomEntity(
                "@N2@",
                "NOTE",
                0,
                ["0 @N2@ NOTE\n", "1 NOTE Mémoire Crétel\n"],
            )
        )
        self.controller.entity_controller.notes[note.pointer] = note

        for query in ("cretel", "crétel", "Crétel", "Cretel"):
            with self.subTest(query=query):
                results = self.controller.search_entities("NOTE", query)
                self.assertEqual([item.pointer for item in results], ["@N2@"])

    # Vérifie search objects ignores case and accents.
    def test_search_objects_ignores_case_and_accents(self):
        multimedia = MultimediaObject(
            GedcomEntity(
                "@O2@",
                "OBJE",
                0,
                ["0 @O2@ OBJE\n", "1 TITL Photo Crétel\n"],
            )
        )
        self.controller.entity_controller.objects[multimedia.pointer] = multimedia

        for query in ("cretel", "crétel", "Crétel", "Cretel"):
            with self.subTest(query=query):
                results = self.controller.search_entities("OBJE", query)
                self.assertEqual([item.pointer for item in results], ["@O2@"])

    # Vérifie search submitters ignores case and accents.
    def test_search_submitters_ignores_case_and_accents(self):
        submitter = Submitter(
            GedcomEntity(
                "@M2@",
                "SUBM",
                0,
                ["0 @M2@ SUBM\n", "1 NAME Émile Crétel\n"],
            )
        )
        self.controller.entity_controller.submitters[submitter.pointer] = submitter

        for query in ("cretel", "crétel", "Crétel", "Cretel"):
            with self.subTest(query=query):
                results = self.controller.search_entities("SUBM", query)
                self.assertEqual([item.pointer for item in results], ["@M2@"])


if __name__ == "__main__":
    unittest.main()
