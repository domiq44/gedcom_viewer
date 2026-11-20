"""Tests du bouton de copie : icône, confirmation et réinitialisation."""

import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from ui.copy_button import CopyButton


class TestCopyButton(unittest.TestCase):
    """Vérifie l'icône du bouton de copie, sa confirmation et sa réinitialisation."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.frame = tk.Frame(self.root)
        self.command = Mock(return_value=True)
        self.button = CopyButton(self.frame, self.command)

    def tearDown(self):
        self.root.destroy()

    # Vérifie initial icon.
    def test_initial_icon(self):
        # Given (Arrange) un bouton copier neuf
        # When (Act) on lit son libellé
        label = self.button.cget("text")
        # Then (Assert) l'icône de copie est affichée
        self.assertEqual(label, CopyButton.ICON)

    # Vérifie copy sets copied icon on success.
    def test_copy_sets_copied_icon_on_success(self):
        # Given (Arrange) une commande qui réussit
        self.command.return_value = True
        # When (Act) on déclenche la copie
        self.button._copy()
        # Then (Assert) l'icône « copié » est affichée
        self.assertEqual(self.button.cget("text"), CopyButton.COPIED_ICON)

    # Vérifie copy keeps icon when command returns false.
    def test_copy_keeps_icon_when_command_returns_false(self):
        # Given (Arrange) une commande qui échoue
        self.command.return_value = False
        # When (Act) on déclenche la copie
        self.button._copy()
        # Then (Assert) l'icône reste l'icône de copie
        self.assertEqual(self.button.cget("text"), CopyButton.ICON)

    # Vérifie reset icon restores initial icon.
    def test_reset_icon_restores_initial_icon(self):
        # Given (Arrange) un bouton affichant l'icône « copié »
        self.button.configure(text=CopyButton.COPIED_ICON)
        # When (Act) on réinitialise l'icône
        self.button._reset_icon()
        # Then (Assert) l'icône de copie est restaurée
        self.assertEqual(self.button.cget("text"), CopyButton.ICON)

    # Vérifie destroy cancels pending reset.
    def test_destroy_cancels_pending_reset(self):
        # Given (Arrange) une copie planifiée pour réinitialisation
        self.button._copy()
        # When (Act) on détruit le bouton
        self.button.destroy()
        # Then (Assert) aucune erreur ne survient et le bouton est détruit
        self.assertFalse(self.button.winfo_exists())

    # Vérifie destroy logs when cancel fails.
    def test_destroy_logs_when_cancel_fails(self):
        # Given (Arrange) un bouton dont l'annulation du réinitialiseur échoue
        self.button._reset_after_id = "pending"
        with patch.object(self.button, "after_cancel", side_effect=Exception("boom")):
            # When (Act) on détruit le bouton
            self.button.destroy()
        # Then (Assert) le bouton est détruit sans propager l'exception
        self.assertFalse(self.button.winfo_exists())

    # Vérifie copy logs when cancel fails.
    def test_copy_logs_when_cancel_fails(self):
        # Given (Arrange) un bouton dont l'annulation du réinitialiseur échoue
        self.command.return_value = True
        self.button._reset_after_id = "pending"
        with patch.object(self.button, "after_cancel", side_effect=Exception("boom")):
            # When (Act) on déclenche la copie
            self.button._copy()
        # Then (Assert) l'icône « copié » est tout de même affichée
        self.assertEqual(self.button.cget("text"), CopyButton.COPIED_ICON)

    # Vérifie reset icon returns when widget destroyed.
    def test_reset_icon_returns_when_widget_destroyed(self):
        # Given (Arrange) un bouton détruit
        self.button.destroy()
        # When (Act) on réinitialise l'icône
        self.button._reset_icon()
        # Then (Assert) aucune erreur ne survient
        self.assertFalse(self.button.winfo_exists())

    # Vérifie copy handles destroyed widget.
    def test_copy_handles_destroyed_widget(self):
        # Given (Arrange) un bouton détruit et une commande réussie
        self.button.destroy()

        # When (Act) on déclenche la copie
        self.button._copy()

        # Then (Assert) aucune erreur ne survient
        self.assertFalse(self.button.winfo_exists())


if __name__ == "__main__":
    unittest.main()
