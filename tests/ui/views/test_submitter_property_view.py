"""Tests de la vue des soumetteurs."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.i18n import Translator
from ui.views.submitter_property_view import SubmitterPropertyView


class TestSubmitterPropertyView(unittest.TestCase):
    """Vérifie les coordonnées et champs additionnels d'un soumetteur."""

    def setUp(self):
        """Crée une fenêtre racine et une vue de soumetteur."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.view = SubmitterPropertyView(self.root, Mock(), self.translator)

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie display renders details contacts and additional fields.
    def test_display_renders_details_contacts_and_additional_fields(self):
        # Given un soumetteur complet
        submitter = SimpleNamespace(
            pointer="@M1@",
            name="John /Doe/",
            address="Adresse",
            address_line_1="Ligne 1",
            address_line_2="Ligne 2",
            city="Paris",
            state="IDF",
            postal_code="75001",
            country="France",
            registered_number="123",
            record_id="ID",
            restriction="privacy",
            change_date="1 JAN 2020",
            change_time="12:00",
            phone="010",
            phones=["020"],
            email="a@b",
            faxes=["fax"],
            website="web",
            language="fr",
            additional_fields=[{"tag": "NOTE", "value": "Note", "details": []}],
        )

        # When on affiche le soumetteur
        self.view.display(submitter)

        # Then les sections attendues sont présentes
        for key in (
            "view.submitter_details",
            "view.contact_information",
            "view.additional_fields",
        ):
            self.assertIn(self.translator.get(key), self.view.sections)
        self.assertEqual(self.view.title_label.cget("text"), "John /Doe/")

    # Vérifie display none clears previous content.
    def test_display_none_clears_previous_content(self):
        # Given une vue déjà remplie
        self.view.display(SimpleNamespace(pointer="@M1@", name="John"))

        # When on affiche None
        self.view.display(None)

        # Then la vue est vidée et le titre par défaut est restauré
        self.assertEqual(self.view.sections, {})
        self.assertEqual(
            self.view.title_label.cget("text"),
            self.translator.get("view.submitter"),
        )


if __name__ == "__main__":
    unittest.main()
