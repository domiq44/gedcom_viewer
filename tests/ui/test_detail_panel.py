"""Tests du panneau de détail GEDCOM."""

import tkinter as tk
import unittest

from ui.detail_panel import DetailPanel
from ui.i18n import Translator
from ui.themes import COLORS


class TestDetailPanel(unittest.TestCase):
    """Vérifie le formatage, la visibilité et la copie du GEDCOM brut."""

    def setUp(self):
        """Crée une fenêtre racine et un panneau de détail."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.panel = DetailPanel(self.root, Translator("fr"))

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie format gedcom block indents by level.
    def test_format_gedcom_block_indents_by_level(self):
        # Given un bloc GEDCOM avec une ligne vide et une ligne malformée
        content = "0 @I1@ INDI\n1 NAME John\n\n2 SEX M\n"

        # When on formatte le bloc
        rendered = DetailPanel._format_gedcom_block(content)

        # Then chaque niveau est indenté de deux espaces
        self.assertEqual(
            rendered,
            "0 @I1@ INDI\n  1 NAME John\n\n    2 SEX M",
        )

    # Vérifie display raw renders indented content.
    def test_display_raw_renders_indented_content(self):
        # Given un panneau avec l'indentation active
        self.panel.display_raw("0 @I1@ INDI\n1 NAME John\n")

        # When on lit le contenu affiché
        # Then les niveaux sont indentés
        self.assertEqual(
            self.panel.text_area.get("1.0", "end-1c"),
            "0 @I1@ INDI\n  1 NAME John",
        )

    # Vérifie display raw can disable indentation.
    def test_display_raw_can_disable_indentation(self):
        # Given un panneau sans indentation
        self.panel.indent_var.set(False)

        # When on affiche un bloc
        self.panel.display_raw("0 @I1@ INDI\n1 NAME John\n")

        # Then le texte brut est conservé
        self.assertEqual(
            self.panel.text_area.get("1.0", "end-1c"),
            "0 @I1@ INDI\n1 NAME John\n",
        )

    # Vérifie set view visibility keeps one view visible.
    def test_set_view_visibility_keeps_one_view_visible(self):
        # Given un panneau de détail
        # When on masque les deux vues
        self.panel.set_view_visibility(False, False)

        # Then la vue entité reste visible
        self.assertFalse(self.panel.show_gedcom_view_var.get())
        self.assertTrue(self.panel.show_entity_view_var.get())

    # Vérifie copy to clipboard returns false when empty.
    def test_copy_to_clipboard_returns_false_when_empty(self):
        # Given un panneau sans contenu
        # When on copie
        # Then l'opération échoue
        self.assertFalse(self.panel.copy_to_clipboard())

    # Vérifie copy to clipboard copies rendered content.
    def test_copy_to_clipboard_copies_rendered_content(self):
        # Given un panneau avec du contenu
        self.panel.display_raw("0 @I1@ INDI\n")
        self.root.update()

        # When on copie
        copied = self.panel.copy_to_clipboard()

        # Then le presse-papiers contient le texte affiché
        self.assertTrue(copied)
        self.assertEqual(self.panel.winfo_toplevel().clipboard_get(), "0 @I1@ INDI")

    # Vérifie apply theme uses current background.
    def test_apply_theme_uses_current_background(self):
        # Given un panneau de détail
        # When on réapplique le thème
        self.panel.apply_theme()

        # Then la couleur de fond correspond au thème courant
        self.assertEqual(self.panel.cget("bg"), COLORS["background"])


if __name__ == "__main__":
    unittest.main()
