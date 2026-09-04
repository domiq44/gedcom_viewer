import json
import logging
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

logger = logging.getLogger(__name__)

from controllers.app_controller import AppController
from ui.menus import MenuBar
from ui.syntax_highlighter import GedcomHighlighter
from ui.views.individual_view import IndividualView
from ui.views.family_view import FamilyView
from ui.views.repo_view import RepositoryView
from ui.views.source_view import SourceView
from ui.views.note_view import NoteView
from ui.views.multimedia_view import MultimediaView
from ui.views.submitter_view import SubmitterView
from ui.themes import COLORS, FONTS


class _UiLogHandler(logging.Handler):
    def __init__(self, status_var):
        super().__init__()
        self.status_var = status_var

    def emit(self, record):
        try:
            message = self.format(record)
            self.status_var.set(message)
        except Exception:
            pass


class _Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.window = None
        self.after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _schedule(self, event=None):
        self._hide()
        self.after_id = self.widget.after(450, self._show)

    def _show(self):
        self.after_id = None
        if not self.widget.winfo_exists() or not self.widget.winfo_ismapped():
            return

        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(
            f"+{self.widget.winfo_rootx()}+{self.widget.winfo_rooty() + self.widget.winfo_height() + 4}"
        )
        tk.Label(
            self.window,
            text=self.text,
            bg="#263746",
            fg="#ffffff",
            padx=7,
            pady=4,
            font=("TkDefaultFont", 9),
        ).pack()

    def _hide(self, event=None):
        if self.after_id is not None:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.window is not None:
            self.window.destroy()
            self.window = None


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
        self.content.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._sync_content_width)
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


