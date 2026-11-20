"""Tests de présentation et de formatage du contrôleur applicatif."""

import unittest

from controllers.entity_types import ENTITY_CONTEXT_BY_TYPE, ENTITY_TYPE_BY_CONTEXT
from gedcom.models.entity import GedcomEntity
from gedcom.models.individual import Individual
from tests.controllers.app_controller_test_case import (
    AppControllerTestMixin,
    DummyEntity,
)


class TestAppControllerPresentation(AppControllerTestMixin, unittest.TestCase):
    """Vérifie les libellés, les noms d'affichage et les clés de tri."""

    # Vérifie get entity type menu display items.
    def test_get_entity_type_menu_display_items(self):
        items = self.controller.get_entity_type_menu_display_items()
        self.assertIn(("Individu", "INDI"), items)
        self.assertIn(("Famille", "FAM"), items)
        self.assertFalse(any("INDI" in label for label, _ in items))
        self.assertFalse(any("FAM" in label for label, _ in items))

    # Vérifie entity type context mappings are inverse.
    def test_entity_type_context_mappings_are_inverse(self):
        self.assertEqual(
            ENTITY_TYPE_BY_CONTEXT,
            {
                context_type: entity_type
                for entity_type, context_type in ENTITY_CONTEXT_BY_TYPE.items()
            },
        )
        self.assertEqual(
            set(ENTITY_CONTEXT_BY_TYPE), set(self.controller.ENTITY_LABELS)
        )

    # Vérifie format details merges continuations.
    def test_format_details_merges_continuations(self):
        # Given une liste de détails contenant des continuations
        details = [
            {"tag": "NOTE", "value": "Texte"},
            {"tag": "CONT", "value": " suite"},
        ]
        # When on formate les détails via la façade
        formatted = self.controller.format_details(details)
        # Then les continuations sont fusionnées dans le texte parent
        self.assertEqual(formatted, [{"tag": "NOTE", "value": "Texte\n suite"}])

    # Vérifie format entity label and context.
    def test_format_entity_label_and_context(self):
        entity = self.controller.get_entity("@I1@")
        self.assertEqual(self.controller.format_entity_label(entity), "@I1@")

        individual = self.controller.get_individual("@I1@")
        self.assertEqual(self.controller.format_entity_label(individual), "@I1@")

        context = self.controller.get_entity_view_context(individual)
        self.assertEqual(context["type"], "individual")
        self.assertIs(context["entity"], individual)
        self.assertIs(context["raw_entity"], individual.entity)

        family = self.controller.get_family("@F1@")
        context = self.controller.get_entity_view_context(family)
        self.assertEqual(context["type"], "family")
        self.assertIs(context["entity"], family)
        self.assertIs(context["raw_entity"], family.entity)

    # Vérifie format multimedia display name preserves absolute file path.
    def test_format_multimedia_display_name_preserves_absolute_file_path(self):
        multimedia = self.controller.get_object("@O1@")
        paths = (
            "/tmp/images/Charles Henri René.jpg",
            r"C:\temp\Charles Henri René.jpg",
        )
        for path in paths:
            with self.subTest(path=path):
                multimedia.file = path
                self.assertEqual(
                    self.controller.format_entity_display_name(multimedia, "OBJE"),
                    path,
                )

    # Vérifie format individual display name uses surname then given name.
    def test_format_individual_display_name_uses_surname_then_given_name(self):
        individual = Individual(
            GedcomEntity(
                "@I2@",
                "INDI",
                0,
                ["0 @I2@ INDI\n", "1 NAME Charles Henri René /Arbon/\n"],
            )
        )

        self.assertEqual(
            self.controller.format_entity_display_name(individual, "INDI"),
            "Arbon, Charles Henri René",
        )

    # Vérifie format individual list name keeps given name for missing surname.
    def test_format_individual_list_name_keeps_given_name_for_missing_surname(self):
        individual = Individual(
            GedcomEntity(
                "@I3@",
                "INDI",
                0,
                ["0 @I3@ INDI\n", "1 NAME Ada\n"],
            )
        )

        self.assertEqual(
            self.controller.format_entity_display_name(individual, "INDI"),
            "Ada",
        )

    # Vérifie format individual list name uses comma when name is missing.
    def test_format_individual_list_name_uses_comma_when_name_is_missing(self):
        individual = Individual(GedcomEntity("@I4@", "INDI", 0, ["0 @I4@ INDI\n"]))

        self.assertEqual(
            self.controller.format_entity_display_name(individual, "INDI"),
            ",",
        )

    # Vérifie sort keys use numeric pointer and surname.
    def test_sort_keys_use_numeric_pointer_and_surname(self):
        pointer_2 = DummyEntity("@I2@", "INDI")
        pointer_10 = DummyEntity("@I10@", "INDI")
        self.assertLess(
            self.controller.get_entity_sort_key(pointer_2, "INDI", "pointer"),
            self.controller.get_entity_sort_key(pointer_10, "INDI", "pointer"),
        )

        surname_adams = Individual(
            GedcomEntity("@I20@", "INDI", 0, ["0 @I20@ INDI\n", "1 NAME Zoe /Adams/\n"])
        )
        surname_martin = Individual(
            GedcomEntity(
                "@I21@", "INDI", 0, ["0 @I21@ INDI\n", "1 NAME Jean /Martin/\n"]
            )
        )
        self.assertLess(
            self.controller.get_entity_sort_key(surname_adams, "INDI", "name"),
            self.controller.get_entity_sort_key(surname_martin, "INDI", "name"),
        )

    # Vérifie resolve pointer preference.
    def test_resolve_pointer_preference(self):
        self.assertIs(
            self.controller.resolve_pointer("@I1@"),
            self.controller.get_individual("@I1@"),
        )
        self.assertIs(
            self.controller.resolve_pointer("@F1@"), self.controller.get_family("@F1@")
        )


if __name__ == "__main__":
    unittest.main()
