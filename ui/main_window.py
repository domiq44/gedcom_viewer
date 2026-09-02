import json
import logging
import os
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


class GedcomViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("GEDCOM Viewer 5.5.1")

        self.recent_files = self._load_recent_files()
        self.menu_bar = MenuBar(self.root, self)
        self.controller = AppController()
        self.filtered_entities = []
        self._nav_history = []
        self._nav_index = -1

        # --- PANED WINDOW PRINCIPAL ---
        main_pane = tk.PanedWindow(root, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # --- FRAME GAUCHE ---
        left_frame = tk.Frame(main_pane)
        main_pane.add(left_frame, minsize=250)

        tk.Label(left_frame, text="Type d'entité :").grid(row=0, column=0, sticky="w")
        self.entity_type_var = tk.StringVar()
        self.entity_type_var.trace_add("write", self.on_entity_type_change)
        self.entity_type_menu = tk.OptionMenu(left_frame, self.entity_type_var, "")
        self.entity_type_menu.grid(row=1, column=0, sticky="w")

        tk.Label(left_frame, text="Recherche :").grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_entities)
        self.search_entry = tk.Entry(left_frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=3, column=0, sticky="w")

        tk.Label(left_frame, text="Entités :").grid(
            row=4, column=0, sticky="w", pady=(10, 0)
        )
        self.entity_listbox = tk.Listbox(
            left_frame,
            width=40,
            height=20,
            font=("Consolas", 10),
        )
        self.entity_listbox.grid(row=5, column=0, sticky="nsew")
        self.entity_listbox.bind("<<ListboxSelect>>", self.show_entity)

        left_frame.grid_rowconfigure(5, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # --- FRAME DROITE ---
        right_frame = tk.Frame(main_pane)
        main_pane.add(right_frame)

        self.nav_toolbar = ttk.Frame(right_frame)
        self.nav_toolbar.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.back_button = ttk.Button(
            self.nav_toolbar, text="← Précédent", command=self.go_back
        )
        self.back_button.pack(side="left")

        self.forward_button = ttk.Button(
            self.nav_toolbar, text="Suivant →", command=self.go_forward
        )
        self.forward_button.pack(side="left", padx=(5, 0))

        self.history_status = tk.Label(
            self.nav_toolbar,
            text="Historique : 0/0",
            foreground="#666666",
            font=("TkDefaultFont", 9),
        )
        self.history_status.pack(side="left", padx=(10, 0))

        # Séparateur visuel
        separator = tk.Label(self.nav_toolbar, text=" | ", foreground="#cccccc")
        separator.pack(side="left", padx=(10, 5))

        # Boutons pour accéder à l'en-tête et au trailer du fichier
        self.header_button = ttk.Button(
            self.nav_toolbar, text="📄 En-tête", command=self.show_header
        )
        self.header_button.pack(side="left", padx=(0, 5))

        self.trailer_button = ttk.Button(
            self.nav_toolbar, text="🔚 Fin du fichier", command=self.show_trailer
        )
        self.trailer_button.pack(side="left")

        self.status_var = tk.StringVar(value="Prêt")
        self.log_status_frame = tk.LabelFrame(
            right_frame,
            text="Dernière erreur log",
            padx=6,
            pady=4,
        )
        self.log_status_frame.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        self.status_label = tk.Label(
            self.log_status_frame,
            textvariable=self.status_var,
            foreground="#666666",
            font=("TkDefaultFont", 9),
            anchor="w",
        )
        self.status_label.pack(fill="x", expand=True)

        right_content = tk.PanedWindow(
            right_frame, orient="horizontal", sashrelief="raised", sashwidth=8
        )
        right_content.grid(row=1, column=0, sticky="nsew")

        self.gedcom_frame = tk.LabelFrame(right_content, text="GEDCOM", padx=8, pady=8)
        right_content.add(self.gedcom_frame, minsize=350)
        right_content.paneconfigure(self.gedcom_frame, stretch="always")

        tk.Label(self.gedcom_frame, text="Contenu brut du fichier :").pack(
            anchor="w", pady=(0, 5)
        )
        self.text_area = tk.Text(
            self.gedcom_frame,
            width=70,
            height=30,
            font=("Consolas", 10),
        )
        self.text_area.pack(fill="both", expand=True)

        self.entity_notebook_frame = tk.LabelFrame(
            right_content, text="Vue de l’entité", padx=8, pady=8
        )
        right_content.add(self.entity_notebook_frame, minsize=450)
        right_content.paneconfigure(self.entity_notebook_frame, stretch="always")

        self.notebook = ttk.Notebook(self.entity_notebook_frame)
        self.notebook.pack(fill="both", expand=True)

        self.individual_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.individual_tab, text="Individu")
        self.individual_view = IndividualView(self.individual_tab, self.navigate_to)
        self.individual_view.set_family_name_resolver(self.controller.get_family)
        self.individual_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.family_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.family_tab, text="Famille")
        self.family_view = FamilyView(self.family_tab, self.navigate_to)
        self.family_view.set_name_resolver(self.controller.get_individual)
        self.family_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.repo_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.repo_tab, text="Dépôt")
        self.repo_view = RepositoryView(self.repo_tab, self.navigate_to)
        self.repo_view.set_reference_resolver(self.controller.get_repository)
        self.repo_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.source_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.source_tab, text="Source")
        self.source_view = SourceView(self.source_tab, self.navigate_to)
        self.source_view.set_reference_resolver(self.controller.get_repository)
        self.source_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.note_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.note_tab, text="Note")
        self.note_view = NoteView(self.note_tab, self.navigate_to)
        self.note_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.object_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.object_tab, text="Multimédia")
        self.object_view = MultimediaView(self.object_tab, self.navigate_to)
        self.object_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.submitter_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.submitter_tab, text="Submitter")
        self.submitter_view = SubmitterView(self.submitter_tab, self.navigate_to)
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

        self.highlighter = GedcomHighlighter(self.text_area)
        self._attach_ui_log_handler()
        self._update_navigation_buttons()

        if self.recent_files:
            startup_file = self.recent_files[0]
            if os.path.isfile(startup_file):
                self._load_file_from_path(startup_file)

        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        self.entity_notebook_frame.grid_columnconfigure(0, weight=1)
        self.entity_notebook_frame.grid_rowconfigure(0, weight=1)

    def _attach_ui_log_handler(self):
        if hasattr(self, "_ui_log_handler"):
            return

        self._ui_log_handler = _UiLogHandler(self.status_var)
        self._ui_log_handler.setFormatter(
            logging.Formatter("%(levelname)s: %(message)s")
        )
        logging.getLogger().addHandler(self._ui_log_handler)

    def _load_recent_files(self):
        recent_path = os.path.expanduser("~/.gedcom_viewer_recent.json")
        if not os.path.isfile(recent_path):
            return []

        try:
            with open(recent_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, list):
                return [path for path in data if isinstance(path, str)]
        except Exception:
            return []
        return []

    def _save_recent_files(self):
        recent_path = os.path.expanduser("~/.gedcom_viewer_recent.json")
        try:
            with open(recent_path, "w", encoding="utf-8") as handle:
                json.dump(self.recent_files[:10], handle)
        except Exception:
            return

    def _remember_recent_file(self, filename):
        normalized = os.path.abspath(filename)
        if not normalized:
            return

        self.recent_files = [
            path for path in self.recent_files if os.path.abspath(path) != normalized
        ]
        self.recent_files.insert(0, normalized)
        self.recent_files = self.recent_files[:10]
        self._save_recent_files()
        if hasattr(self, "menu_bar"):
            self.menu_bar.refresh_recent_menu()

    def _load_file_from_path(self, filename):
        if not filename:
            return

        logger.info("Chargement du fichier GEDCOM: %s", filename)
        try:
            self.controller.load_file(filename)
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

        menu = self.entity_type_menu["menu"]
        menu.delete(0, "end")
        for (
            display,
            entity_type,
        ) in self.controller.get_entity_type_menu_display_items():
            menu.add_command(
                label=display,
                command=lambda value=entity_type: self.entity_type_var.set(value),
            )

        self.list_entities()
        logger.info("GEDCOM chargé avec succès: %s", filename)

    def _clear_entity_views(self, keep_type=None):
        for entity_type, (view, _) in self._entity_view_map.items():
            if entity_type != keep_type:
                view.display(None)

    def _show_entity_view(self, entity_type, entity=None):
        for current_type, (view, tab) in self._entity_view_map.items():
            if current_type == entity_type:
                view.display(entity)
                self.notebook.select(tab)
            else:
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
        self._clear_entity_views(keep_type=entity_type)
        self.list_entities()

    def open_recent_file(self, filename):
        self._load_file_from_path(filename)

    def load_file(self):
        filename = filedialog.askopenfilename(
            title="Choisir un fichier GEDCOM", filetypes=[("GEDCOM files", "*.ged")]
        )
        if not filename:
            return

        self._load_file_from_path(filename)

    def list_entities(self):
        if not self.controller.is_loaded():
            return

        entity_type = self.entity_type_var.get()
        self.entity_listbox.delete(0, tk.END)
        items = self.controller.get_entity_list_items(entity_type)
        self.filtered_entities = [entity for entity, _ in items]

        for _, label in items:
            self.entity_listbox.insert(tk.END, label)

    def filter_entities(self, *args):
        if not self.controller.is_loaded():
            return

        entity_type = self.entity_type_var.get()
        query = self.search_var.get()
        self.entity_listbox.delete(0, tk.END)

        items = self.controller.get_entity_list_items(entity_type, query)
        self.filtered_entities = [entity for entity, _ in items]

        for _, label in items:
            self.entity_listbox.insert(tk.END, label)

    def show_entity(self, event):
        if not self.entity_listbox.curselection():
            return
        if not self.controller.is_loaded():
            return

        index = self.entity_listbox.curselection()[0]
        entity = self.filtered_entities[index]
        context = self.controller.get_entity_display_info(entity)
        self.display_entity_context(context)

    def show_header(self):
        if not self.controller.is_loaded():
            return

        block = self.controller.extract_head()
        if not block:
            messagebox.showerror("Erreur", "Aucun en-tête HEAD trouvé dans le fichier.")
            return

        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, block)
        self.highlighter.highlight()

    def show_trailer(self):
        if not self.controller.is_loaded():
            return

        block = self.controller.extract_trailer()
        if not block:
            messagebox.showerror("Erreur", "Aucun bloc TRLR trouvé dans le fichier.")
            return

        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, block)
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
            if len(self._entity_view_map) > 0:
                first_tab = next(iter(self._entity_view_map.values()))[1]
                self.notebook.select(first_tab)

        if context.get("raw_block") is not None:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, context["raw_block"])
            self.highlighter.highlight()
