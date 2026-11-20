"""Tests de la vue des sources."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.i18n import Translator
from ui.views.source_property_view import SourcePropertyView


class TestSourcePropertyView(unittest.TestCase):
    """Vérifie les sections bibliographiques et les champs additionnels."""

    def setUp(self):
        """Crée une fenêtre racine et une vue de source."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.view = SourcePropertyView(self.root, Mock(), self.translator)

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie display renders all source sections.
    def test_display_renders_all_source_sections(self):
        # Given une source complète
        source = SimpleNamespace(
            pointer="@S1@",
            title="Source",
            author="Auteur",
            pub_date="1900",
            publication="Publication",
            abbreviation="AB",
            agency="Agence",
            record_id="ID",
            repository="@R1@",
            call_number="C1",
            media="M",
            repo_note="Note dépôt",
            text="Texte",
            data_events=[
                {
                    "tag": "DATA",
                    "value": "",
                    "details": [("TEXT", "Détail")],
                }
            ],
            notes=["Note"],
            sources=["@S2@"],
            references=["@R2@"],
            additional_fields=[
                {"tag": "EVEN", "value": "", "details": [("TYPE", "Militaire")]}
            ],
        )

        # When on affiche la source
        self.view.display(source)

        # Then chaque section attendue est présente
        for key in (
            "view.source_bibliography",
            "view.source_repository",
            "view.source_content",
            "view.data_events",
            "view.notes",
            "view.source_links",
            "view.references",
            "view.additional_fields",
        ):
            self.assertIn(self.translator.get(key), self.view.sections)

    # Vérifie display none clears previous content.
    def test_display_none_clears_previous_content(self):
        # Given une vue déjà remplie
        self.view.display(
            SimpleNamespace(pointer="@S1@", title="Source", author="Auteur")
        )

        # When on affiche None
        self.view.display(None)

        # Then la vue est vidée et le titre par défaut est restauré
        self.assertEqual(self.view.sections, {})
        self.assertEqual(
            self.view.title_label.cget("text"), self.translator.get("view.source")
        )


if __name__ == "__main__":
    unittest.main()
