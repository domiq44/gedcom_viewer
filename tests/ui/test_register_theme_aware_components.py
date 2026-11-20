"""Tests de l'enregistrement groupé des composants d'un hôte."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.theme_aware import register_theme_aware_components


class TestRegisterThemeAwareComponents(unittest.TestCase):
    """Vérifie l'enregistrement groupé des composants d'un hôte."""

    # Vérifie les composants connus et les vues sont enregistrés.
    def test_registers_known_components_and_views(self):
        # Given un hôte avec des composants et deux vues de détail
        header = Mock()
        detail_panel = Mock()
        first_view = Mock()
        second_view = Mock()
        host = SimpleNamespace(
            theme_registry=Mock(),
            app_header=header,
            detail_panel=detail_panel,
            entity_view_manager=SimpleNamespace(
                views={"individual": first_view, "family": second_view}
            ),
        )

        # When on enregistre les composants thémables
        register_theme_aware_components(host)

        # Then chaque composant et chaque vue est enregistré
        registered = {
            call.args[0] for call in host.theme_registry.register.call_args_list
        }
        self.assertEqual(registered, {header, detail_panel, first_view, second_view})

    # Vérifie les composants absents sont ignorés.
    def test_ignores_missing_components(self):
        # Given un hôte sans composant thémable
        host = SimpleNamespace(theme_registry=Mock())

        # When on enregistre les composants thémables
        register_theme_aware_components(host)

        # Then aucun composant n'est enregistré
        host.theme_registry.register.assert_not_called()


if __name__ == "__main__":
    unittest.main()
