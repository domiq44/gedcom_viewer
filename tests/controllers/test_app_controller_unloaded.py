"""Tests des valeurs de repli du contrôleur applicatif non chargé."""

import unittest

from controllers.app_controller import AppController
from gedcom.models.entity import GedcomEntity
from gedcom.models.individual import Individual
from tests.controllers.app_controller_test_case import DummyEntity
from ui.i18n import Translator


class TestAppControllerUnloaded(unittest.TestCase):
    """Vérifie les valeurs par défaut d'une façade sans fichier chargé."""

    # Vérifie entity labels are immutable.
    def test_entity_labels_are_immutable(self):
        # Given les libellés par défaut de la façade
        # When on tente de les modifier
        with self.assertRaises(TypeError):
            AppController.ENTITY_LABELS["INDI"] = "Modifié"

        # Then le mapping reste inchangé
        self.assertEqual(AppController.ENTITY_LABELS["INDI"], "Individu")

    # Vérifie unloaded type menu uses translated labels.
    def test_unloaded_type_menu_uses_translated_labels(self):
        controller = AppController(translator=Translator("en"))

        items = controller.get_all_entity_type_menu_display_items()

        self.assertIn(("Individual", "INDI"), items)
        self.assertIn(("Family", "FAM"), items)

    # Vérifie unloaded controller returns safe defaults.
    def test_unloaded_controller_returns_safe_defaults(self):
        # Given une façade sans contrôleurs spécialisés
        controller = AppController(translator=Translator("fr"))
        entity = DummyEntity("@I1@", "INDI")
        individual = Individual(
            GedcomEntity(
                "@I1@",
                "INDI",
                0,
                ["0 @I1@ INDI\n", "1 NAME John /Doe/\n"],
            )
        )

        # When on interroge les opérations dépendant du chargement
        types = controller.get_entity_types()
        items = controller.get_entity_list_items("INDI")
        label = controller.get_entity_type_label("INDI")
        display_name = controller.format_entity_display_name(individual, "INDI")
        sort_key = controller.get_entity_sort_key(entity, "INDI", "pointer")
        context = controller.get_entity_display_info(entity)
        raw_block = controller.get_raw_block(entity)
        pointer = controller.resolve_pointer("@I1@")

        # Then les valeurs par défaut restent exploitables
        self.assertEqual(types, [])
        self.assertEqual(items, [])
        self.assertEqual(label, "Individu")
        self.assertEqual(display_name, "Doe, John")
        self.assertEqual(sort_key, (False, 1, "@i1@"))
        self.assertEqual(context["type"], "raw")
        self.assertEqual(context["raw_block"], "0 @I1@ INDI\n")
        self.assertEqual(raw_block, "0 @I1@ INDI\n")
        self.assertIsNone(pointer)

    # Vérifie unloaded controller formats details without presentation.
    def test_unloaded_controller_formats_details_without_presentation(self):
        # Given une façade sans présentateur
        controller = AppController()
        details = [
            {"tag": "NOTE", "value": "Texte"},
            {"tag": "CONT", "value": " suite"},
        ]

        # When on formate les détails
        formatted = controller.format_details(details)

        # Then les continuations sont fusionnées
        self.assertEqual(formatted, [{"tag": "NOTE", "value": "Texte\n suite"}])

    # Vérifie unloaded controller returns empty collections.
    def test_unloaded_controller_returns_empty_collections(self):
        # Given une façade sans contrôleurs spécialisés
        controller = AppController()

        # When on demande les collections dépendant du chargement
        menu_items = controller.get_entity_type_menu_items()
        menu_display_items = controller.get_entity_type_menu_display_items()
        entities = controller.list_entities("INDI")
        search_results = controller.search_entities("INDI", "John")
        entity_list = controller.get_entity_list("INDI")
        entity_list_items = controller.get_entity_list_items("INDI")

        # Then les collections sont vides
        self.assertEqual(menu_items, [])
        self.assertEqual(menu_display_items, [])
        self.assertEqual(entities, [])
        self.assertEqual(search_results, [])
        self.assertEqual(entity_list, [])
        self.assertEqual(entity_list_items, [])

    # Vérifie unloaded controller returns none for entity pointers.
    def test_unloaded_controller_returns_none_for_entity_pointers(self):
        # Given une façade sans contrôleurs spécialisés
        controller = AppController()

        # When on résout des pointeurs d'entités
        pointers = [
            controller.get_entity("@I1@"),
            controller.get_individual("@I1@"),
            controller.get_family("@F1@"),
            controller.get_source("@S1@"),
            controller.get_repository("@R1@"),
            controller.get_note("@N1@"),
            controller.get_object("@O1@"),
            controller.get_submitter("@M1@"),
        ]

        # Then aucune entité n'est résolue
        self.assertEqual(pointers, [None] * 8)

    # Vérifie unloaded controller uses safe labels and contexts.
    def test_unloaded_controller_uses_safe_labels_and_contexts(self):
        # Given une façade sans contrôleurs spécialisés
        controller = AppController(translator=Translator("fr"))
        entity = DummyEntity("@I1@", "INDI")

        # When on demande les libellés et contextes de repli
        unknown_label = controller.get_entity_type_label("UNKNOWN")
        entity_label = controller.format_entity_label(entity)
        context = controller.get_entity_view_context(entity)

        # Then les valeurs par défaut restent exploitables
        self.assertEqual(unknown_label, "UNKNOWN")
        self.assertEqual(entity_label, "@I1@")
        self.assertEqual(context["type"], "raw")
        self.assertEqual(context["raw_entity"], entity)

    # Vérifie unloaded controller handles invalid raw blocks.
    def test_unloaded_controller_handles_invalid_raw_blocks(self):
        # Given une façade sans présentateur et des entités sans bloc brut exploitable
        class InvalidRawEntity:
            """Entité dont le bloc brut échoue."""

            def raw_block(self):
                """Échoue volontairement."""
                raise ValueError("boom")

        class EntityWithoutRawBlock:
            """Entité sans méthode de bloc brut."""

        controller = AppController()

        # When on demande les blocs bruts
        default_context = controller.get_entity_display_info(InvalidRawEntity())
        invalid_block = controller.get_raw_block(InvalidRawEntity())
        missing_block = controller.get_raw_block(EntityWithoutRawBlock())
        none_block = controller.get_raw_block(None)

        # Then les valeurs de repli sont vides
        self.assertEqual(default_context["raw_block"], "")
        self.assertEqual(invalid_block, "")
        self.assertEqual(missing_block, "")
        self.assertEqual(none_block, "")


if __name__ == "__main__":
    unittest.main()
