"""Tests du module d'info-bulles (ui.tooltip)."""

import tkinter as tk
import unittest
from unittest.mock import patch

from ui.tooltip import Tooltip


class TestTooltip(unittest.TestCase):
    """Vérifie la planification, l'affichage et la destruction de l'infobulle."""

    def setUp(self):
        self.root = tk.Tk()
        self.widget = tk.Label(self.root, text="cible")
        self.widget.pack()
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    # Vérifie show creates bubble when widget mapped.
    def test_show_creates_bubble_when_widget_mapped(self):
        # Given (Arrange) un widget visible et une infobulle
        tooltip = Tooltip(self.widget, "texte")
        # When (Act) on affiche l'infobulle
        tooltip._show()
        # Then (Assert) une fenêtre d'infobulle existe
        self.assertIsNotNone(tooltip.window)
        self.assertTrue(tooltip.window.winfo_exists())

    # Vérifie show skips when widget not mapped.
    def test_show_skips_when_widget_not_mapped(self):
        # Given (Arrange) un widget non affiché
        hidden = tk.Label(self.root)
        tooltip = Tooltip(hidden, "texte")
        # When (Act) on affiche l'infobulle
        tooltip._show()
        # Then (Assert) aucune fenêtre n'est créée
        self.assertIsNone(tooltip.window)

    # Vérifie hide destroys existing bubble.
    def test_hide_destroys_existing_bubble(self):
        # Given (Arrange) une infobulle affichée
        tooltip = Tooltip(self.widget, "texte")
        tooltip._show()
        # When (Act) on masque l'infobulle
        tooltip._hide()
        # Then (Assert) la fenêtre est détruite
        self.assertIsNone(tooltip.window)

    # Vérifie schedule arms deferred display.
    def test_schedule_arms_deferred_display(self):
        # Given (Arrange) une infobulle
        tooltip = Tooltip(self.widget, "texte")
        # When (Act) on planifie l'affichage
        tooltip._schedule()
        # Then (Assert) un rappel différé est armé
        self.assertIsNotNone(tooltip.after_id)

    # Vérifie schedule handles after error.
    def test_schedule_handles_after_error(self):
        # Given (Arrange) un widget dont la planification échoue
        tooltip = Tooltip(self.widget, "texte")

        # When (Act) on planifie l'affichage
        with patch.object(self.widget, "after", side_effect=tk.TclError("boom")):
            tooltip._schedule()

        # Then (Assert) aucun rappel n'est armé
        self.assertIsNone(tooltip.after_id)

    # Vérifie show handles tcl error.
    def test_show_handles_tcl_error(self):
        # Given (Arrange) un widget dont l'état ne peut plus être lu
        tooltip = Tooltip(self.widget, "texte")

        # When (Act) on tente d'afficher l'infobulle
        with patch.object(
            self.widget, "winfo_ismapped", side_effect=tk.TclError("boom")
        ):
            tooltip._show()

        # Then (Assert) aucune fenêtre n'est créée
        self.assertIsNone(tooltip.window)

    # Vérifie hide cancels pending callback.
    def test_hide_cancels_pending_callback(self):
        # Given (Arrange) une infobulle avec un affichage planifié
        tooltip = Tooltip(self.widget, "texte")
        tooltip._schedule()
        # When (Act) on masque avant l'échéance
        tooltip._hide()
        # Then (Assert) le rappel est annulé
        self.assertIsNone(tooltip.after_id)

    # Vérifie schedule handles destroyed widget.
    def test_schedule_handles_destroyed_widget(self):
        # Given (Arrange) un widget détruit
        tooltip = Tooltip(self.widget, "texte")
        self.widget.destroy()

        # When (Act) on planifie l'affichage
        tooltip._schedule()

        # Then (Assert) aucun rappel n'est armé
        self.assertIsNone(tooltip.after_id)

    # Vérifie hide handles cancel failure.
    def test_hide_handles_cancel_failure(self):
        # Given (Arrange) une infobulle avec un rappel annulable en échec
        tooltip = Tooltip(self.widget, "texte")
        tooltip._schedule()

        # When (Act) on masque alors que l'annulation échoue
        with patch.object(self.widget, "after_cancel", side_effect=tk.TclError("boom")):
            tooltip._hide()

        # Then (Assert) l'état est nettoyé sans exception
        self.assertIsNone(tooltip.after_id)


if __name__ == "__main__":
    unittest.main()
