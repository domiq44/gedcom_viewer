"""Tests de l'ouverture du navigateur au clic sur une URL."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ui.views import link_utils


class TestOpenUrlAtClick(unittest.TestCase):
    """Vérifie l'ouverture du navigateur au clic sur une URL."""

    def setUp(self):
        self.root = tk.Tk()
        self.text = tk.Text(self.root)
        self.text.pack()
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    # Vérifie click on url opens browser.
    def test_click_on_url_opens_browser(self):
        # Given (Arrange) un widget avec une URL et un clic positionné dessus
        self.text.insert("1.0", "Visit https://example.com now")
        bbox = self.text.bbox("1.0 + 7 chars")
        event = SimpleNamespace(widget=self.text, x=bbox[0] + 1, y=bbox[1] + 1)
        # When (Act) on simule le clic
        with patch("ui.views.link_utils.webbrowser.open") as open_mock:
            link_utils._open_url_at_click(event)
        # Then (Assert) le navigateur est ouvert avec l'URL
        open_mock.assert_called_once_with("https://example.com")

    # Vérifie click outside url does nothing.
    def test_click_outside_url_does_nothing(self):
        # Given (Arrange) un widget avec une URL, clic hors de l'URL
        self.text.insert("1.0", "Visit https://example.com now")
        bbox = self.text.bbox("1.0 + 0 chars")
        event = SimpleNamespace(widget=self.text, x=bbox[0], y=bbox[1])
        # When (Act) on simule le clic hors URL
        with patch("ui.views.link_utils.webbrowser.open") as open_mock:
            link_utils._open_url_at_click(event)
        # Then (Assert) aucun navigateur n'est ouvert
        open_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
