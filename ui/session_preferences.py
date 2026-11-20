"""Préférences de session : thème, langue et fichiers récents."""

import logging
import os
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Any, Protocol, runtime_checkable

from controllers.recent_files_store import RecentFilesStore
from ui.app_header import AppHeader
from ui.application_menu import ApplicationMenu
from ui.detail_panel import DetailPanel
from ui.entity_list_browser import EntityListBrowser
from ui.entity_type_panel import EntityTypePanel
from ui.file_manager import FileManager
from ui.i18n import Translator
from ui.navigation_bar import NavigationBar
from ui.status_bar import StatusBar
from ui.syntax_highlighter import GedcomHighlighter
from ui.theme_aware import ThemeRegistry
from ui.themes import COLORS, apply_app_theme, current_theme, set_theme

logger = logging.getLogger(__name__)


@runtime_checkable
class SessionHost(Protocol):
    """Contrat structurel attendu de l'hôte du mixin de préférences."""

    root: tk.Misc
    translator: Translator
    status_var: tk.StringVar
    file_manager: FileManager
    menu_bar: ApplicationMenu
    detail_panel: DetailPanel
    app_header: AppHeader
    entity_type_tabs: EntityTypePanel
    entity_browser: EntityListBrowser
    nav_toolbar: NavigationBar
    log_status_frame: StatusBar
    highlighter: GedcomHighlighter
    theme_registry: ThemeRegistry
    recent_files: list[str]
    last_directory: str
    theme: str
    window_size: tuple[int, int] | None
    view_preferences: dict[str, object]
    last_selected_entities: dict[str, str]

    def _show_entity_view(self, entity_type: str | None, entity: Any) -> None:
        """Affiche l'entité courante."""
        ...

    def _load_file_async(self, filename: str, strict: bool = False) -> None:
        """Charge un fichier de manière asynchrone."""
        ...


