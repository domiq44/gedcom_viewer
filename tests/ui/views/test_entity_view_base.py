"""Tests du protocole de formatage des détails de la vue d'entité."""

import tkinter as tk
import unittest
from types import SimpleNamespace

from ui.views.entity_view_base import EntityViewBase


class TestEntityViewDetailsFormatter(unittest.TestCase):
    """Vérifie le résolveur de formatage des détails de ``EntityViewBase``."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.view = EntityViewBase(self.root, on_pointer_click=lambda pointer: None)
        self.details = [
            {"tag": "NOTE", "value": "Texte"},
            {"tag": "CONT", "value": " suite"},
        ]

    def tearDown(self):
        self.root.destroy()

    # Vérifie returns details unchanged without resolver.
    def test_returns_details_unchanged_without_resolver(self):
        # Given une vue sans résolveur de formatage
        # When on formate les détails
        with self.assertLogs("ui.views.entity_view_base", level="WARNING"):
            formatted = self.view._format_details(self.details)
        # Then les détails sont restitués inchangés
        self.assertEqual(formatted, self.details)

    # Vérifie applies injected formatter.
    def test_applies_injected_formatter(self):
        # Given un résolveur de formatage injecté
        self.view.set_details_formatter_resolver(
            lambda details: [{"tag": "NOTE", "value": "fusionné"}]
        )
        # When on formate les détails
        formatted = self.view._format_details(self.details)
        # Then le résultat du résolveur est utilisé
        self.assertEqual(formatted, [{"tag": "NOTE", "value": "fusionné"}])

    # Vérifie falls back when formatter returns non list.
    def test_falls_back_when_formatter_returns_non_list(self):
        # Given un résolveur qui ne renvoie pas une liste
        self.view.set_details_formatter_resolver(lambda details: None)
        # When on formate les détails
        formatted = self.view._format_details(self.details)
        # Then les détails d'origine sont conservés
        self.assertEqual(formatted, self.details)

    # Vérifie logs and falls back when formatter raises.
    def test_logs_and_falls_back_when_formatter_raises(self):
        # Given un résolveur qui lève une exception
        def failing_formatter(details):
            """Simule un résolveur défaillant."""
            raise RuntimeError("échec de formatage")

        self.view.set_details_formatter_resolver(failing_formatter)
        # When on formate les détails
        with self.assertLogs("ui.views.entity_view_base", level="ERROR"):
            formatted = self.view._format_details(self.details)
        # Then les détails d'origine sont conservés
        self.assertEqual(formatted, self.details)

    # Vérifie pointer resolver exception returns none.
    def test_pointer_resolver_exception_returns_none(self):
        # Given un résolveur générique qui échoue
        def failing_resolver(pointer):
            """Simule un résolveur défaillant."""
            raise RuntimeError("boom")

        self.view.set_pointer_resolver(failing_resolver)

        # When on résout un pointeur
        with self.assertLogs("ui.views.entity_view_base", level="ERROR"):
            target, entity_type = self.view._resolve_pointer_target("@I1@")

        # Then aucune cible n'est retournée
        self.assertIsNone(target)
        self.assertIsNone(entity_type)

    # Vérifie type resolver exception falls through to next resolver.
    def test_type_resolver_exception_falls_through_to_next_resolver(self):
        # Given un résolveur INDI défaillant et un résolveur FAM valide
        def failing_resolver(pointer):
            """Simule un résolveur INDI défaillant."""
            raise RuntimeError("boom")

        target = SimpleNamespace(tag="FAM")
        self.view.set_name_resolver(failing_resolver)
        self.view.set_family_name_resolver(lambda pointer: target)

        # When on résout un pointeur
        with self.assertLogs("ui.views.entity_view_base", level="ERROR"):
            resolved, entity_type = self.view._resolve_pointer_target("@F1@")

        # Then le résolveur suivant est utilisé
        self.assertIs(resolved, target)
        self.assertEqual(entity_type, "FAM")

    # Vérifie display pointer uses title when no formatter.
    def test_display_pointer_uses_title_when_no_formatter(self):
        # Given une cible avec un titre et aucun résolveur de libellé
        target = SimpleNamespace(title="Source Title")
        self.view.set_pointer_resolver(lambda pointer: target)

        # When on affiche le pointeur
        label = self.view._display_pointer("@S1@")

        # Then le titre est utilisé comme libellé
        self.assertEqual(label, "Source Title (@S1@)")

    # Vérifie display pointer logs and falls back when formatter raises.
    def test_display_pointer_logs_and_falls_back_when_formatter_raises(self):
        # Given un résolveur de libellé qui échoue
        target = SimpleNamespace(title="Source Title")
        self.view.set_pointer_resolver(lambda pointer: target)
        self.view.set_display_name_resolver(
            lambda entity, entity_type: (_ for _ in ()).throw(RuntimeError("boom"))
        )

        # When on affiche le pointeur
        with self.assertLogs("ui.views.entity_view_base", level="ERROR"):
            label = self.view._display_pointer("@S1@")

        # Then le pointeur brut est retourné
        self.assertEqual(label, "@S1@")

    # Vérifie set source resolver stores resolver.
    def test_set_source_resolver_stores_resolver(self):
        # Given un résolveur de source
        def resolver(pointer):
            """Retourne aucune source."""
            return None

        # When on l'injecte
        self.view.set_source_resolver(resolver)

        # Then il est conservé
        self.assertIs(self.view.source_resolver, resolver)
