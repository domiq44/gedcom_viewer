"""Tests de la vue des dépôts."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.i18n import Translator
from ui.views.repository_property_view import RepositoryPropertyView


class TestRepositoryPropertyView(unittest.TestCase):
    """Vérifie les sections d'identité, d'adresse et de contact."""

    def setUp(self):
        """Crée une fenêtre racine et une vue de dépôt."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.view = RepositoryPropertyView(self.root, Mock(), self.translator)

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie display renders details address and contacts.
    def test_display_renders_details_address_and_contacts(self):
        # Given un dépôt complet
        repository = SimpleNamespace(
            pointer="@R1@",
            name="Archives",
            record_id="ID",
            change_date="1 JAN 2020",
            change_time="12:00",
            address="Adresse",
            address_line_1="Ligne 1",
            address_line_2="Ligne 2",
            city="Paris",
            state="IDF",
            postal_code="75001",
            country="France",
            phone="010",
            phones=["020"],
            email="a@b",
            faxes=["fax"],
            websites=["web"],
            notes=["Note"],
            references=["@S1@"],
            additional_fields=[
                {"tag": "EVEN", "value": "", "details": [("TYPE", "Militaire")]}
            ],
        )

        # When on affiche le dépôt
        self.view.display(repository)

        # Then les sections attendues sont présentes
        for key in (
            "view.repository_details",
            "view.repository_address",
            "view.contact_information",
            "view.notes",
            "view.references",
            "view.additional_fields",
        ):
            self.assertIn(self.translator.get(key), self.view.sections)

    # Vérifie display none clears previous content.
    def test_display_none_clears_previous_content(self):
        # Given une vue déjà remplie
        self.view.display(SimpleNamespace(pointer="@R1@", name="Archives"))

        # When on affiche None
        self.view.display(None)

        # Then la vue est vidée et le titre par défaut est restauré
        self.assertEqual(self.view.sections, {})
        self.assertEqual(
            self.view.title_label.cget("text"),
            self.translator.get("view.repository"),
        )


if __name__ == "__main__":
    unittest.main()
