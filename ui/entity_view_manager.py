"""Construit et affiche les vues de détail par type d'entité."""

from tkinter import ttk

from ui.views.citation_property_view import CitationPropertyView
from ui.views.family_property_view import FamilyPropertyView
from ui.views.individual_property_view import IndividualPropertyView
from ui.views.multimedia_property_view import MultimediaPropertyView
from ui.views.note_property_view import NotePropertyView
from ui.views.repository_property_view import RepositoryPropertyView
from ui.views.source_property_view import SourcePropertyView
from ui.views.submitter_property_view import SubmitterPropertyView


class EntityViewManager:
    """Construit et affiche les vues détaillées selon le type d’entité."""

    VIEW_SPECS = (
        ("individual", "INDI", IndividualPropertyView),
        ("family", "FAM", FamilyPropertyView),
        ("source", "SOUR", SourcePropertyView),
        ("repo", "REPO", RepositoryPropertyView),
        ("note", "NOTE", NotePropertyView),
        ("object", "OBJE", MultimediaPropertyView),
        ("submitter", "SUBM", SubmitterPropertyView),
        ("citation", "CITE", CitationPropertyView),
    )

    def __init__(self, entity_view_map=None):
        """Initialise le gestionnaire de vues."""
        self.entity_view_map = entity_view_map or {}
        self.views = {}
        self.tabs = {}
        self._visible_type = None

    def build_views(
        self,
        container,
        translator,
        on_navigate,
        controller_provider,
        tooltip_factory=None,
        base_path=None,
    ):
        """Construit les vues de détail par type d'entité."""
        resolvers = {
            "set_pointer_resolver": lambda pointer: controller_provider().resolve_pointer(
                pointer
            ),
            "set_display_name_resolver": lambda entity, entity_type=None: controller_provider().format_entity_display_name(  # type: ignore[misc]
                entity, entity_type
            ),
            "set_family_name_resolver": lambda pointer: controller_provider().get_family(
                pointer
            ),
            "set_family_member_resolver": lambda pointer: controller_provider().get_individual(
                pointer
            ),
            "set_family_display_name_resolver": lambda entity, entity_type=None: controller_provider().format_entity_display_name(  # type: ignore[misc]
                entity, entity_type
            ),
            "set_note_resolver": lambda pointer: controller_provider().get_note(
                pointer
            ),
            "set_object_resolver": lambda pointer: controller_provider().get_object(
                pointer
            ),
            "set_object_display_name_resolver": lambda entity, entity_type=None: controller_provider().format_entity_display_name(  # type: ignore[misc]
                entity, entity_type
            ),
            "set_details_formatter_resolver": lambda details: controller_provider().format_details(
                details
            ),
        }

        self.entity_view_map = {}
        self.views = {}
        self.tabs = {}
        self._visible_type = None
        for name, entity_type, view_class in self.VIEW_SPECS:
            tab = ttk.Frame(container)
            view = view_class(
                tab,
                on_navigate,
                translator,
                entity_type=entity_type,
                tooltip_factory=tooltip_factory,
            )
            if isinstance(view, MultimediaPropertyView):
                view.set_base_path(base_path)
            for resolver_name, resolver in resolvers.items():
                getattr(view, resolver_name)(resolver)
            view.pack(fill="both", expand=True, padx=10, pady=10)

            self.views[name] = view
            self.tabs[name] = tab
            self.entity_view_map[entity_type] = (view, tab)

        return self.entity_view_map

    def clear(self, keep_type=None):
        """Efface les vues (ou toutes sauf un type)."""
        if keep_type is None:
            for _view, tab in self.entity_view_map.values():
                tab.pack_forget()
            for view, _tab in self.entity_view_map.values():
                view.display(None)
            self._visible_type = None
            return

        for entity_type, (_view, tab) in self.entity_view_map.items():
            if entity_type == keep_type:
                tab.pack(fill="both", expand=True)
            else:
                tab.pack_forget()
        self._visible_type = keep_type

    def show(self, entity_type, entity=None):
        """Affiche la vue d'un type d'entité."""
        if entity is not None and not getattr(entity, "pointer", None):
            entity = None

        for current_type, (view, tab) in self.entity_view_map.items():
            if current_type == entity_type:
                tab.pack(fill="both", expand=True)
                view.display(entity)
            else:
                tab.pack_forget()
        self._visible_type = entity_type
