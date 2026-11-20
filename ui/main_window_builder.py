"""Construction de l'arborescence de widgets de la fenêtre principale.

Ce module isole la responsabilité de construction de l'interface ( assemblage
des composants visuels) de la logique d'orchestration portée par
:class:`ui.main_window.GedcomViewer`.
"""

import tkinter as tk
from tkinter import ttk

from ui.app_header import AppHeader
from ui.detail_panel import DetailPanel
from ui.entity_list_browser import EntityListBrowser
from ui.entity_selection_coordinator import EntitySelectionCoordinator
from ui.entity_type_panel import EntityTypePanel
from ui.navigation_bar import NavigationBar
from ui.status_bar import StatusBar
from ui.theme_aware import register_theme_aware_components
from ui.tooltip import Tooltip


class MainWindowBuilder:
    """Construit les widgets de la fenêtre principale et les rattache à l'hôte."""

    def __init__(self, host):
        """Mémorise la fenêtre hôte qui recevra les widgets construits."""
        self.host = host

    def build(self):
        """Construit l'ensemble de l'interface principale."""
        self._build_app_header()
        self._build_layout()
        self._build_entity_type_panel()
        self._build_entity_viewer()
        self._build_detail_views()
        self._register_theme_aware()

    def _register_theme_aware(self):
        """Enregistre les composants qui savent se re-thémer."""
        register_theme_aware_components(self.host)

    def _build_app_header(self):
        """Crée l'en-tête applicatif."""
        host = self.host
        host.app_header = AppHeader(
            host.root,
            host.translator,
        )
        host.app_header.pack(fill="x", padx=10, pady=(10, 0))

    def _build_layout(self):
        """Crée les conteneurs principaux (navigation et contenu)."""
        host = self.host
        root = host.root
        content_frame = ttk.Frame(root)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0)
        content_frame.grid_columnconfigure(1, weight=1)

        # Liste des types d'entités (toujours visible, colonne de gauche).
        host.entity_type_tabs_frame = tk.Frame(content_frame)
        host.entity_type_tabs_frame.grid(row=0, column=0, sticky="nsew")

        # Conteneur central : affiche soit la liste des entités+vues, soit l'arbre.
        host.central_frame = tk.Frame(content_frame)
        host.central_frame.grid(row=0, column=1, sticky="nsew")
        host.central_frame.grid_rowconfigure(0, weight=1)
        host.central_frame.grid_columnconfigure(0, weight=1)

        host.main_pane = tk.PanedWindow(host.central_frame, orient="horizontal")
        host.main_pane.grid(row=0, column=0, sticky="nsew")

        host.left_frame = tk.Frame(host.main_pane)
        host.main_pane.add(host.left_frame, minsize=280, width=320, stretch="never")

        host.right_frame = tk.Frame(host.main_pane)
        host.main_pane.add(host.right_frame, minsize=420, width=580, stretch="always")

        host.right_frame.grid_columnconfigure(0, weight=1)
        host.right_frame.grid_rowconfigure(1, weight=1)

        host.ancestor_tree_frame = tk.Frame(host.central_frame)
        host.ancestor_tree_frame.grid(row=0, column=0, sticky="nsew")
        host.ancestor_tree_frame.grid_remove()

    def _build_entity_type_panel(self):
        """Crée le panneau de types et l'explorateur d'entités."""
        host = self.host
        host.entity_type_var = tk.StringVar()

        host.entity_type_tabs = EntityTypePanel(
            host.entity_type_tabs_frame,
            host.translator,
            host.entity_type_var,
        )
        host.entity_type_tabs.pack(fill="both", expand=True)

        host.entity_browser = EntityListBrowser(
            host.left_frame,
            host.translator,
            lambda: host.controller,
            host.entity_type_var,
            on_select=host.show_entity,
            on_empty=host._clear_empty_entity_selection,
            tooltip_factory=Tooltip,
        )
        host.entity_browser.pack(fill="both", expand=True)
        host.entity_selection_coordinator = EntitySelectionCoordinator(
            host.entity_type_var,
            host.entity_type_tabs,
            host.entity_browser,
            host.entity_view_manager,
        )
        host.entity_type_var.trace_add("write", host.on_entity_type_change)

    def _build_entity_viewer(self):
        """Crée la barre de navigation, la barre de statut et le panneau de détail."""
        self._build_navigation_bar()
        self._build_status_bar()
        self._build_content_panels()

    def _build_navigation_bar(self):
        """Crée la barre de navigation."""
        host = self.host
        host.nav_toolbar = NavigationBar(
            host.right_frame,
            host.translator,
            on_back=host.go_back,
            on_forward=host.go_forward,
            tooltip_factory=Tooltip,
        )
        host.nav_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 7))

    def _build_status_bar(self):
        """Crée la barre de statut."""
        host = self.host
        host.status_var = tk.StringVar(value=host.translator.get("ui.ready"))
        host.log_status_frame = StatusBar(
            host.right_frame, host.translator, host.status_var
        )
        host.log_status_frame.grid(row=2, column=0, sticky="ew", pady=(4, 0))

    def _build_content_panels(self):
        """Crée le panneau de détail (GEDCOM brut et fiche entité)."""
        host = self.host
        right_content = tk.PanedWindow(
            host.right_frame, orient="horizontal", sashrelief="raised", sashwidth=8
        )
        right_content.grid(row=1, column=0, sticky="nsew")

        host.detail_panel = DetailPanel(
            right_content,
            host.translator,
            controller_provider=lambda: host.controller,
            tooltip_factory=Tooltip,
        )
        host._apply_view_preferences()
        right_content.add(host.detail_panel, minsize=300, width=370)
        right_content.paneconfigure(host.detail_panel, stretch="always")

    def _build_detail_views(self):
        """Construit les vues de détail par type d'entité."""
        host = self.host
        # Résoudre self.controller à l'appel permet de remplacer la session après chargement.
        host._entity_view_map = host.entity_view_manager.build_views(
            host.detail_panel.entity_detail_container,
            host.translator,
            host.navigate_to,
            lambda: host.controller,
            tooltip_factory=Tooltip,
            base_path=None,
        )
