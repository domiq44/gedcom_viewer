"""Tests du registre de re-thème."""

import gc
import unittest
import weakref
from unittest.mock import Mock

from ui.theme_aware import ThemeAware, ThemeRegistry


class _Dummy:
    """Composant de test exposant apply_theme."""

    def __init__(self):
        """Initialise un espion de re-thème."""
        self.apply_theme = Mock()


class TestThemeRegistry(unittest.TestCase):
    """Vérifie l'enregistrement et l'application du thème."""

    # Vérifie register and apply theme.
    def test_register_and_apply_theme(self):
        # Given deux composants enregistrés
        registry = ThemeRegistry()
        first = _Dummy()
        second = _Dummy()
        registry.register(first)
        registry.register(second)

        # When on applique le thème
        registry.apply_theme()

        # Then chaque composant est re-thémé
        first.apply_theme.assert_called_once()
        second.apply_theme.assert_called_once()

    # Vérifie apply theme ignores components without method.
    def test_apply_theme_ignores_components_without_method(self):
        # Given un registre et un objet sans apply_theme
        registry = ThemeRegistry()

        # When on enregistre et applique le thème
        registry.register(object())
        registry.apply_theme()

        # Then aucune erreur n'est levée
        self.assertEqual(len(list(registry._components)), 0)

    # Vérifie apply theme continues after component error.
    def test_apply_theme_continues_after_component_error(self):
        # Given deux composants dont le premier échoue
        registry = ThemeRegistry()
        failing = _Dummy()
        failing.apply_theme.side_effect = RuntimeError("boom")
        healthy = _Dummy()
        registry.register(failing)
        registry.register(healthy)

        # When on applique le thème
        with self.assertLogs("ui.theme_aware", level="ERROR") as logs:
            registry.apply_theme()

        # Then le second composant est tout de même re-thémé
        healthy.apply_theme.assert_called_once()
        self.assertIn("Échec de l'application du thème", "\n".join(logs.output))

    # Vérifie theme aware protocol matches apply theme.
    def test_theme_aware_protocol_matches_apply_theme(self):
        # Given un composant avec apply_theme et un objet sans
        # When on vérifie le protocole
        # Then seul le premier est reconnu
        self.assertIsInstance(_Dummy(), ThemeAware)
        self.assertNotIsInstance(object(), ThemeAware)

    # Vérifie register is idempotent.
    def test_register_is_idempotent(self):
        # Given un composant enregistré deux fois
        registry = ThemeRegistry()
        component = _Dummy()
        registry.register(component)
        registry.register(component)

        # When on applique le thème
        registry.apply_theme()

        # Then le composant n'est re-thémé qu'une fois
        component.apply_theme.assert_called_once()

    # Vérifie registry drops destroyed components.
    def test_registry_drops_destroyed_components(self):
        # Given un composant enregistré puis supprimé
        registry = ThemeRegistry()
        component = _Dummy()
        registry.register(component)
        reference = weakref.ref(component)
        del component
        gc.collect()

        # When on applique le thème
        # Then le composant détruit est ignoré
        self.assertIsNone(reference())
        registry.apply_theme()
        self.assertEqual(len(list(registry._components)), 0)


if __name__ == "__main__":
    unittest.main()
