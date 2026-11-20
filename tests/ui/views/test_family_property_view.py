"""Tests de la vue des familles."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.i18n import Translator
from ui.views.family_property_view import FamilyPropertyView


class TestFamilyPropertyView(unittest.TestCase):
    """Vérifie les membres, mariages et champs additionnels."""

    def setUp(self):
        """Crée une fenêtre racine et une vue de famille."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.view = FamilyPropertyView(self.root, Mock(), self.translator)

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie display renders members children and marriages.
    def test_display_renders_members_children_and_marriages(self):
        # Given une famille avec parents, enfants et mariage
        family = SimpleNamespace(
            pointer="@F1@",
            husband="@I1@",
            wife="@I2@",
            children=["@I3@"],
            number_of_children=1,
            marriages=[
                {
                    "tag": "MARR",
                    "value": "",
                    "details": [("DATE", "1 JAN 1900"), ("PLAC", "Paris")],
                }
            ],
        )

        # When on affiche la famille
        self.view.display(family)

        # Then les sections membres, enfants et mariages sont présentes
        self.assertIn(self.translator.get("view.family_members"), self.view.sections)
        self.assertIn(self.translator.get("view.children"), self.view.sections)
        self.assertIn(self.translator.get("view.marriages"), self.view.sections)
        members_section = self.view.sections[self.translator.get("view.family_members")]
        members = self.view._section_rows[members_section]
        self.assertEqual(len(members), 2)

    # Vérifie display renders additional fields.
    def test_display_renders_additional_fields(self):
        # Given une famille avec un champ additionnel
        family = SimpleNamespace(
            pointer="@F1@",
            additional_fields=[
                {"tag": "EVEN", "value": "", "details": [("TYPE", "Militaire")]}
            ],
        )

        # When on affiche la famille
        self.view.display(family)

        # Then la section des champs additionnels est créée
        section = self.translator.get("view.additional_fields")
        self.assertIn(section, self.view.sections)
        section_frame = self.view.sections[section]
        self.assertEqual(len(self.view._section_rows[section_frame]), 2)

    # Vérifie display none clears previous content.
    def test_display_none_clears_previous_content(self):
        # Given une vue déjà remplie
        self.view.display(SimpleNamespace(pointer="@F1@", husband="@I1@"))

        # When on affiche None
        self.view.display(None)

        # Then la vue est vidée et le titre par défaut est restauré
        self.assertEqual(self.view.sections, {})
        self.assertEqual(
            self.view.title_label.cget("text"), self.translator.get("view.family")
        )

    # Vérifie display family events ignores other tags and renders value.
    def test_display_family_events_ignores_other_tags_and_renders_value(self):
        # Given une famille avec un événement DIV et un événement MARR
        section = self.view._section("Événements")
        events = [
            SimpleNamespace(tag="DIV", value="1910", details=[]),
            SimpleNamespace(
                tag="MARR",
                value="1900",
                details=[("", "ignored"), ("DATE", "1 JAN 1900")],
            ),
        ]

        # When on affiche les événements MARR
        with self.assertLogs("ui.views.entity_view_base", level="WARNING"):
            row = self.view._display_family_events(
                section, events, "MARR", "view.marriage_number"
            )

        # Then seul l'événement MARR est rendu
        self.assertEqual(row, 2)
        self.assertEqual(len(self.view._section_rows[section]), 2)

    # Vérifie display additional fields handles objects and empty details.
    def test_display_additional_fields_handles_objects_and_empty_details(self):
        # Given un champ additionnel objet avec un détail sans tag
        section = self.view._section("Champs additionnels")
        fields = [
            SimpleNamespace(
                tag="EVEN",
                value="",
                details=[SimpleNamespace(), ("TYPE", "Militaire")],
            )
        ]

        # When on affiche les champs additionnels
        self.view._render_additional_fields(section, fields)

        # Then seuls les détails valides sont rendus
        self.assertEqual(len(self.view._section_rows[section]), 2)

    # Vérifie display renders boolean overview field.
    def test_display_renders_boolean_overview_field(self):
        # Given une famille avec un champ booléen
        family = SimpleNamespace(pointer="@F1@", number_of_children=True)

        # When on affiche la famille
        self.view.display(family)

        # Then la valeur booléenne est traduite
        section = self.translator.get("view.family")
        rows = self.view._section_rows[self.view.sections[section]]
        self.assertIn("Oui", [value for _label, value in rows])

    # Vérifie display uses marriage date and place fallbacks.
    def test_display_uses_marriage_date_and_place_fallbacks(self):
        # Given une famille sans événement mariage mais avec date et lieu
        family = SimpleNamespace(
            pointer="@F1@",
            marriage_date="1 JAN 1900",
            marriage_place="Paris",
        )

        # When on affiche la famille
        self.view.display(family)

        # Then les champs de repli sont rendus
        section = self.translator.get("view.family")
        rows = self.view._section_rows[self.view.sections[section]]
        values = [value for _label, value in rows]
        self.assertIn("1 JAN 1900", values)
        self.assertIn("Paris", values)

    # Vérifie display uses divorce date and place fallbacks.
    def test_display_uses_divorce_date_and_place_fallbacks(self):
        # Given une famille sans événement divorce mais avec date et lieu
        family = SimpleNamespace(
            pointer="@F1@",
            divorce_date="1 JAN 1910",
            divorce_place="Lyon",
        )

        # When on affiche la famille
        self.view.display(family)

        # Then les champs de repli sont rendus
        section = self.translator.get("view.family")
        rows = self.view._section_rows[self.view.sections[section]]
        values = [value for _label, value in rows]
        self.assertIn("1 JAN 1910", values)
        self.assertIn("Lyon", values)


if __name__ == "__main__":
    unittest.main()
