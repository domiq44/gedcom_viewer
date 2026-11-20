"""Coordonne la sélection d'entité entre panneaux."""


class EntitySelectionCoordinator:
    """Synchronise le type affiché, la liste et l’entité sélectionnée."""

    def __init__(
        self, entity_type_var, entity_type_panel, entity_browser, view_manager
    ):
        """Initialise le coordinateur de sélection."""
        self.entity_type_var = entity_type_var
        self.entity_type_panel = entity_type_panel
        self.entity_browser = entity_browser
        self.view_manager = view_manager
        self._syncing_context = False
        self._selection_to_ignore = None
        self._last_selected_entities = {}

    def on_entity_type_change(self):
        """Synchronise la liste et la vue après changement de type."""
        entity_type = self.entity_type_var.get()
        self.entity_type_panel.update_selection(entity_type)
        if self._syncing_context:
            return

        self.view_manager.clear(keep_type=entity_type)
        self._refresh_list(reset_search=True)
        children = self.entity_browser.entity_tree.get_children()
        if children and children[0] != "empty":
            remembered_entity = self._last_selected_entities.get(entity_type)
            if remembered_entity is not None and self.entity_browser.select_entity(
                remembered_entity
            ):
                return
            self.entity_browser.entity_tree.selection_set(children[0])
            self.entity_browser.entity_tree.focus(children[0])

    def remember_selection(self, entity_type, entity):
        """Mémorise la dernière sélection par type."""
        if entity_type and entity is not None:
            self._last_selected_entities[entity_type] = entity

    def get_selection_pointers(self):
        """Retourne les sélections mémorisées sous forme de pointeurs (sérialisable)."""
        pointers = {}
        for entity_type, entity in self._last_selected_entities.items():
            pointer = getattr(entity, "pointer", None)
            if pointer:
                pointers[entity_type] = pointer
        return pointers

    def load_selection_pointers(self, pointers, resolve_entity):
        """Restaure les sélections à partir de pointeurs.

        ``resolve_entity`` est un appelable prenant un pointeur et retournant
        l'entité correspondante (ou ``None``).
        """
        self._last_selected_entities = {}
        for entity_type, pointer in pointers.items():
            entity = resolve_entity(pointer)
            if entity is not None:
                self._last_selected_entities[entity_type] = entity

    def clear_selection_memory(self):
        """Oublie les sélections mémorisées."""
        self._last_selected_entities.clear()

    def snapshot_selection_memory(self):
        """Retourne une copie de l'état de sélection courant."""
        return {
            "last_selected_entities": dict(self._last_selected_entities),
            "selection_to_ignore": self._selection_to_ignore,
        }

    def restore_selection_memory(self, snapshot):
        """Restaure un état de sélection capturé."""
        self._last_selected_entities = dict(snapshot.get("last_selected_entities", {}))
        self._selection_to_ignore = snapshot.get("selection_to_ignore")

    def set_entity_type_without_refresh(self, entity_type):
        """Définit le type courant sans déclencher de rafraîchissement."""
        self._syncing_context = True
        try:
            self.entity_type_var.set(entity_type)
        finally:
            self._syncing_context = False

    def synchronize_to_context(self, context, display_type_map):
        """Aligne type, liste et sélection sur un contexte."""
        entity_type = display_type_map.get(context.get("type"))
        entity = context.get("entity")
        if entity_type is None or entity is None:
            return

        controller = self.entity_browser.controller
        if controller is None or not controller.is_loaded():
            return

        available_types = controller.get_entity_types()
        if not isinstance(available_types, (list, tuple, set)):
            return
        if entity_type not in available_types:
            return

        type_changed = entity_type != self.entity_type_var.get()
        self._syncing_context = True
        try:
            if type_changed:
                self.entity_type_var.set(entity_type)

            if type_changed or not self.entity_browser.contains_entity(entity):
                self._refresh_list(reset_search=True)

            if self.entity_browser.select_entity(entity):
                self._selection_to_ignore = entity
            self.remember_selection(entity_type, entity)
        finally:
            self._syncing_context = False

    def should_ignore_selection(self, entity):
        """Indique si la sélection doit être ignorée (une fois)."""
        if self._selection_to_ignore is not entity:
            return False
        self._selection_to_ignore = None
        return True

    def _refresh_list(self, reset_search):
        """Recharge la liste des entités."""
        self.entity_browser.cancel_pending_search()
        if reset_search and self.entity_browser.search_var.get():
            self.entity_browser.reset_search()
            self.entity_browser.cancel_pending_search()
        self.entity_browser.list_entities()
