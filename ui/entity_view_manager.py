import tkinter as tk
from tkinter import ttk

from ui.startup_diagnostics import measure_startup_callback
from ui.views.family_view import FamilyView
from ui.views.individual_view import IndividualView
from ui.views.multimedia_view import MultimediaView
from ui.views.note_view import NoteView
from ui.views.repo_view import RepositoryView
from ui.views.source_view import SourceView
from ui.views.submitter_view import SubmitterView


class _ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.content = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.content.bind(
            "<Configure>",
            measure_startup_callback(
                self, "ScrollableFrame.content_configure", self._update_scrollregion
            ),
        )
        self.canvas.bind(
            "<Configure>",
            measure_startup_callback(
                self, "ScrollableFrame.canvas_configure", self._sync_content_width
            ),
        )
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _update_scrollregion(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_content_width(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)
        self._update_scrollregion()

    def _bind_mousewheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -int(event.delta / 120)
        self.canvas.yview_scroll(delta, "units")


class EntityViewManager:
    """Construit et affiche les vues détaillées selon le type d’entité."""

    def __init__(self, entity_view_map=None):
        self.entity_view_map = entity_view_map or {}
        self.views = {}
        self.tabs = {}

    def build_views(self, container, translator, on_navigate, controller_provider):
        view_specs = [
            (
                "individual",
                "INDI",
                IndividualView,
                True,
                {
                    "set_family_name_resolver": lambda ptr: controller_provider().get_family(
                        ptr
                    ),
                    "set_family_member_resolver": lambda ptr: controller_provider().get_individual(
                        ptr
                    ),
                    "set_family_label_resolver": lambda entity, entity_type=None: controller_provider().format_entity_label(
                        entity, entity_type
                    ),
                    "set_family_display_name_resolver": lambda entity, entity_type=None: controller_provider().format_entity_display_name(
                        entity, entity_type
                    ),
                    "set_note_resolver": lambda ptr: controller_provider().get_note(
                        ptr
                    ),
                    "set_object_resolver": lambda ptr: controller_provider().get_object(
                        ptr
                    ),
                    "set_object_display_name_resolver": lambda entity, entity_type=None: controller_provider().format_entity_display_name(
                        entity, entity_type
                    ),
                },
            ),
            (
                "family",
                "FAM",
                FamilyView,
                True,
                {
                    "set_name_resolver": lambda ptr: controller_provider().get_individual(
                        ptr
                    ),
                    "set_source_resolver": lambda ptr: controller_provider().get_source(
                        ptr
                    ),
                    "set_note_resolver": lambda ptr: controller_provider().get_note(
                        ptr
                    ),
                    "set_display_name_resolver": lambda entity, entity_type=None: controller_provider().format_entity_display_name(
                        entity, entity_type
                    ),
                },
            ),
            (
                "repo",
                "REPO",
                RepositoryView,
                True,
                {
                    "set_reference_resolver": lambda ptr: controller_provider().get_repository(
                        ptr
                    )
                },
            ),
            (
                "source",
                "SOUR",
                SourceView,
                True,
                {
                    "set_reference_resolver": lambda ptr: controller_provider().get_repository(
                        ptr
                    )
                },
            ),
            (
                "note",
                "NOTE",
                NoteView,
                True,
                {
                    "set_reference_resolver": lambda ptr: controller_provider().get_source(
                        ptr
                    )
                },
            ),
            ("object", "OBJE", MultimediaView, False, {}),
            (
                "submitter",
                "SUBM",
                SubmitterView,
                True,
                {
                    "set_reference_resolver": lambda ptr: controller_provider().get_submitter(
                        ptr
                    )
                },
            ),
        ]

        self.entity_view_map = {}
        self.views = {}
        self.tabs = {}
        for name, entity_type, view_class, scrollable, resolvers in view_specs:
            tab = ttk.Frame(container)
            if scrollable:
                scroll = _ScrollableFrame(tab)
                scroll.pack(fill="both", expand=True)
                parent = scroll.content
            else:
                parent = tab

            view = view_class(parent, on_navigate, translator)
            for resolver_name, resolver in resolvers.items():
                if hasattr(view, resolver_name):
                    getattr(view, resolver_name)(resolver)
            view.pack(fill="both", expand=True, padx=10, pady=10)

            self.views[name] = view
            self.tabs[name] = tab
            self.entity_view_map[entity_type] = (view, tab)

        return self.entity_view_map

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
