"""Tests des actions d'affichage d'entités de la fenêtre principale."""

import unittest
from unittest.mock import Mock

from ui.entity_display import EntityDisplayMixin


class _EntityDisplayHost(EntityDisplayMixin):
    """Hôte minimal exposant les dépendances de l'affichage d'entités."""

    def __init__(self):
        """Initialise les dépendances simulées."""
        self.root = Mock()
        self.translator = Mock()
        self.controller = Mock()
        self.entity_navigator = Mock()
        self.entity_view_manager = Mock()
        self.entity_selection_coordinator = Mock()
        self.entity_browser = Mock()
        self.entity_browser.entity_tree.selection.return_value = []
        self.entity_type_tabs = Mock()
        self.entity_type_var = Mock()
        self.entity_type_var.get.return_value = "INDI"
        self.nav_toolbar = Mock()
        self.menu_bar = Mock()
        self.detail_panel = Mock()
        self.highlighter = Mock()
        self._navigation_history = Mock()
        self._entity_selection_after_id = None
        self._current_entity_type = None
        self._current_entity = None
        self.DISPLAY_TYPE_MAP = {}
        self._show_entity_view = Mock()
        self._clear_entity_views = Mock()
        self._display_raw_text = Mock()
        self._record_navigation = Mock()


class TestEntityDisplayMixin(unittest.TestCase):
    """Vérifie les actions d'affichage de la fenêtre principale."""

    def setUp(self):
        """Crée un hôte d'affichage d'entités."""
        self.host = _EntityDisplayHost()

    # Vérifie clear search delegates.
    def test_clear_search_delegates(self):
        # Given un navigateur d'entités
        # When on efface la recherche
        self.host.clear_search()

        # Then l'effacement est délégué
        self.host.entity_browser.clear_search.assert_called_once()

    # Vérifie show selected entity returns without selection.
    def test_show_selected_entity_returns_without_selection(self):
        # Given aucune sélection
        # When on affiche l'entité sélectionnée
        self.host._show_selected_entity()

        # Then aucune résolution n'a lieu
        self.host.entity_browser.get_entity.assert_not_called()

    # Vérifie show selected entity returns when controller not loaded.
    def test_show_selected_entity_returns_when_controller_not_loaded(self):
        # Given une sélection mais aucun fichier chargé
        self.host.entity_browser.entity_tree.selection.return_value = ["@I1@"]
        self.host.controller.is_loaded.return_value = False

        # When on affiche l'entité sélectionnée
        self.host._show_selected_entity()

        # Then aucune entité n'est résolue
        self.host.entity_browser.get_entity.assert_not_called()

    # Vérifie show selected entity handles empty item.
    def test_show_selected_entity_handles_empty_item(self):
        # Given une sélection vide
        self.host.entity_browser.entity_tree.selection.return_value = ["empty"]
        self.host.controller.is_loaded.return_value = True

        # When on affiche l'entité sélectionnée
        self.host._show_selected_entity()

        # Then la vue est vidée
        self.host._show_entity_view.assert_called_once_with("INDI", None)
        self.host._display_raw_text.assert_called_once_with("")

    # Vérifie show selected entity uses controller context for citation.
    def test_show_selected_entity_uses_controller_context_for_citation(self):
        # Given une citation sélectionnée
        citation = Mock()
        context = {
            "type": "citation",
            "entity": citation,
            "raw_entity": citation,
            "raw_block": "2 SOUR @S1@\n",
        }
        self.host.entity_type_var.get.return_value = "CITE"
        self.host.entity_browser.entity_tree.selection.return_value = ["0"]
        self.host.controller.is_loaded.return_value = True
        self.host.entity_browser.get_entity.return_value = citation
        self.host.controller.get_entity_display_info.return_value = context
        self.host.entity_selection_coordinator.should_ignore_selection.return_value = (
            False
        )
        self.host.display_entity_context = Mock()

        # When on affiche l'entité sélectionnée
        self.host._show_selected_entity()

        # Then le contexte de présentation est délégué au contrôleur
        self.host.controller.get_entity_display_info.assert_called_once_with(citation)
        self.host.display_entity_context.assert_called_once_with(context)

    # Vérifie show selected entity returns when entity missing.
    def test_show_selected_entity_returns_when_entity_missing(self):
        # Given une sélection sans entité résolue
        self.host.entity_browser.entity_tree.selection.return_value = ["@I1@"]
        self.host.controller.is_loaded.return_value = True
        self.host.entity_browser.get_entity.return_value = None

        # When on affiche l'entité sélectionnée
        self.host._show_selected_entity()

        # Then aucune sélection n'est mémorisée
        self.host.entity_selection_coordinator.remember_selection.assert_not_called()

    # Vérifie show header returns when not loaded.
    def test_show_header_returns_when_not_loaded(self):
        # Given aucun fichier chargé
        self.host.controller.is_loaded.return_value = False

        # When on affiche l'en-tête
        self.host.show_header()

        # Then aucun bloc n'est extrait
        self.host.controller.extract_head.assert_not_called()

    # Vérifie show trailer returns when not loaded.
    def test_show_trailer_returns_when_not_loaded(self):
        # Given aucun fichier chargé
        self.host.controller.is_loaded.return_value = False

        # When on affiche le trailer
        self.host.show_trailer()

        # Then aucun bloc n'est extrait
        self.host.controller.extract_trailer.assert_not_called()

    # Vérifie display entity context clears unknown type.
    def test_display_entity_context_clears_unknown_type(self):
        # Given un contexte de type inconnu
        context = {"type": "unknown", "entity": object()}

        # When on affiche le contexte
        self.host.display_entity_context(context)

        # Then les vues sont effacées
        self.host._clear_entity_views.assert_called_once()


if __name__ == "__main__":
    unittest.main()
