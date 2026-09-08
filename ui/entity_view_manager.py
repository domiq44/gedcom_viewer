class EntityViewManager:
    """Gère l’affichage des vues détaillées selon le type d’entité sélectionné."""

    def __init__(self, entity_view_map):
        self.entity_view_map = entity_view_map

    def clear(self, keep_type=None):
        for entity_type, (view, tab) in self.entity_view_map.items():
            if entity_type == keep_type:
                tab.pack(fill="both", expand=True)
            else:
                tab.pack_forget()
                view.display(None)

    def show(self, entity_type, entity=None):
        if entity is not None and not getattr(entity, "pointer", None):
            entity = None

        for current_type, (view, tab) in self.entity_view_map.items():
            if current_type == entity_type:
                tab.pack(fill="both", expand=True)
                view.display(entity)
            else:
                tab.pack_forget()
                view.display(None)
