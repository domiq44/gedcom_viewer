"""Tests de la vue des objets multimédia."""

import tempfile
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.i18n import Translator
from ui.views.multimedia_property_view import MultimediaPropertyView


class TestMultimediaPropertyView(unittest.TestCase):
    """Vérifie le titre, les détails et l'aperçu d'un objet multimédia."""

    def setUp(self):
        """Crée une fenêtre racine et une vue multimédia."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.view = MultimediaPropertyView(self.root, Mock(), self.translator)

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie display renders title details and notes.
    def test_display_renders_title_details_and_notes(self):
        # Given un objet multimédia avec fichier et note
        multimedia = SimpleNamespace(
            pointer="@O1@",
            title="Photo",
            file="/tmp/photo.jpg",
            file_records=[
                {"file": "/tmp/photo.jpg", "format": "jpg", "title": "Photo"}
            ],
            notes=["Note"],
            additional_fields=[{"tag": "NOTE", "value": "Détail", "details": []}],
        )

        # When on affiche l'objet
        self.view.display(multimedia)

        # Then le titre et les sections attendues sont présents
        self.assertEqual(self.view.title_label.cget("text"), "Photo")
        for key in (
            "view.multimedia_details",
            "view.note",
            "view.additional_fields",
        ):
            self.assertIn(self.translator.get(key), self.view.sections)
        self.assertIsNotNone(self.view.note_widget)

    # Vérifie display none shows placeholder.
    def test_display_none_shows_placeholder(self):
        # Given une vue vide
        # When on affiche None
        self.view.display(None)

        # Then l'aperçu indisponible est affiché
        self.assertEqual(
            self.view.preview_label.cget("text"),
            self.translator.get("view.preview_unavailable"),
        )
        self.assertEqual(self.view.sections, {})

    # Vérifie set base path only accepts directories.
    def test_set_base_path_only_accepts_directories(self):
        # Given un répertoire temporaire et un chemin inexistant
        # When on définit le répertoire de base
        temp_dir = tempfile.gettempdir()
        self.view.set_base_path(temp_dir)
        accepted = self.view.base_path
        self.view.set_base_path("/dossier/inexistant")

        # Then seul le répertoire existant est conservé
        self.assertEqual(accepted, temp_dir)
        self.assertIsNone(self.view.base_path)


if __name__ == "__main__":
    unittest.main()
