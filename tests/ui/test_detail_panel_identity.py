"""Tests de l'en-tête d'identité du panneau de détail."""

import tkinter as tk
import unittest

from ui.detail_panel import DetailPanel
from ui.i18n import Translator
from ui.themes import COLORS, set_theme


class _Entity:
    """Entité minimale portant un pointeur."""

    def __init__(self, pointer="@I1@"):
        """Mémorise le pointeur de l'entité."""
        self.pointer = pointer


class _Controller:
    """Contrôleur factice exposant un résumé d'entité."""

    def __init__(self, summary):
        """Mémorise le résumé renvoyé par le contrôleur."""
        self._summary = summary

    def format_entity_summary(self, entity_type, entity):
        """Retourne le résumé mémorisé."""
        return self._summary


class TestDetailPanelIdentity(unittest.TestCase):
    """Vérifie le rendu de l'en-tête d'identité du panneau de détail."""

    def setUp(self):
        """Crée une fenêtre racine et un panneau de détail sans contrôleur."""
        self.root = tk.Tk()
        self.root.withdraw()
        set_theme("light")
        self.panel = DetailPanel(self.root, Translator("fr"))

    def tearDown(self):
        """Rétablit le thème clair et détruit la fenêtre racine."""
        set_theme("light")
        self.root.destroy()

    # Vérifie le titre et le sous-titre proviennent du contrôleur.
    def test_set_context_renders_title_and_subtitle(self):
        # Given un contrôleur renvoyant un résumé d'individu
        controller = _Controller(
            {"title": "John /Doe/", "subtitle": "1900 – 1980", "facts": []}
        )
        self.panel.controller_provider = lambda: controller

        # When on affiche la fiche d'un individu
        self.panel.set_context("INDI", _Entity())

        # Then le titre et le sous-titre de l'en-tête sont renseignés
        self.assertEqual(self.panel.identity_title.cget("text"), "John /Doe/")
        self.assertEqual(self.panel.identity_subtitle.cget("text"), "1900 – 1980")

    # Vérifie les faits du résumé sont rendus en couples libellé/valeur.
    def test_set_context_renders_facts(self):
        # Given un contrôleur renvoyant deux faits
        controller = _Controller(
            {
                "title": "John /Doe/",
                "subtitle": "",
                "facts": [("Date de naissance", "1900"), ("Lieu", "Paris")],
            }
        )
        self.panel.controller_provider = lambda: controller

        # When on affiche la fiche d'un individu
        self.panel.set_context("INDI", _Entity())

        # Then deux widgets de fait sont créés
        self.assertEqual(len(self.panel.identity_facts.winfo_children()), 4)

    # Vérifie les faits précédents sont détruits lors d'un nouvel affichage.
    def test_set_context_replaces_previous_facts(self):
        # Given un en-tête déjà alimenté par deux faits
        controller = _Controller(
            {
                "title": "John /Doe/",
                "subtitle": "",
                "facts": [("Lieu", "Paris"), ("Métier", "Boulanger")],
            }
        )
        self.panel.controller_provider = lambda: controller
        self.panel.set_context("INDI", _Entity())

        # When on affiche une fiche sans fait
        empty = _Controller({"title": "Jane", "subtitle": "", "facts": []})
        self.panel.controller_provider = lambda: empty
        self.panel.set_context("INDI", _Entity("@I2@"))

        # Then les anciens widgets de faits sont détruits
        self.assertEqual(self.panel.identity_facts.winfo_children(), [])

    # Vérifie le titre retombe sur le type et le pointeur sans contrôleur.
    def test_set_context_falls_back_to_pointer_without_controller(self):
        # Given un panneau sans contrôleur
        # When on affiche la fiche d'un individu
        self.panel.set_context("INDI", _Entity("@I1@"))

        # Then le titre combine le type et le pointeur
        self.assertEqual(self.panel.identity_title.cget("text"), "INDI · @I1@")

    # Vérifie l'en-tête signale l'absence de sélection.
    def test_set_context_shows_no_selection_for_missing_entity(self):
        # Given un panneau sans contrôleur
        # When on affiche un type sans entité
        self.panel.set_context("INDI", None)

        # Then l'en-tête indique l'absence de sélection
        self.assertEqual(self.panel.identity_title.cget("text"), "Aucune sélection")

    # Vérifie le titre et le sous-titre suivent le thème courant.
    def test_apply_theme_recolors_header(self):
        # Given un en-tête affiché sous le thème clair
        self.panel.set_context("INDI", _Entity())

        # When on bascule vers le thème sombre et on réapplique le thème
        set_theme("dark")
        self.panel.apply_theme()

        # Then les couleurs de l'en-tête suivent le thème sombre
        self.assertEqual(self.panel.identity_title.cget("fg"), COLORS["text"])
        self.assertEqual(self.panel.identity_subtitle.cget("fg"), COLORS["muted_text"])

    # Vérifie les widgets de faits suivent le thème courant.
    def test_apply_theme_recolors_fact_widgets(self):
        # Given un en-tête avec un fait affiché
        controller = _Controller(
            {"title": "John /Doe/", "subtitle": "", "facts": [("Lieu", "Paris")]}
        )
        self.panel.controller_provider = lambda: controller
        self.panel.set_context("INDI", _Entity())

        # When on réapplique le thème
        self.panel.apply_theme()

        # Then le libellé et la valeur utilisent les couleurs du thème
        label_widget, value_widget = self.panel.identity_facts.winfo_children()
        self.assertEqual(label_widget.cget("fg"), COLORS["muted_text"])
        self.assertEqual(value_widget.cget("fg"), COLORS["text"])


if __name__ == "__main__":
    unittest.main()
