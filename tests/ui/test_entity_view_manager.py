"""Tests du gestionnaire de vues par entité."""

import unittest
from unittest.mock import Mock

from ui.entity_view_manager import EntityViewManager


class TestEntityViewManager(unittest.TestCase):
    """Vérifie le catalogue de vues et leur affichage."""

    # Vérifie view specs cover every entity type.
    def test_view_specs_cover_every_entity_type(self):
        # Given le catalogue des vues
        manager = EntityViewManager()

        # When on lit les spécifications
        # Then chaque type d'entité possède une vue dédiée
        entity_types = [entity_type for _name, entity_type, _view in manager.VIEW_SPECS]
        self.assertEqual(
            set(entity_types),
            {"INDI", "FAM", "SOUR", "REPO", "NOTE", "OBJE", "SUBM", "CITE"},
        )

    # Vérifie clear keeps only requested type.
    def test_clear_keeps_only_requested_type(self):
        # Given un gestionnaire avec deux vues simulées
        manager = EntityViewManager()
        kept_view, kept_tab = Mock(), Mock()
        hidden_view, hidden_tab = Mock(), Mock()
        manager.entity_view_map = {
            "INDI": (kept_view, kept_tab),
            "FAM": (hidden_view, hidden_tab),
        }

        # When on efface tout sauf INDI
        manager.clear(keep_type="INDI")

        # Then seul l'onglet INDI reste affiché et les vues cachées ne sont pas vidées
        kept_tab.pack.assert_called_once()
        hidden_tab.pack_forget.assert_called_once()
        hidden_view.display.assert_not_called()
        kept_view.display.assert_not_called()
        self.assertEqual(manager._visible_type, "INDI")

    # Vérifie show displays requested view and hides others.
    def test_show_displays_requested_view_and_hides_others(self):
        # Given un gestionnaire avec deux vues simulées
        manager = EntityViewManager()
        shown_view, shown_tab = Mock(), Mock()
        hidden_view, hidden_tab = Mock(), Mock()
        manager.entity_view_map = {
            "INDI": (shown_view, shown_tab),
            "FAM": (hidden_view, hidden_tab),
        }
        entity = Mock(pointer="@I1@")

        # When on affiche une entité INDI
        manager.show("INDI", entity)

        # Then la vue INDI reçoit l'entité et les autres vues sont seulement masquées
        shown_tab.pack.assert_called_once()
        shown_view.display.assert_called_once_with(entity)
        hidden_tab.pack_forget.assert_called_once()
        hidden_view.display.assert_not_called()
        self.assertEqual(manager._visible_type, "INDI")

    # Vérifie show ignores entity without pointer.
    def test_show_ignores_entity_without_pointer(self):
        # Given un gestionnaire avec une vue simulée
        manager = EntityViewManager()
        view, tab = Mock(), Mock()
        manager.entity_view_map = {"INDI": (view, tab)}

        # When on affiche une entité sans pointeur
        manager.show("INDI", Mock(pointer=None))

        # Then la vue est vidée
        view.display.assert_called_once_with(None)


if __name__ == "__main__":
    unittest.main()
