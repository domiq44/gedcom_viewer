import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from app.use_cases.load_gedcom import load_gedcom

from ui.menus import MenuBar
from ui.syntax_highlighter import GedcomHighlighter
from ui.views.individual_view import IndividualView
from ui.views.family_view import FamilyView

ENTITY_LABELS = {
    "INDI": "Individu",
    "FAM": "Famille",
    "OBJE": "Multimédia",
    "NOTE": "Note",
    "SOUR": "Source",
    "SUBM": "Fournisseur d'information",
    "REPO": "Dépôt"
}


class GedcomViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("GEDCOM Viewer 5.5.1")

        MenuBar(self.root, self)

        # Session applicative (parser + index + modèles)
        self.session = None

        # --- PANED WINDOW PRINCIPAL ---
        main_pane = tk.PanedWindow(root, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # --- FRAME GAUCHE ---
        left_frame = tk.Frame(main_pane)
        main_pane.add(left_frame, minsize=250)

        # Type d'entité
        tk.Label(left_frame, text="Type d'entité :").grid(row=0, column=0, sticky="w")
        self.entity_type_var = tk.StringVar()
        self.entity_type_var.trace_add("write", self.on_entity_type_change)
        self.entity_type_menu = tk.OptionMenu(left_frame, self.entity_type_var, "")
        self.entity_type_menu.grid(row=1, column=0, sticky="w")

        # Barre de recherche
        tk.Label(left_frame, text="Recherche :").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_entities)
        self.search_entry = tk.Entry(left_frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=3, column=0, sticky="w")

        # Liste des entités
        tk.Label(left_frame, text="Entités :").grid(row=4, column=0, sticky="w", pady=(10, 0))
        self.entity_listbox = tk.Listbox(left_frame, width=40, height=20)
        self.entity_listbox.grid(row=5, column=0, sticky="nsew")
        self.entity_listbox.bind("<<ListboxSelect>>", self.show_entity)

        left_frame.grid_rowconfigure(5, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # --- FRAME DROITE ---
        right_frame = tk.Frame(main_pane)
        main_pane.add(right_frame)

        # Notebook (onglets)
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        tk.Label(right_frame, text="Contenu GEDCOM :").grid(row=0, column=0, sticky="nw")
        self.gedcom_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.gedcom_frame, text="GEDCOM brut")

        self.text_area = tk.Text(self.gedcom_frame, width=70, height=30)
        self.text_area.pack(fill="both", expand=True)

        # Vue fiche individu
        self.individual_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.individual_tab, text="Individu")

        self.individual_view = IndividualView(self.individual_tab, self)
        self.individual_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.highlighter = GedcomHighlighter(self.text_area)

        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)

        # Onglet Famille
        self.family_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.family_tab, text="Famille")

        self.family_view = FamilyView(self.family_tab, self)
        self.family_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.filtered_entities = []

    # -----------------------------
    # Déclenchement automatique quand le type change
    # -----------------------------
    def on_entity_type_change(self, *args):
        if not self.entity_type_var.get().startswith("INDI"):
            self.hide_individual_view()

        self.list_entities()

    # -----------------------------
    # Charger un fichier GEDCOM
    # -----------------------------
    def load_file(self):
        filename = filedialog.askopenfilename(
            title="Choisir un fichier GEDCOM",
            filetypes=[("GEDCOM files", "*.ged")]
        )
        if not filename:
            return

        try:
            self.session = load_gedcom(filename)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le fichier GEDCOM :\n{e}")
            return

        self.hide_individual_view()

        ordered_types = list(ENTITY_LABELS.keys())
        types = [t for t in ordered_types if t in self.session.parser.entities]

        if not types:
            messagebox.showerror("Erreur", "Aucune entité trouvée")
            return

        self.entity_type_var.set(types[0])

        menu = self.entity_type_menu["menu"]
        menu.delete(0, "end")

        for t in types:
            label = ENTITY_LABELS.get(t, "Type inconnu")
            display = f"{t} – {label}"
            menu.add_command(label=display, command=lambda v=t: self.entity_type_var.set(v))

        messagebox.showinfo("OK", "Fichier GEDCOM chargé")

    # -----------------------------
    # Lister les entités du type choisi
    # -----------------------------
    def list_entities(self):
        if not self.session:
            return

        entity_type = self.entity_type_var.get().split(" – ")[0]
        self.entity_listbox.delete(0, tk.END)

        if entity_type == "INDI":
            self.current_entities = self.session.list_individuals()
        else:
            self.current_entities = self.session.parser.entities.get(entity_type, [])

        self.filtered_entities = list(self.current_entities)

        for entity in self.filtered_entities:
            label = getattr(entity, "pointer", None) or "(sans pointeur)"
            self.entity_listbox.insert(tk.END, label)

    # -----------------------------
    # Filtrer les entités
    # -----------------------------
    def filter_entities(self, *args):
        if not self.session:
            return

        query = self.search_var.get().lower()
        self.entity_listbox.delete(0, tk.END)

        if self.entity_type_var.get().startswith("INDI"):
            self.filtered_entities = self.session.search_individuals(query)
        else:
            self.filtered_entities = [
                e for e in self.current_entities
                if getattr(e, "pointer", "") and query in e.pointer.lower()
            ]

        for entity in self.filtered_entities:
            label = getattr(entity, "pointer", None) or "(sans pointeur)"
            self.entity_listbox.insert(tk.END, label)

    # -----------------------------
    # Afficher le bloc GEDCOM brut
    # -----------------------------
    def show_entity(self, event):
        if not self.entity_listbox.curselection():
            return
        if not self.session:
            return

        index = self.entity_listbox.curselection()[0]
        entity = self.filtered_entities[index]

        raw_entity = None

        # INDIVIDU : entity est un Individual
        if getattr(entity, "entity", None) is not None and entity.entity.tag == "INDI":
            self.individual_view.display(entity)
            self.notebook.select(self.individual_tab)
            raw_entity = entity.entity

        # FAMILLE : dans ta listbox, pour FAM (hors INDI) tu mets des GedcomEntity bruts
        elif getattr(entity, "tag", None) == "FAM":
            fam = self.session.get_family(getattr(entity, "pointer", None))
            self.family_view.display(fam)
            self.notebook.select(self.family_tab)
            raw_entity = fam.entity if fam else entity

        # AUTRES : entity est un GedcomEntity brut
        else:
            self.individual_view.display(None)
            self.family_view.display(None)
            self.notebook.select(self.gedcom_frame)
            raw_entity = entity

        if raw_entity is not None:
            block = raw_entity.raw_block()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, block)
            self.highlighter.highlight()

    # -----------------------------
    # Afficher le bloc d'en-tête GEDCOM (0 HEAD)
    # -----------------------------
    def show_header(self):
        if not self.session:
            return

        block = self.session.extract_head()

        if not block:
            messagebox.showerror("Erreur", "Aucun en-tête HEAD trouvé dans le fichier.")
            return

        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, block)
        self.highlighter.highlight()

    def hide_individual_view(self):
        self.individual_view.display(None)

    def navigate_to(self, pointer):
        if not self.session:
            messagebox.showerror("Erreur", "Aucune session chargée.")
            return

        if pointer in self.session.individuals:
            ind = self.session.individuals[pointer]
            self.individual_view.display(ind)
            self.notebook.select(self.individual_tab)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, ind.entity.raw_block())
            self.highlighter.highlight()
            return

        if pointer in self.session.families:
            fam = self.session.families[pointer]
            self.family_view.display(fam)
            self.notebook.select(self.family_tab)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, fam.entity.raw_block())
            self.highlighter.highlight()
            return

        messagebox.showerror("Erreur", f"Impossible de trouver l'entité {pointer}")