class GedcomViewer:
    SETTINGS_PATH = "~/.gedcom_viewer.json"
    LEGACY_RECENT_PATH = "~/.gedcom_viewer_recent.json"

    def __init__(self, root):
        self.root = root
        self.root.title("GEDCOM Viewer 5.5.1")
        self.root.configure(bg=COLORS["background"])
        self.root.minsize(1100, 700)

        self.last_directory = os.path.expanduser("~")
        self.recent_files = self._load_recent_files()
        self.menu_bar = MenuBar(self.root, self)
        self.controller = AppController()
        self.filtered_entities = []
        self._nav_history = []
        self._nav_index = -1
        self._entity_sort_column = None
        self._entity_sort_reverse = False
        self._entity_by_item_id = {}

        self.app_header = tk.Frame(
            root,
            bg="#dfeaf5",
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
            padx=18,
            pady=10,
        )
        self.app_header.pack(fill="x", padx=10, pady=(10, 0))

        self.app_title = tk.Label(
            self.app_header,
            text="GEDCOM Viewer",
            font=("Segoe UI", 18, "bold"),
            bg="#dfeaf5",
            fg="#163a57",
        )
        self.app_title.pack(anchor="w")

        self.app_subtitle = tk.Label(
            self.app_header,
            text="Explorateur de fichiers GEDCOM",
            font=("Segoe UI", 9),
            bg="#dfeaf5",
            fg="#44627a",
        )
        self.app_subtitle.pack(anchor="w")

        content_frame = ttk.Frame(root)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        layout_pane = tk.PanedWindow(content_frame, orient="horizontal")
        layout_pane.grid(row=0, column=0, sticky="nsew")

        self.entity_type_tabs = tk.Frame(
            layout_pane,
            bg=COLORS["sidebar"],
            width=220,
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
        )
        self.entity_type_tabs.grid_propagate(False)
        self.entity_type_tabs.grid_columnconfigure(0, weight=1)
        self._entity_type_buttons = {}
        layout_pane.add(self.entity_type_tabs, minsize=190, width=220)

        main_pane = tk.PanedWindow(layout_pane, orient="horizontal")
        layout_pane.add(main_pane, minsize=700, stretch="always")

        # --- FRAME GAUCHE ---
        left_frame = tk.Frame(main_pane)
        main_pane.add(left_frame, minsize=280, width=320, stretch="never")

        self.entity_type_var = tk.StringVar()
        self.entity_type_var.trace_add("write", self.on_entity_type_change)

        tk.Label(left_frame, text="Recherche :").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_entities)
        self.search_entry = tk.Entry(
            left_frame,
            textvariable=self.search_var,
            width=30,
            relief="solid",
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["selection"],
            bg="#ffffff",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
        )
        self.search_entry.grid(row=1, column=0, sticky="ew")

        tk.Label(left_frame, text="Entités :").grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        self.entity_tree = ttk.Treeview(
            left_frame,
            columns=("name", "pointer"),
            show="headings",
            selectmode="browse",
            style="Entity.Treeview",
            padding=(6, 0),
        )
        self.entity_tree.heading(
            "name", text="Nom", command=lambda: self._sort_entity_tree("name")
        )
        self.entity_tree.heading(
            "pointer",
            text="Identifiant",
            command=lambda: self._sort_entity_tree("pointer"),
        )
        self.entity_tree.column("name", width=230, minwidth=140, anchor="w")
        self.entity_tree.column("pointer", width=80, minwidth=70, anchor="e")
        self.entity_tree.grid(row=3, column=0, sticky="nsew")
        self.entity_tree.bind("<<TreeviewSelect>>", self.show_entity)

        entity_scrollbar = ttk.Scrollbar(
            left_frame, orient="vertical", command=self.entity_tree.yview
        )
        entity_scrollbar.grid(row=3, column=1, sticky="ns")
        self.entity_tree.configure(yscrollcommand=entity_scrollbar.set)

        left_frame.grid_rowconfigure(3, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # --- FRAME DROITE ---
        right_frame = tk.Frame(main_pane)
        main_pane.add(right_frame, minsize=420, width=580, stretch="always")

        self.nav_toolbar = tk.Frame(
            right_frame,
            bg=COLORS["background"],
            padx=0,
            pady=2,
        )
        self.nav_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 7))

        navigation_group = tk.Frame(
            self.nav_toolbar,
            bg=COLORS["surface"],
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
        )
        navigation_group.pack(side="left")

        self.back_button = ttk.Button(
            navigation_group,
            text="←",
            command=self.go_back,
            style="Nav.TButton",
            width=3,
        )
        self.back_button.pack(side="left")
        _Tooltip(self.back_button, "Précédent")

        self.forward_button = ttk.Button(
            navigation_group,
            text="→",
            command=self.go_forward,
            style="Nav.TButton",
            width=3,
        )
        self.forward_button.pack(side="left")
        _Tooltip(self.forward_button, "Suivant")

        self.history_status = tk.Label(
            self.nav_toolbar,
            text="Historique : 0/0",
            bg=COLORS["background"],
            foreground=COLORS["muted_text"],
            font=FONTS["ui"],
        )
        self.history_status.pack(side="right", padx=(12, 4))

        self.status_var = tk.StringVar(value="Prêt")
        self.log_status_frame = tk.LabelFrame(
            right_frame,
            text="Dernière erreur log",
            padx=6,
            pady=4,
        )
        self.log_status_frame.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        self.status_label = tk.Entry(
            self.log_status_frame,
            textvariable=self.status_var,
            font=("TkDefaultFont", 9),
            state="readonly",
            readonlybackground=self.log_status_frame.cget("background"),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        self.status_label.pack(fill="x", expand=True)

        right_content = tk.PanedWindow(
            right_frame, orient="horizontal", sashrelief="raised", sashwidth=8
        )
        right_content.grid(row=1, column=0, sticky="nsew")

        self.gedcom_frame = tk.LabelFrame(
            right_content,
            text="GEDCOM",
            padx=8,
            pady=8,
            bg=COLORS["background"],
            bd=1,
            relief="groove",
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
        )
        right_content.add(self.gedcom_frame, minsize=300, width=370)
        right_content.paneconfigure(self.gedcom_frame, stretch="always")

        tk.Label(self.gedcom_frame, text="Contenu brut du fichier :").pack(
            anchor="w", pady=(0, 5)
        )
        self.text_area = tk.Text(
            self.gedcom_frame,
            width=70,
            height=30,
            font=FONTS["mono"],
            state="disabled",
            relief="solid",
            bd=1,
            bg="#fcfcfd",
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["selection"],
        )
        self.text_area.pack(fill="both", expand=True)

        self.entity_detail_frame = tk.LabelFrame(
            right_content,
            text="Vue de l’entité",
            padx=8,
            pady=8,
            bg=COLORS["background"],
            bd=1,
            relief="groove",
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
        )
        right_content.add(self.entity_detail_frame, minsize=340, width=410)
        right_content.paneconfigure(self.entity_detail_frame, stretch="always")

        self.entity_detail_container = tk.Frame(
            self.entity_detail_frame, bg=COLORS["surface"], bd=1, relief="solid"
        )
        self.entity_detail_container.pack(fill="both", expand=True)
        self.entity_detail_container.grid_rowconfigure(0, weight=1)
        self.entity_detail_container.grid_columnconfigure(0, weight=1)

        self.individual_tab = ttk.Frame(self.entity_detail_container)
        individual_scroll = _ScrollableFrame(self.individual_tab)
        individual_scroll.pack(fill="both", expand=True)
        self.individual_view = IndividualView(individual_scroll.content, self.navigate_to)
        self.individual_view.set_family_name_resolver(self.controller.get_family)
        self.individual_view.set_family_member_resolver(self.controller.get_individual)
        self.individual_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.family_tab = ttk.Frame(self.entity_detail_container)
        family_scroll = _ScrollableFrame(self.family_tab)
        family_scroll.pack(fill="both", expand=True)
        self.family_view = FamilyView(family_scroll.content, self.navigate_to)
        self.family_view.set_name_resolver(self.controller.get_individual)
        self.family_view.set_source_resolver(self.controller.get_source)
        self.family_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.repo_tab = ttk.Frame(self.entity_detail_container)
        repo_scroll = _ScrollableFrame(self.repo_tab)
        repo_scroll.pack(fill="both", expand=True)
        self.repo_view = RepositoryView(repo_scroll.content, self.navigate_to)
        self.repo_view.set_reference_resolver(self.controller.get_repository)
        self.repo_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.source_tab = ttk.Frame(self.entity_detail_container)
        source_scroll = _ScrollableFrame(self.source_tab)
        source_scroll.pack(fill="both", expand=True)
        self.source_view = SourceView(source_scroll.content, self.navigate_to)
        self.source_view.set_reference_resolver(self.controller.get_repository)
        self.source_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.note_tab = ttk.Frame(self.entity_detail_container)
        note_scroll = _ScrollableFrame(self.note_tab)
        note_scroll.pack(fill="both", expand=True)
        self.note_view = NoteView(note_scroll.content, self.navigate_to)
        self.note_view.set_reference_resolver(self.controller.get_source)
        self.note_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.object_tab = ttk.Frame(self.entity_detail_container)
        self.object_view = MultimediaView(self.object_tab, self.navigate_to)
        self.object_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.submitter_tab = ttk.Frame(self.entity_detail_container)
        submitter_scroll = _ScrollableFrame(self.submitter_tab)
        submitter_scroll.pack(fill="both", expand=True)
        self.submitter_view = SubmitterView(submitter_scroll.content, self.navigate_to)
        self.submitter_view.set_reference_resolver(self.controller.get_submitter)
        self.submitter_view.pack(fill="both", expand=True, padx=10, pady=10)

        self._entity_view_map = {
            "INDI": (self.individual_view, self.individual_tab),
            "FAM": (self.family_view, self.family_tab),
            "REPO": (self.repo_view, self.repo_tab),
            "SOUR": (self.source_view, self.source_tab),
            "NOTE": (self.note_view, self.note_tab),
            "OBJE": (self.object_view, self.object_tab),
            "SUBM": (self.submitter_view, self.submitter_tab),
        }
        self._update_entity_type_tabs()

        self.highlighter = GedcomHighlighter(self.text_area)
        self._attach_ui_log_handler()
        self._update_navigation_buttons()

        if self.recent_files:
            startup_file = self.recent_files[0]
            if os.path.isfile(startup_file):
                self.status_var.set("Chargement du dernier fichier GEDCOM…")
                self.root.after(50, self._load_file_from_path, startup_file)

        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        self.entity_detail_frame.grid_columnconfigure(0, weight=1)
        self.entity_detail_frame.grid_rowconfigure(0, weight=1)

    def _attach_ui_log_handler(self):
        if hasattr(self, "_ui_log_handler"):
            return

        self._ui_log_handler = _UiLogHandler(self.status_var)
        self._ui_log_handler.setFormatter(
            logging.Formatter("%(levelname)s: %(message)s")
        )
        logging.getLogger().addHandler(self._ui_log_handler)

    def _load_recent_files(self):
        settings_path = os.path.expanduser(self.SETTINGS_PATH)
        legacy_path = os.path.expanduser(self.LEGACY_RECENT_PATH)
        recent_path = settings_path if os.path.isfile(settings_path) else legacy_path
        if not os.path.isfile(recent_path):
            return []

        try:
            with open(recent_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                last_directory = data.get("last_directory")
                if isinstance(last_directory, str) and os.path.isdir(last_directory):
                    self.last_directory = last_directory
                data = data.get("recent_files", [])
            if isinstance(data, list):
                recent_files = [path for path in data if isinstance(path, str)]
                if self.last_directory == os.path.expanduser("~"):
                    for path in recent_files:
                        directory = os.path.dirname(os.path.abspath(path))
                        if os.path.isdir(directory):
                            self.last_directory = directory
                            break
                return recent_files
        except Exception as exc:
            logger.warning(
                "Impossible de lire la liste des fichiers récents %s: %s",
                recent_path,
                exc,
            )
            return []
        return []

    def _save_recent_files(self):
        recent_path = os.path.expanduser(self.SETTINGS_PATH)
        try:
            with open(recent_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "recent_files": self.recent_files[:10],
                        "last_directory": self.last_directory,
                    },
                    handle,
                )
        except Exception as exc:
            logger.warning(
                "Impossible d'enregistrer la liste des fichiers récents %s: %s",
                recent_path,
                exc,
            )

    def clear_recent_files(self):
        self.recent_files = []
        self._save_recent_files()
        if hasattr(self, "menu_bar"):
            self.menu_bar.refresh_recent_menu()

    def _remember_recent_file(self, filename):
        normalized = os.path.abspath(filename)
        if not normalized:
            return

        self.last_directory = os.path.dirname(normalized)
        self.recent_files = [
            path for path in self.recent_files if os.path.abspath(path) != normalized
        ]
        self.recent_files.insert(0, normalized)
        self.recent_files = self.recent_files[:10]
        self._save_recent_files()
        if hasattr(self, "menu_bar"):
            self.menu_bar.refresh_recent_menu()

    def _file_dialog_options(self):
        initialdir = self.last_directory
        if not initialdir or not os.path.isdir(initialdir):
            initialdir = os.path.expanduser("~")
        return {"initialdir": initialdir}

    def _load_file_from_path(self, filename, strict=False):
        if not filename:
            return

        logger.info("Chargement du fichier GEDCOM: %s", filename)
        load_started_at = time.perf_counter()
        try:
            self.controller.load_file(filename, strict=strict)
        except Exception as e:
            logger.exception("Échec du chargement du GEDCOM %s", filename)
            messagebox.showerror(
                "Erreur", f"Impossible de charger le fichier GEDCOM :\n{e}"
            )
            return

        base_path = os.path.dirname(filename)
        self.object_view.set_base_path(base_path)
        logger.info("Base de chemins multimédia définie sur: %s", base_path)
        self._remember_recent_file(filename)
        self._clear_entity_views()
        self._nav_history = []
        self._nav_index = -1
        self._update_navigation_buttons()

        entity_types = self.controller.get_entity_types()
        if not entity_types:
            logger.warning("Aucune entité trouvée dans %s", filename)
            messagebox.showerror("Erreur", "Aucune entité trouvée")
            return

        self.entity_type_var.set(entity_types[0])

        self._update_entity_type_tabs()

        self.list_entities()
        load_duration = time.perf_counter() - load_started_at
        logger.info(
            "GEDCOM chargé avec succès en %.3f s: %s",
            load_duration,
            filename,
        )

    def _clear_entity_views(self, keep_type=None):
        for entity_type, (view, tab) in self._entity_view_map.items():
            if entity_type == keep_type:
                tab.pack(fill="both", expand=True)
            else:
                tab.pack_forget()
                view.display(None)

    def _show_entity_view(self, entity_type, entity=None):
        if entity is not None and not getattr(entity, "pointer", None):
            entity = None

        for current_type, (view, tab) in self._entity_view_map.items():
            if current_type == entity_type:
                tab.pack(fill="both", expand=True)
                view.display(entity)
            else:
                tab.pack_forget()
                view.display(None)

    def _update_navigation_buttons(self):
        can_go_back = self._nav_index > 0
        can_go_forward = self._nav_index < len(self._nav_history) - 1

        self.back_button.state(("disabled",) if not can_go_back else ("!disabled",))
        self.forward_button.state(
            ("disabled",) if not can_go_forward else ("!disabled",)
        )
        total = len(self._nav_history)
        current = self._nav_index + 1 if self._nav_index >= 0 else 0
        self.history_status.config(text=f"Historique : {current}/{total}")

    def on_entity_type_change(self, *args):
        entity_type = self.entity_type_var.get()
        self._update_entity_type_tab_state(entity_type)
        self._clear_entity_views(keep_type=entity_type)
        self.list_entities()
        if entity_type in self._entity_view_map:
            self._show_entity_view(entity_type, None)

    def _update_entity_type_tabs(self):
        for button in self._entity_type_buttons.values():
            button.destroy()
        self._entity_type_buttons = {}

        for row, (display, entity_type) in enumerate(
            self.controller.get_all_entity_type_menu_display_items()
        ):
            button = tk.Button(
                self.entity_type_tabs,
                text=display,
                command=lambda value=entity_type: self.entity_type_var.set(value),
                anchor="w",
                justify="left",
                padx=14,
                pady=9,
                relief="flat",
                bd=1,
                bg=COLORS["sidebar"],
                fg=COLORS["sidebar_text"],
                activebackground=COLORS["sidebar_hover"],
                activeforeground=COLORS["sidebar_active_text"],
                cursor="hand2",
                highlightthickness=0,
                font=("Segoe UI", 10, "bold"),
            )
            button.grid(row=row, column=0, sticky="ew", padx=6, pady=(0, 4))
            if row == 0:
                button.grid(pady=(4, 4))
            self._entity_type_buttons[entity_type] = button

        self._update_entity_type_tab_state(self.entity_type_var.get())

    def _update_entity_type_tab_state(self, selected_type):
        for entity_type, button in self._entity_type_buttons.items():
            is_selected = entity_type == selected_type
            has_entities = entity_type in self.controller.get_entity_types()
            button.config(
                relief="solid" if is_selected else "flat",
                borderwidth=2 if is_selected else 1,
                bg=(
                    COLORS["sidebar_active"] if is_selected else COLORS["sidebar"]
                ),
                fg=(
                    COLORS["sidebar_active_text"]
                    if is_selected
                    else COLORS["sidebar_text"]
                ),
                padx=14,
                pady=9,
            )
            if is_selected:
                button.config(
                    fg=COLORS["sidebar_active_text"],
                    bg=COLORS["sidebar_active"],
                    highlightbackground=COLORS["selection"],
                    highlightcolor=COLORS["selection"],
                    activebackground=COLORS["sidebar_hover"],
                    activeforeground=COLORS["sidebar_active_text"],
                )
            elif not has_entities:
                button.config(
                    fg=COLORS["sidebar_text"],
                    bg=COLORS["sidebar"],
                    highlightbackground=COLORS["sidebar"],
                    highlightcolor=COLORS["sidebar"],
                    activebackground=COLORS["sidebar_hover"],
                    activeforeground=COLORS["sidebar_active_text"],
                )
            else:
                button.config(
                    fg=COLORS["sidebar_text"],
                    bg=COLORS["sidebar"],
                    highlightbackground=COLORS["sidebar"],
                    highlightcolor=COLORS["sidebar"],
                    activebackground=COLORS["sidebar_hover"],
                    activeforeground=COLORS["sidebar_active_text"],
                )

    def _sort_entity_tree(self, column):
        if self._entity_sort_column == column:
            self._entity_sort_reverse = not self._entity_sort_reverse
        else:
            self._entity_sort_column = column
            self._entity_sort_reverse = False

        entity_type = self.entity_type_var.get()
        rows = []
        for item_id in self.entity_tree.get_children():
            values = self.entity_tree.item(item_id, "values")
            entity = self._entity_by_item_id[item_id]
            rows.append(
                (
                    item_id,
                    values,
                    entity,
                    self.controller.get_entity_sort_key(entity, entity_type, column),
                )
            )

        rows.sort(
            key=lambda row: row[3],
            reverse=self._entity_sort_reverse,
        )

        self.filtered_entities = [entity for _, _, entity, _ in rows]
        self._entity_by_item_id = {
            item_id: entity for item_id, _, entity, _ in rows
        }
        for index, (item_id, _, _, _) in enumerate(rows):
            self.entity_tree.move(item_id, "", index)

    def open_recent_file(self, filename):
        self._load_file_from_path(filename)

    def open_validated_file(self):
        filename = filedialog.askopenfilename(
            title="Choisir un fichier GEDCOM à valider",
            filetypes=[("GEDCOM files", "*.ged")],
            **self._file_dialog_options(),
        )
        if not filename:
            return

        self._load_file_from_path(filename, strict=True)

    def load_file(self):
        filename = filedialog.askopenfilename(
            title="Choisir un fichier GEDCOM",
            filetypes=[("GEDCOM files", "*.ged")],
            **self._file_dialog_options(),
        )
        if not filename:
            return

        self._load_file_from_path(filename)

    def list_entities(self):
        if not self.controller.is_loaded():
            return

        entity_type = self.entity_type_var.get()
        self.entity_tree.delete(*self.entity_tree.get_children())
        self._entity_by_item_id = {}
        self.filtered_entities = []

        if entity_type not in self.controller.get_entity_types():
            self.entity_tree.insert(
                "",
                "end",
                iid="empty",
                values=("Aucune entité de ce type", "—"),
            )
            self._show_entity_view(entity_type, None)
            self._display_raw_text("")
            return

        items = self.controller.get_entity_list_items(entity_type)
        self.filtered_entities = [entity for entity, _ in items]

        if not items:
            self.entity_tree.insert(
                "",
                "end",
                iid="empty",
                values=("Aucune entité de ce type", "—"),
            )
            self._show_entity_view(entity_type, None)
            self._display_raw_text("")
            return

        for index, (entity, _) in enumerate(items):
            item_id = str(index)
            self._entity_by_item_id[item_id] = entity
            self.entity_tree.insert(
                "",
                "end",
                iid=item_id,
                values=(
                    self.controller.format_entity_display_name(entity, entity_type),
                    getattr(entity, "pointer", "") or "—",
                ),
            )

    def filter_entities(self, *args):
        if not self.controller.is_loaded():
            return

        entity_type = self.entity_type_var.get()
        query = self.search_var.get()
        self.entity_tree.delete(*self.entity_tree.get_children())
        self._entity_by_item_id = {}
        self.filtered_entities = []

        if entity_type not in self.controller.get_entity_types():
            self.entity_tree.insert(
                "",
                "end",
                iid="empty",
                values=("Aucune entité de ce type", "—"),
            )
            self._show_entity_view(entity_type, None)
            self._display_raw_text("")
            return

        items = self.controller.get_entity_list_items(entity_type, query)
        self.filtered_entities = [entity for entity, _ in items]

        if not items:
            self.entity_tree.insert(
                "",
                "end",
                iid="empty",
                values=("Aucune entité de ce type", "—"),
            )
            self._show_entity_view(entity_type, None)
            self._display_raw_text("")
            return

        for index, (entity, _) in enumerate(items):
            item_id = str(index)
            self._entity_by_item_id[item_id] = entity
            self.entity_tree.insert(
                "",
                "end",
                iid=item_id,
                values=(
                    self.controller.format_entity_display_name(entity, entity_type),
                    getattr(entity, "pointer", "") or "—",
                ),
            )

    def show_entity(self, event):
        selection = self.entity_tree.selection()
        if not selection:
            return
        if not self.controller.is_loaded():
            return

        item_id = selection[0]
        if item_id == "empty":
            self._show_entity_view(self.entity_type_var.get(), None)
            self._display_raw_text("")
            return

        entity = self._entity_by_item_id.get(item_id)
        if entity is None:
            return
        context = self.controller.get_entity_display_info(entity)
        self.display_entity_context(context)

    def _display_raw_text(self, content):
        self.text_area.config(state="normal")
        try:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, content)
        finally:
            self.text_area.config(state="disabled")

    def show_header(self):
        if not self.controller.is_loaded():
            return

        block = self.controller.extract_head()
        if not block:
            messagebox.showerror("Erreur", "Aucun en-tête HEAD trouvé dans le fichier.")
            return

        self._display_raw_text(block)
        self.highlighter.highlight()

    def show_trailer(self):
        if not self.controller.is_loaded():
            return

        block = self.controller.extract_trailer()
        if not block:
            messagebox.showerror("Erreur", "Aucun bloc TRLR trouvé dans le fichier.")
            return

        self._display_raw_text(block)
        self.highlighter.highlight()

    def _record_navigation(self, context):
        if not context or not context.get("entity"):
            return

        pointer = getattr(context["entity"], "pointer", None)
        if not pointer:
            return

        current_pointer = None
        if self._nav_index >= 0 and self._nav_history:
            current_pointer = getattr(
                self._nav_history[self._nav_index]["entity"], "pointer", None
            )

        if current_pointer == pointer:
            return

        if self._nav_index < len(self._nav_history) - 1:
            self._nav_history = self._nav_history[: self._nav_index + 1]

        self._nav_history.append(context)
        self._nav_index = len(self._nav_history) - 1
        self._update_navigation_buttons()

    def navigate_to(self, pointer):
        if not self.controller.is_loaded():
            messagebox.showerror("Erreur", "Aucune session chargée.")
            return

        target = self.controller.resolve_pointer(pointer)
        if target is None:
            messagebox.showerror("Erreur", f"Entité introuvable : {pointer}")
            return

        context = self.controller.get_entity_display_info(target)
        self._record_navigation(context)
        self.display_entity_context(context)

    def go_back(self):
        if self._nav_index <= 0:
            return

        self._nav_index -= 1
        context = self._nav_history[self._nav_index]
        self.display_entity_context(context)
        self._update_navigation_buttons()

    def go_forward(self):
        if self._nav_index >= len(self._nav_history) - 1:
            return

        self._nav_index += 1
        context = self._nav_history[self._nav_index]
        self.display_entity_context(context)
        self._update_navigation_buttons()

    def display_entity_context(self, context):
        display_type_map = {
            "individual": "INDI",
            "family": "FAM",
            "repository": "REPO",
            "source": "SOUR",
            "note": "NOTE",
            "object": "OBJE",
            "submitter": "SUBM",
        }

        self._record_navigation(context)

        entity_type = display_type_map.get(context["type"])
        if entity_type is not None:
            self._show_entity_view(entity_type, context["entity"])
        else:
            self._clear_entity_views()

        if context.get("raw_block") is not None:
            self._display_raw_text(context["raw_block"])
            self.highlighter.highlight()
