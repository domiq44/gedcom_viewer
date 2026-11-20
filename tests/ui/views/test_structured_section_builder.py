"""Tests du constructeur de sections des fiches structurées."""

import tkinter as tk
import unittest
from unittest.mock import Mock

from ui.views.structured_section_builder import StructuredSectionBuilder


class TestStructuredSectionBuilder(unittest.TestCase):
    """Vérifie la construction des sections et la copie de leur contenu."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.content = tk.Frame(self.root)
        self.translator = Mock()
        self.translator.get.return_value = "Copier"
        self.builder = StructuredSectionBuilder(
            self.content,
            self.translator,
            tooltip_factory_provider=lambda: None,
            bind_scroll=Mock(),
        )

    def tearDown(self):
        self.root.destroy()

    # Vérifie build registers section and copy button.
    def test_build_registers_section_and_copy_button(self):
        # Given (Arrange) un constructeur
        # When (Act) on construit une section
        section = self.builder.build("Détails")
        # Then (Assert) la section et son bouton de copie sont enregistrés
        self.assertIn("Détails", self.builder.sections)
        self.assertIn(section, self.builder.copy_buttons)
        self.assertEqual(self.builder.titles[section], "Détails")
        self.assertEqual(self.builder.rows[section], [])

    # Vérifie copy appends title and rows to clipboard.
    def test_copy_appends_title_and_rows_to_clipboard(self):
        # Given (Arrange) une section avec deux lignes
        section = self.builder.build("Détails")
        self.builder.rows[section].extend([("NAME", "John"), ("", "texte")])
        # When (Act) on copie la section
        result = self.builder.copy(section)
        # Then (Assert) le presse-papiers contient le titre et les lignes
        self.root.update()
        self.assertTrue(result)
        self.assertEqual(self.root.clipboard_get(), "Détails\nNAME: John\ntexte")

    # Vérifie reset clears registries.
    def test_reset_clears_registries(self):
        # Given (Arrange) une section construite
        self.builder.build("Détails")
        # When (Act) on réinitialise le constructeur
        self.builder.reset()
        # Then (Assert) les registres sont vides
        self.assertEqual(self.builder.sections, {})
        self.assertEqual(self.builder.copy_buttons, {})
        self.assertEqual(self.builder.titles, {})
        self.assertEqual(self.builder.rows, {})
