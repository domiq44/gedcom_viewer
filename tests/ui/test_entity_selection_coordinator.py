"""Tests du coordinateur de sélection d'entité."""

import tkinter as tk
import unittest
from unittest.mock import Mock

from ui.entity_selection_coordinator import EntitySelectionCoordinator


class TestEntitySelectionCoordinator(unittest.TestCase):
    """Vérifie la synchronisation du type, de la liste et de la sélection."""

    def setUp(self):
        """Crée une fenêtre racine et un coordinateur avec des dépendances simulées."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.entity_type_var = tk.StringVar(value="INDI")
        self.panel = Mock()
        self.browser = Mock()
        self.browser.entity_tree.get_children.return_value = ["I1"]
        self.browser.search_var.get.return_value = ""
        self.browser.select_entity.return_value = False
        self.view_manager = Mock()
        self.coordinator = EntitySelectionCoordinator(
            self.entity_type_var,
            self.panel,
            self.browser,
            self.view_manager,
        )

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie entity type change selects first item.
    def test_entity_type_change_selects_first_item(self):
        # Given un coordinateur initialisé
        # When on change de type
        self.coordinator.on_entity_type_change()

        # Then la liste est rechargée et le premier élément sélectionné
        self.panel.update_selection.assert_called_once_with("INDI")
        self.view_manager.clear.assert_called_once_with(keep_type="INDI")
        self.browser.list_entities.assert_called_once()
        self.browser.entity_tree.selection_set.assert_called_once_with("I1")
        self.browser.entity_tree.focus.assert_called_once_with("I1")

    # Vérifie entity type change restores remembered selection.
    def test_entity_type_change_restores_remembered_selection(self):
        # Given une sélection mémorisée pour INDI
        entity = Mock()
        self.coordinator.remember_selection("INDI", entity)
        self.browser.select_entity.return_value = True

        # When on change de type
        self.coordinator.on_entity_type_change()

        # Then l'entité mémorisée est resélectionnée
        self.browser.select_entity.assert_called_once_with(entity)
        self.browser.entity_tree.selection_set.assert_not_called()

    # Vérifie synchronize to context selects entity once.
    def test_synchronize_to_context_selects_entity_once(self):
        # Given un contexte de type individuel et une entité connue
        entity = Mock()
        context = {"type": "individual", "entity": entity}
        self.entity_type_var.set("FAM")
        self.browser.controller.get_entity_types.return_value = ["INDI"]
        self.browser.contains_entity.return_value = False
        self.browser.select_entity.return_value = True

        # When on synchronise la sélection
        self.coordinator.synchronize_to_context(context, {"individual": "INDI"})

        # Then le type et la sélection suivent le contexte, une seule fois
        self.assertEqual(self.entity_type_var.get(), "INDI")
        self.browser.select_entity.assert_called_once_with(entity)
        self.assertTrue(self.coordinator.should_ignore_selection(entity))
        self.assertFalse(self.coordinator.should_ignore_selection(entity))

    # Vérifie snapshot and restore selection memory.
    def test_snapshot_and_restore_selection_memory(self):
        # Given une sélection mémorisée et un type ignoré
        entity = Mock()
        self.coordinator.remember_selection("INDI", entity)
        self.coordinator._selection_to_ignore = entity
        snapshot = self.coordinator.snapshot_selection_memory()

        # When on modifie puis restaure l'état
        self.coordinator.clear_selection_memory()
        self.coordinator.restore_selection_memory(snapshot)

        # Then la sélection et l'ignorance sont restaurées
        self.assertTrue(self.coordinator.should_ignore_selection(entity))
        self.assertFalse(self.coordinator.should_ignore_selection(entity))

    # Vérifie set entity type without refresh does not refresh list.
    def test_set_entity_type_without_refresh_does_not_refresh_list(self):
        # Given un coordinateur initialisé
        # When on définit le type sans rafraîchissement
        self.coordinator.set_entity_type_without_refresh("FAM")

        # Then le type est changé mais la liste n'est pas rechargée
        self.assertEqual(self.entity_type_var.get(), "FAM")
        self.browser.list_entities.assert_not_called()

    # Vérifie synchronize to context returns without loaded controller.
    def test_synchronize_to_context_returns_without_loaded_controller(self):
        # Given un contexte valide mais aucun contrôleur chargé
        context = {"type": "individual", "entity": Mock()}
        self.browser.controller.is_loaded.return_value = False

        # When on synchronise la sélection
        self.coordinator.synchronize_to_context(context, {"individual": "INDI"})

        # Then aucun type n'est interrogé
        self.browser.controller.get_entity_types.assert_not_called()
        self.browser.select_entity.assert_not_called()

    # Vérifie synchronize to context ignores unknown type.
    def test_synchronize_to_context_ignores_unknown_type(self):
        # Given un contexte dont le type est inconnu
        context = {"type": "unknown", "entity": Mock()}

        # When on synchronise la sélection
        self.coordinator.synchronize_to_context(context, {})

        # Then aucune sélection n'a lieu
        self.entity_type_var.set("FAM")
        self.browser.select_entity.assert_not_called()

    # Vérifie get selection pointers retourne les pointeurs des entités mémorisées.
    def test_get_selection_pointers_returns_entity_pointers(self):
        # Given deux entités mémorisées avec un pointeur et une sans
        indi = Mock(pointer="@I1@")
        fam = Mock(pointer="@F2@")
        note = Mock(pointer=None)
        self.coordinator.remember_selection("INDI", indi)
        self.coordinator.remember_selection("FAM", fam)
        self.coordinator.remember_selection("NOTE", note)

        # When on récupère les pointeurs
        pointers = self.coordinator.get_selection_pointers()

        # Then seules les entités ayant un pointeur sont retournées
        self.assertEqual(pointers, {"INDI": "@I1@", "FAM": "@F2@"})

    # Vérifie load selection pointers restaure les entités résolues.
    def test_load_selection_pointers_restores_entities(self):
        # Given un résolveur qui retourne une entité par pointeur
        resolved = Mock()
        self.browser.controller.get_entity.side_effect = lambda p: (
            resolved if p == "@I1@" else None
        )

        # When on charge des pointeurs dont l'un ne se résout pas
        self.coordinator.load_selection_pointers(
            {"INDI": "@I1@", "FAM": "@F2@"}, self.browser.controller.get_entity
        )

        # Then seule l'entité résolue est mémorisée
        self.assertEqual(self.coordinator._last_selected_entities, {"INDI": resolved})

    # Vérifie load selection pointers réinitialise la mémoire.
    def test_load_selection_pointers_resets_memory(self):
        # Given une sélection existante
        self.coordinator.remember_selection("INDI", Mock())
        self.browser.controller.get_entity.return_value = Mock()

        # When on recharge des pointeurs
        self.coordinator.load_selection_pointers(
            {"FAM": "@F2@"}, self.browser.controller.get_entity
        )

        # Then l'ancienne sélection est remplacée
        self.assertEqual(set(self.coordinator._last_selected_entities), {"FAM"})


if __name__ == "__main__":
    unittest.main()
