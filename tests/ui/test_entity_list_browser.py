"""Tests du navigateur de liste d'entités : remplissage, repérage et filtrage."""

import gc
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ui.entity_list_browser import EntityListBrowser
from ui.i18n import Translator


class FakeController:
    """Contrôleur minimal pour tester l'explorateur d'entités isolément."""

    def __init__(self, loaded=True, types=("INDI",), items=None):
        self._loaded = loaded
        self._types = list(types)
        self._items = items or {}

    def is_loaded(self):
        return self._loaded

    def get_entity_types(self):
        return list(self._types)

    def get_entity_list_items(self, entity_type, query=""):
        return self._items.get(entity_type, [])

    def format_entity_display_name(self, entity, entity_type):
        return getattr(entity, "name", "")

    def get_entity_sort_key(self, entity, entity_type, column):
        if column == "pointer":
            return getattr(entity, "pointer", "")
        return getattr(entity, "name", "")


class TestEntityListBrowser(unittest.TestCase):
    """Vérifie le remplissage de la liste, le repérage d'items et l'application du filtre."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.parent = tk.Frame(self.root)
        self.translator = Translator()
        self.entity_type_var = tk.StringVar(value="INDI")
        self.on_empty = Mock()
        self.individuals = [
            SimpleNamespace(name="Alice", pointer="@I1@"),
            SimpleNamespace(name="Bob", pointer="@I2@"),
        ]
        self.controller = FakeController(
            items={"INDI": [(entity, None) for entity in self.individuals]}
        )

    def tearDown(self):
        self.root.destroy()
        gc.collect()

    def _make_browser(self, controller=None):
        controller = controller or self.controller
        return EntityListBrowser(
            self.parent,
            self.translator,
            controller_provider=lambda: controller,
            entity_type_var=self.entity_type_var,
            on_select=lambda entity: None,
            on_empty=self.on_empty,
        )

    # Vérifie refresh populates tree.
    def test_refresh_populates_tree(self):
        # Given (Arrange) un explorateur avec deux individus
        browser = self._make_browser()
        # When (Act) on rafraîchit la liste
        browser.refresh_entities()
        # Then (Assert) deux lignes sont présentes dans l'arbre
        children = browser.entity_tree.get_children()
        self.assertEqual(len(children), 2)

    # Vérifie white box pointer index is built on refresh.
    def test_white_box_pointer_index_is_built_on_refresh(self):
        # Given (Arrange) un explorateur avec deux individus
        browser = self._make_browser()
        # When (Act) on rafraîchit la liste
        browser.refresh_entities()
        # Then (Assert) l'index pointeur→item contient chaque pointeur
        self.assertEqual(
            browser._item_id_by_pointer,
            {"@I1@": "0", "@I2@": "1"},
        )

    # Vérifie refresh shows empty for unknown type.
    def test_refresh_shows_empty_for_unknown_type(self):
        # Given (Arrange) un explorateur dont le type n'est pas chargé
        self.entity_type_var.set("FAM")
        browser = self._make_browser()
        # When (Act) on rafraîchit la liste
        browser.refresh_entities()
        # Then (Assert) une ligne vide est affichée et on_empty est appelé
        self.assertEqual(browser.entity_tree.get_children(), ("empty",))
        self.on_empty.assert_called_once_with("FAM")

    # Vérifie find entity item id by identity.
    def test_find_entity_item_id_by_identity(self):
        # Given (Arrange) un explorateur peuplé
        browser = self._make_browser()
        browser.refresh_entities()
        # When (Act) on cherche l'ID d'un individu par identité
        item_id = browser.find_entity_item_id(self.individuals[0])
        # Then (Assert) l'ID correspondant est renvoyé
        self.assertEqual(item_id, "0")

    # Vérifie find entity item id by pointer fallback.
    def test_find_entity_item_id_by_pointer_fallback(self):
        # Given (Arrange) un explorateur peuplé et un objet équivalent par pointeur
        browser = self._make_browser()
        browser.refresh_entities()
        equivalent = SimpleNamespace(name="Alice", pointer="@I1@")
        # When (Act) on cherche l'ID par pointeur
        item_id = browser.find_entity_item_id(equivalent)
        # Then (Assert) l'ID correspondant au pointeur est renvoyé
        self.assertEqual(item_id, "0")

    # Vérifie find entity item id returns none for cite.
    def test_find_entity_item_id_returns_none_for_cite(self):
        # Given (Arrange) un explorateur en mode citations
        self.entity_type_var.set("CITE")
        browser = self._make_browser()
        browser.refresh_entities()
        # When (Act) on cherche l'ID d'une entité
        item_id = browser.find_entity_item_id(self.individuals[0])
        # Then (Assert) aucun ID n'est renvoyé en mode CITE
        self.assertIsNone(item_id)

    # Vérifie find entity item id returns none without pointer.
    def test_find_entity_item_id_returns_none_without_pointer(self):
        # Given (Arrange) un explorateur peuplé et une entité sans pointeur
        browser = self._make_browser()
        browser.refresh_entities()
        anonymous = SimpleNamespace(name="Anon", pointer=None)
        # When (Act) on cherche l'ID de l'entité sans pointeur
        item_id = browser.find_entity_item_id(anonymous)
        # Then (Assert) aucun ID n'est renvoyé
        self.assertIsNone(item_id)

    # Vérifie sort entities reverses order.
    def test_sort_entities_reverses_order(self):
        # Given (Arrange) un explorateur peuplé trié par nom
        browser = self._make_browser()
        browser.refresh_entities()
        first_before = browser.entity_tree.item(
            browser.entity_tree.get_children()[0], "values"
        )
        # When (Act) on trie deux fois par le nom
        browser.sort_entities("name")
        first_asc = browser.entity_tree.item(
            browser.entity_tree.get_children()[0], "values"
        )
        browser.sort_entities("name")
        first_desc = browser.entity_tree.item(
            browser.entity_tree.get_children()[0], "values"
        )
        # Then (Assert) le second tri inverse l'ordre
        self.assertNotEqual(first_asc, first_desc)
        self.assertEqual(first_asc, first_before)

    # Vérifie async search publishes the filtered entities.
    def test_async_search_publishes_the_filtered_entities(self):
        # Given (Arrange) un explorateur chargé et les cycles Tcl déjà collectés
        browser = self._make_browser()
        gc.collect()
        # When (Act) on lance la recherche puis on publie le résultat
        browser._launch_search("Ali")
        browser._search_worker.join(timeout=2)
        browser._poll_search_result()
        # Then (Assert) l'arbre est peuplé
        self.assertEqual(len(browser.entity_tree.get_children()), 2)

    # Vérifie search filter is a no-op when unloaded.
    def test_search_filter_is_a_noop_when_unloaded(self):
        # Given (Arrange) un explorateur non chargé
        browser = self._make_browser(controller=FakeController(loaded=False))
        # When (Act) on déclenche la recherche
        browser.filter_entities()
        # Then (Assert) aucune recherche n'est planifiée
        self.assertIsNone(browser.search_after_id)
        self.assertEqual(browser.entity_tree.get_children(), ())

    # Vérifie pagination limits the first page.
    def test_pagination_limits_the_first_page(self):
        # Given (Arrange) plus d'entités que la taille d'une page
        individuals = [
            SimpleNamespace(name=f"P{i}", pointer=f"@I{i}@")
            for i in range(EntityListBrowser.PAGE_SIZE + 10)
        ]
        controller = FakeController(
            items={"INDI": [(entity, None) for entity in individuals]}
        )
        browser = self._make_browser(controller=controller)
        # When (Act) on rafraîchit la liste
        browser.refresh_entities()
        # Then (Assert) seule la première page est affichée
        self.assertEqual(
            len(browser.entity_tree.get_children()), EntityListBrowser.PAGE_SIZE
        )

    # Vérifie pagination adds a page at the bottom.
    def test_pagination_adds_a_page_at_the_bottom(self):
        # Given (Arrange) une liste dont la première page est affichée
        individuals = [
            SimpleNamespace(name=f"P{i}", pointer=f"@I{i}@")
            for i in range(EntityListBrowser.PAGE_SIZE + 10)
        ]
        controller = FakeController(
            items={"INDI": [(entity, None) for entity in individuals]}
        )
        browser = self._make_browser(controller=controller)
        browser.refresh_entities()
        # When (Act) on atteint le bas de la liste
        with patch.object(browser.entity_tree, "yview", return_value=(0.9, 1.0)):
            browser._grow_page_if_needed()
        # Then (Assert) la page suivante est ajoutée
        self.assertEqual(
            len(browser.entity_tree.get_children()), EntityListBrowser.PAGE_SIZE + 10
        )


if __name__ == "__main__":
    unittest.main()
