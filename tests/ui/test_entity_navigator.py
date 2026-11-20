"""Tests du navigateur d'entités."""

import unittest
from unittest.mock import Mock

from ui.entity_navigator import EntityNavigator


class TestEntityNavigator(unittest.TestCase):
    """Vérifie la navigation et les erreurs de résolution."""

    def _navigator(self, controller, history):
        """Construit un navigateur avec des callbacks simulés."""
        return EntityNavigator(
            controller=controller,
            history=history,
            on_display=Mock(),
            on_error=Mock(),
        )

    # Vérifie navigate to records and displays context.
    def test_navigate_to_records_and_displays_context(self):
        # Given un contrôleur chargé et une entité résoluble
        controller = Mock()
        controller.is_loaded.return_value = True
        controller.resolve_pointer.return_value = object()
        context = {"pointer": "@I1@"}
        controller.get_entity_display_info.return_value = context
        history = Mock()
        navigator = self._navigator(controller, history)

        # When on navigue vers un pointeur
        navigator.navigate_to("@I1@")

        # Then le contexte est enregistré puis affiché
        history.record.assert_called_once_with(context)
        navigator.on_display.assert_called_once_with(context)

    # Vérifie navigate to reports missing session.
    def test_navigate_to_reports_missing_session(self):
        # Given un contrôleur non chargé
        controller = Mock()
        controller.is_loaded.return_value = False
        navigator = self._navigator(controller, Mock())

        # When on navigue vers un pointeur
        navigator.navigate_to("@I1@")

        # Then une erreur de session est signalée
        navigator.on_error.assert_called_once_with("ui.error", "ui.no_session")

    # Vérifie navigate to reports unknown entity.
    def test_navigate_to_reports_unknown_entity(self):
        # Given un contrôleur chargé mais un pointeur inconnu
        controller = Mock()
        controller.is_loaded.return_value = True
        controller.resolve_pointer.return_value = None
        navigator = self._navigator(controller, Mock())

        # When on navigue vers un pointeur
        navigator.navigate_to("@I9@")

        # Then une erreur d'entité introuvable est signalée
        navigator.on_error.assert_called_once_with(
            "ui.error", "ui.entity_not_found", pointer="@I9@"
        )

    # Vérifie go back displays previous context.
    def test_go_back_displays_previous_context(self):
        # Given un historique avec un contexte précédent
        history = Mock()
        history.back.return_value = {"pointer": "@I1@"}
        navigator = self._navigator(Mock(), history)

        # When on revient en arrière
        navigator.go_back()

        # Then le contexte précédent est affiché
        navigator.on_display.assert_called_once_with({"pointer": "@I1@"})

    # Vérifie go forward ignores empty history.
    def test_go_forward_ignores_empty_history(self):
        # Given un historique sans contexte suivant
        history = Mock()
        history.forward.return_value = None
        navigator = self._navigator(Mock(), history)

        # When on avance
        navigator.go_forward()

        # Then aucun affichage n'a lieu
        navigator.on_display.assert_not_called()


if __name__ == "__main__":
    unittest.main()
