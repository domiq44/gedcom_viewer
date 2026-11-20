"""Tests de la fabrique de lignes des fiches structurées."""

import tkinter as tk
import unittest
from unittest.mock import Mock

from ui.themes import COLORS
from ui.views.structured_row_factory import StructuredRowFactory


class TestStructuredRowFactory(unittest.TestCase):
    """Vérifie la création des widgets de ligne tag/valeur."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.frame = tk.Frame(self.root)
        self.factory = StructuredRowFactory(
            bind_scroll=Mock(),
            on_pointer_begin=Mock(),
            on_pointer_end=Mock(),
        )

    def tearDown(self):
        self.root.destroy()

    # Vérifie create returns selectable disabled widgets.
    def test_create_returns_selectable_disabled_widgets(self):
        # Given (Arrange) une fabrique et un cadre
        # When (Act) on crée une ligne sans pointeur
        tag_widget, value_widget = self.factory.create(
            self.frame, 0, "NAME", "John /Doe/"
        )
        # Then (Assert) les widgets sont des textes sélectionnables désactivés
        self.assertIsInstance(tag_widget, tk.Text)
        self.assertIsInstance(value_widget, tk.Text)
        self.assertEqual(tag_widget.get("1.0", "end-1c"), "NAME")
        self.assertEqual(value_widget.get("1.0", "end-1c"), "John /Doe/")
        self.assertEqual(str(value_widget.cget("state")), "disabled")

    # Vérifie create binds pointer when pointer given.
    def test_create_binds_pointer_when_pointer_given(self):
        # Given (Arrange) une fabrique et un cadre
        # When (Act) on crée une ligne avec pointeur
        _tag_widget, value_widget = self.factory.create(
            self.frame, 0, "FAMS", "@F1@", pointer="@F1@"
        )
        # Then (Assert) le tag pointer est appliqué avec la couleur lien
        self.assertIn("pointer", value_widget.tag_names("1.0"))
        self.assertEqual(value_widget.tag_cget("pointer", "foreground"), COLORS["link"])

    # Vérifie create does not bind pointer without pointer.
    def test_create_does_not_bind_pointer_without_pointer(self):
        # Given (Arrange) une fabrique et un cadre
        # When (Act) on crée une ligne sans pointeur
        _tag_widget, value_widget = self.factory.create(
            self.frame, 0, "NAME", "John /Doe/"
        )
        # Then (Assert) aucun tag pointer n'est appliqué
        self.assertNotIn("pointer", value_widget.tag_names("1.0"))

    # Vérifie fit value height ignores destroyed widget.
    def test_fit_value_height_ignores_destroyed_widget(self):
        """Vérifie qu'un widget détruit ne provoque pas d'exception."""
        # Given (Arrange) un widget détruit
        widget = tk.Text(self.root)
        widget.destroy()
        # When (Act) on ajuste sa hauteur
        result = StructuredRowFactory._fit_value_height(widget)
        # Then (Assert) aucune exception ne survient
        self.assertIsNone(result)

    # Vérifie fit value height keeps minimum height.
    def test_fit_value_height_keeps_minimum_height(self):
        """Vérifie que la hauteur minimale reste d'une ligne."""
        # Given (Arrange) un texte vide
        widget = tk.Text(self.root, width=1, height=1, wrap="word")
        # When (Act) on ajuste sa hauteur
        StructuredRowFactory._fit_value_height(widget)
        # Then (Assert) la hauteur reste au minimum d'une ligne
        self.assertEqual(int(widget.cget("height")), 1)

    # Vérifie fit value height ajuste la hauteur pour un texte multiligne.
    def test_fit_value_height_adjusts_height_when_widget_visible_and_sized(self):
        # Given (Arrange) un mock avec dimensions positives et plusieurs lignes
        widget = Mock()
        widget.winfo_exists.return_value = True
        widget.winfo_viewable.return_value = True
        widget.winfo_width.return_value = 200
        widget.winfo_height.return_value = 100
        widget._fitting_height = False
        widget.count.return_value = [3]
        widget.cget.return_value = 1
        # When (Act) on ajuste sa hauteur
        StructuredRowFactory._fit_value_height(widget)
        # Then (Assert) la hauteur est configurée à 3
        widget.configure.assert_called_once_with(height=3)

    # Vérifie fit value height retourne tôt si largeur ou hauteur nulle.
    def test_fit_value_height_returns_early_when_width_or_height_zero(self):
        # Given (Arrange) un mock avec une largeur nulle
        widget = Mock()
        widget.winfo_exists.return_value = True
        widget.winfo_viewable.return_value = True
        widget.winfo_width.return_value = 0
        widget.winfo_height.return_value = 100
        # When (Act) on ajuste sa hauteur
        result = StructuredRowFactory._fit_value_height(widget)
        # Then (Assert) aucune modification et aucune exception
        self.assertIsNone(result)

    # Vérifie fit value height retourne tôt si _fitting_height est vrai.
    def test_fit_value_height_returns_early_when_fitting_flag_set(self):
        # Given (Arrange) un mock avec le drapeau _fitting_height activé
        widget = Mock()
        widget.winfo_exists.return_value = True
        widget.winfo_viewable.return_value = True
        widget.winfo_width.return_value = 100
        widget.winfo_height.return_value = 100
        widget._fitting_height = True
        # When (Act) on ajuste sa hauteur
        result = StructuredRowFactory._fit_value_height(widget)
        # Then (Assert) aucune modification et aucune exception
        self.assertIsNone(result)

    # Vérifie fit value height ajuste la hauteur quand le nombre de lignes change.
    def test_fit_value_height_updates_height_when_line_count_changes(self):
        # Given (Arrange) un mock simulant 5 lignes alors que la hauteur est 1
        widget = Mock()
        widget.winfo_exists.return_value = True
        widget.winfo_viewable.return_value = True
        widget.winfo_width.return_value = 100
        widget.winfo_height.return_value = 100
        widget._fitting_height = False
        widget.count.return_value = [5]
        widget.cget.return_value = 1
        # When (Act) on ajuste sa hauteur
        StructuredRowFactory._fit_value_height(widget)
        # Then (Assert) la hauteur est configurée à 5
        widget.configure.assert_called_once_with(height=5)

    # Vérifie fit value height ignore l'erreur Tcl.
    def test_fit_value_height_ignores_tcl_error(self):
        # Given (Arrange) un mock qui lève tk.TclError sur winfo_exists
        widget = Mock()
        widget.winfo_exists.side_effect = tk.TclError("widget destroyed")
        # When (Act) on ajuste sa hauteur
        result = StructuredRowFactory._fit_value_height(widget)
        # Then (Assert) aucune exception ne survient
        self.assertIsNone(result)
