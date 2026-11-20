"""Tests de la vue des individus."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.i18n import Translator
from ui.views.individual_property_view import IndividualPropertyView


class TestIndividualPropertyView(unittest.TestCase):
    """Vérifie les sections affichées pour un individu."""

    def setUp(self):
        """Crée une fenêtre racine et une vue d'individu."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.view = IndividualPropertyView(self.root, Mock(), self.translator)

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie display renders overview and family links.
    def test_display_renders_overview_and_family_links(self):
        # Given un individu avec naissance et liens familiaux
        entity = SimpleNamespace(
            pointer="@I1@",
            name="John /Doe/",
            birth_date="1 JAN 1900",
            birth_place="Paris",
            famc="@F1@",
            fams=["@F2@"],
            events=[],
            occupations=[],
            properties=[],
            notes=[],
            texts=[],
            obje=[],
        )

        # When on affiche l'individu
        self.view.display(entity)

        # Then les sections attendues sont présentes
        self.assertEqual(self.view.title_label.cget("text"), "John Doe")
        self.assertIn(
            self.translator.get("view.individual_overview"), self.view.sections
        )
        self.assertIn(
            self.translator.get("view.individual_family_links"), self.view.sections
        )
        overview_section = self.view.sections[
            self.translator.get("view.individual_overview")
        ]
        overview_rows = self.view._section_rows[overview_section]
        self.assertIn(
            (self.translator.get("view.birth_date"), "1 JAN 1900"), overview_rows
        )

    # Vérifie display renders events and lists.
    def test_display_renders_events_and_lists(self):
        # Given un individu avec événements et listes optionnelles
        entity = SimpleNamespace(
            pointer="@I1@",
            name="Jane /Doe/",
            events=[
                {
                    "tag": "EVEN",
                    "value": "",
                    "children": [{"tag": "TYPE", "value": "Militaire"}],
                }
            ],
            occupations=[{"occupation": "Agriculteur", "date": "1920"}],
            properties=[{"value": "Terrain"}],
            notes=["Note"],
            texts=["Texte"],
            obje=["@O1@"],
        )

        # When on affiche l'individu
        self.view.display(entity)

        # Then chaque liste possède sa section
        for key in (
            "view.events",
            "view.occupations",
            "view.properties",
            "view.notes",
            "view.texts",
            "view.gallery",
        ):
            self.assertIn(self.translator.get(key), self.view.sections)

    # Vérifie display none clears previous content.
    def test_display_none_clears_previous_content(self):
        # Given une vue déjà remplie
        self.view.display(SimpleNamespace(pointer="@I1@", name="John /Doe/", events=[]))

        # When on affiche None
        self.view.display(None)

        # Then la vue est vidée et le titre par défaut est restauré
        self.assertEqual(self.view.sections, {})
        self.assertEqual(
            self.view.title_label.cget("text"),
            self.translator.get("view.individual"),
        )


if __name__ == "__main__":
    unittest.main()