class SessionPreferencesMixin:
    """Gère le thème, la langue et les fichiers récents de la session.

    Les attributs annotés ci-dessous sont fournis par la classe hôte
    (``GedcomViewer``) ; le mixin n'instancie aucun widget.
    """

    SETTINGS_PATH = "~/.gedcom_viewer.json"

    root: Any
    translator: Translator
    status_var: tk.StringVar
    file_manager: FileManager
    menu_bar: ApplicationMenu
    detail_panel: DetailPanel
    app_header: AppHeader
    entity_type_tabs: EntityTypePanel
    entity_browser: EntityListBrowser
    nav_toolbar: NavigationBar
    log_status_frame: StatusBar
    highlighter: GedcomHighlighter
    theme_registry: ThemeRegistry

    recent_files: list[str]
    last_directory: str
    theme: str
    window_size: tuple[int, int] | None
    view_preferences: dict[str, object]
    last_selected_entities: dict[str, str]
    max_age_for_deceased: int

    # Attributs fournis par la classe hôte (GedcomViewer) et typés Any car
    # ils ne sont pas déclarés sur ce mixin.
    entity_selection_coordinator: Any
    _current_entity: Any
    _current_entity_type: Any

    def _open_recent_file_on_startup(self) -> None:
        """Recharge automatiquement le dernier fichier au démarrage."""
        if not self.recent_files:
            logger.info("Aucun fichier GEDCOM récent à charger au démarrage")
            return

        startup_file = self.recent_files[0]
        if not os.path.isfile(startup_file):
            logger.info("Le dernier fichier récent n'est pas disponible au démarrage")
            return

        logger.info("Rechargement automatique du dernier GEDCOM récent programmé")
        self.status_var.set(self.translator.get("ui.loading_last_file"))
        load_async = getattr(self, "_load_file_async", None)
        if load_async is not None:
            self.root.after(50, load_async, startup_file)

    def _load_recent_files(self) -> list[str]:
        """Charge les préférences et les fichiers récents."""
        store = RecentFilesStore(self.SETTINGS_PATH, file_opener=open, log=logger)
        recent_files, last_directory, language = store.load(self.last_directory)
        self.last_directory = last_directory
        self.window_size = store.window_size
        self.view_preferences = store.view_preferences
        self.last_selected_entities = store.last_selected_entities
        raw_max_age = self.view_preferences.get("max_age_for_deceased", 110)
        self.max_age_for_deceased = raw_max_age if type(raw_max_age) is int else 110
        if self.window_size is not None:
            self.root.geometry(f"{self.window_size[0]}x{self.window_size[1]}")
        if isinstance(language, str):
            try:
                self.translator.set_language(language)
            except ValueError:
                logger.warning(
                    "Langue non supportee dans les preferences: %s", language
                )
        theme = store.theme
        self.theme = (
            theme if isinstance(theme, str) and theme in ("light", "dark") else "light"
        )
        set_theme(self.theme)
        apply_app_theme(self.root)
        self.root.configure(bg=COLORS["background"])
        return recent_files

    def _apply_view_preferences(self) -> None:
        """Applique les préférences d'affichage au panneau de détail."""
        preferences = getattr(self, "view_preferences", {})
        if "indent" in preferences:
            self.detail_panel.indent_var.set(preferences["indent"])
        self.detail_panel.set_view_visibility(
            preferences.get("show_gedcom_view", False),
            preferences.get("show_entity_view", True),
        )

    def _sync_file_manager(self) -> None:
        """Synchronise le gestionnaire de fichiers avec l'état courant."""
        self.file_manager.last_directory = self.last_directory
        self.file_manager.recent_files = self.recent_files

    def _save_recent_files(self) -> None:
        """Enregistre les fichiers récents et les préférences."""
        self._sync_file_manager()
        store = RecentFilesStore(self.SETTINGS_PATH, file_opener=open, log=logger)
        store.save(
            self.recent_files,
            self.last_directory,
            self.translator.language,
            window_size=(self.root.winfo_width(), self.root.winfo_height()),
            view_preferences={
                "indent": self.detail_panel.indent_var.get(),
                "show_gedcom_view": self.detail_panel.show_gedcom_view_var.get(),
                "show_entity_view": self.detail_panel.show_entity_view_var.get(),
                "max_age_for_deceased": getattr(self, "max_age_for_deceased", 110),
            },
            last_selected_entities=self.entity_selection_coordinator.get_selection_pointers(),
            theme=getattr(self, "theme", current_theme()),
        )

    def toggle_theme(self, theme: str) -> None:
        """Bascule le thème (clair/sombre) à l'exécution et le sauvegarde."""
        if theme == getattr(self, "theme", None):
            return
        self.theme = theme
        set_theme(theme)
        apply_app_theme(self.root)
        self.root.configure(bg=COLORS["background"])
        self._apply_theme()
        self._save_recent_files()

    def _apply_theme(self) -> None:
        """Re-applique le thème courant aux widgets tk persistants."""
        registry = getattr(self, "theme_registry", None)
        if registry is not None:
            registry.apply_theme()

        current_entity = getattr(self, "_current_entity", None)
        if current_entity is not None:
            show_entity_view = getattr(self, "_show_entity_view", None)
            if show_entity_view is not None:
                show_entity_view(
                    getattr(self, "_current_entity_type", None), current_entity
                )
        self.highlighter.highlight()

    def set_language(self, language: str) -> None:
        """Change la langue après confirmation et redémarre."""
        if language == self.translator.language:
            return

        previous_language = self.translator.language
        self.translator.set_language(language)

        confirmed = messagebox.askyesno(
            self.translator.get("menu.language"),
            self.translator.get("menu.language_confirm"),
            parent=self.root,
        )
        if not confirmed:
            self.translator.set_language(previous_language)
            if hasattr(self.menu_bar, "language_var"):
                self.menu_bar.language_var.set(previous_language)
            return

        self._save_recent_files()
        self.root.after(100, self._restart_application)

    def _restart_application(self) -> None:
        """Redémarre l'application.

        Seuls le script principal est transmis (``sys.argv[0]``) : les
        éventuels arguments PyInstaller ou chemins temporaires de
        ``sys.argv`` ne sont pas reconduits, car ils deviennent invalides
        après redémarrage (nouvel environnement temporaire PyInstaller).
        Le fichier GEDCOM ouvert est rechargé automatiquement depuis la
        liste des fichiers récents au démarrage.
        """
        self.root.destroy()
        os.execv(sys.executable, [sys.executable, sys.argv[0]])

    def clear_recent_files(self) -> None:
        """Efface la liste des fichiers récents."""
        self.recent_files = []
        self._save_recent_files()
        if hasattr(self, "menu_bar"):
            self.menu_bar.refresh_recent_menu()

    def _remember_recent_file(self, filename: str) -> None:
        """Mémorise un fichier récent et met à jour le menu."""
        self.file_manager.remember_recent_file(filename)
        self.last_directory = self.file_manager.last_directory
        self.recent_files = self.file_manager.recent_files
        self._save_recent_files()
        if hasattr(self, "menu_bar"):
            self.menu_bar.refresh_recent_menu()
