"""Tests de la vue des notes."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.i18n import Translator
from ui.views.note_property_view import NotePropertyView


class TestNotePropertyView(unittest.TestCase):
    """Vérifie le texte, les détails et les liens d'une note."""

    def setUp(self):
        """Crée une fenêtre racine et une vue de note."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.view = NotePropertyView(self.root, Mock(), self.translator)

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie display renders text details and links.
    def test_display_renders_text_details_and_links(self):
        # Given une note complète
        note = SimpleNamespace(
            pointer="@N1@",
            text="Texte de la note",
            record_id="ID",
            change_date="1 JAN 2020",
            change_time="12:00",
            source="@S2@",
            sources=["@S1@"],
            references=["@R1@"],
            submitters=["@M1@"],
            additional_fields=[
                {"tag": "EVEN", "value": "", "details": [("TYPE", "Militaire")]}
            ],
        )

        # When on affiche la note
        self.view.display(note)

        # Then les sections attendues sont présentes et le texte est mémorisé
        for key in (
            "view.note",
            "view.note_details",
            "view.sources",
            "view.references",
            "view.submitters",
            "view.additional_fields",
        ):
            self.assertIn(self.translator.get(key), self.view.sections)
        self.assertIsNotNone(self.view.text_widget)

    # Vérifie display none clears previous content.
    def test_display_none_clears_previous_content(self):
        # Given une vue déjà remplie
        self.view.display(SimpleNamespace(pointer="@N1@", text="Texte"))

        # When on affiche None
        self.view.display(None)

        # Then la vue est vidée et le titre par défaut est restauré
        self.assertEqual(self.view.sections, {})
        self.assertEqual(
            self.view.title_label.cget("text"), self.translator.get("view.note")
        )


if __name__ == "__main__":
    unittest.main()
