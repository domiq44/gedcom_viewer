"""Base de test partagée pour la fenêtre principale GEDCOM."""

import os
import tempfile
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from controllers.detail_formatter import merge_text_continuations
from ui.main_window import GedcomViewer


class GedcomViewerTestCase(unittest.TestCase):
    """Prépare une fenêtre principale isolée et un fichier de préférences temporaire."""

    @staticmethod
    def _widget_text(widget):
        """Retourne le texte affiché par un widget texte ou un bouton."""
        if isinstance(widget, tk.Text):
            return widget.get("1.0", "end-1c")
        return widget.cget("text")

    def setUp(self):
        """Crée la fenêtre principale avec un contrôleur simulé."""
        self.root = tk.Tk()
        self.root.withdraw()
        with patch.object(GedcomViewer, "_load_recent_files", return_value=[]):
            self.viewer = GedcomViewer(self.root)
        settings_file = tempfile.NamedTemporaryFile(delete=False)
        settings_file.close()
        self.viewer.SETTINGS_PATH = settings_file.name
        self.settings_file = settings_file.name
        self.viewer.entity_view_manager.views["family"].set_name_resolver(
            lambda pointer: None
        )
        self.viewer.highlighter = Mock()
        self.viewer.controller = Mock()
        self.viewer.controller.format_details.side_effect = merge_text_continuations
        self.viewer.controller.format_entity_summary.return_value = {
            "title": "",
            "subtitle": "",
            "facts": [],
        }

    def tearDown(self):
        """Ferme la fenêtre et supprime le fichier de préférences temporaire."""
        self.viewer._on_close()
        if os.path.exists(self.settings_file):
            os.unlink(self.settings_file)
