"""Tests du rendu des pointeurs cliquables des fiches structurées."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.themes import COLORS
from ui.views.structured_link_renderer import StructuredLinkRenderer


class TestStructuredLinkRenderer(unittest.TestCase):
    """Vérifie le style et l'activation des pointeurs cliquables."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    # Vérifie bind styles pointer.
    def test_bind_styles_pointer(self):
        # Given (Arrange) un texte et des gestionnaires
        widget = tk.Text(self.root)
        widget.insert("1.0", "@I1@")
        on_begin = Mock()
        on_finish = Mock()
        # When (Act) on lie un pointeur
        StructuredLinkRenderer.bind(widget, "@I1@", on_begin, on_finish)
        # Then (Assert) le tag pointer est stylé
        self.assertIn("pointer", widget.tag_names("1.0"))
        self.assertEqual(widget.tag_cget("pointer", "foreground"), COLORS["link"])

    # Vérifie begin stores activation start.
    def test_begin_stores_activation_start(self):
        # Given (Arrange) un événement d'appui
        widget = SimpleNamespace()
        event = SimpleNamespace(widget=widget, x=10, y=20)
        # When (Act) on mémorise le départ
        StructuredLinkRenderer.begin(event, "@I1@")
        # Then (Assert) le point de départ est enregistré
        self.assertEqual(widget._pointer_activation_start, ("@I1@", 10, 20))

    # Vérifie finish activates when pointer did not move.
    def test_finish_activates_when_pointer_did_not_move(self):
        # Given (Arrange) un appui sans glissement
        widget = SimpleNamespace(after_idle=Mock())
        StructuredLinkRenderer.begin(SimpleNamespace(widget=widget, x=10, y=10), "@I1@")
        navigate = Mock()
        # When (Act) on relâche au même endroit
        StructuredLinkRenderer.finish(
            SimpleNamespace(widget=widget, x=12, y=10), "@I1@", navigate
        )
        # Then (Assert) la navigation est planifiée
        widget.after_idle.assert_called_once_with(navigate, "@I1@")

    # Vérifie finish ignores drag beyond threshold.
    def test_finish_ignores_drag_beyond_threshold(self):
        # Given (Arrange) un appui qui glisse au-delà du seuil
        widget = SimpleNamespace(after_idle=Mock())
        StructuredLinkRenderer.begin(SimpleNamespace(widget=widget, x=10, y=10), "@I1@")
        navigate = Mock()
        # When (Act) on relâche après un glissement
        StructuredLinkRenderer.finish(
            SimpleNamespace(widget=widget, x=20, y=10), "@I1@", navigate
        )
        # Then (Assert) aucune navigation n'est planifiée
        widget.after_idle.assert_not_called()

    # Vérifie finish ignores release without begin.
    def test_finish_ignores_release_without_begin(self):
        # Given (Arrange) un relâchement sans appui préalable
        widget = SimpleNamespace(after_idle=Mock())
        navigate = Mock()
        # When (Act) on relâche
        StructuredLinkRenderer.finish(
            SimpleNamespace(widget=widget, x=10, y=10), "@I1@", navigate
        )
        # Then (Assert) aucune navigation n'est planifiée
        widget.after_idle.assert_not_called()
