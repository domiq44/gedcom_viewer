from operator import index
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from gedcom.parser import GedcomParser
from ui.menus import MenuBar
from ui.syntax_highlighter import GedcomHighlighter

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

        # Barre de menus
        MenuBar(self.root, self)

        # Parser GEDCOM
        self.parser = GedcomParser()

        # --- PANED WINDOW PRINCIPAL (séparateur déplaçable) ---
        main_pane = tk.PanedWindow(root, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # --- FRAME GAUCHE ---
        left_frame = tk.Frame(main_pane)
        main_pane.add(left_frame, minsize=250)  # largeur minimale

        # Type d'entité
        tk.Label(left_frame, text="Type d'entité :").grid(row=0, column=0, sticky="w")
        self.entity_type_var = tk.StringVar()
        self.entity_type_var.trace_add("write", self.on_entity_type_change)
        self.entity_type_menu = tk.OptionMenu(left_frame, self.entity_type_var, "")
        self.entity_type_menu.grid(row=1, column=0, sticky="w")

        # Barre de recherche
        tk.Label(left_frame, text="Recherche (identifiants) :").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_entities)
        self.search_entry = tk.Entry(left_frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=3, column=0, sticky="w")

        # Liste des entités
        tk.Label(left_frame, text="Entités :").grid(row=4, column=0, sticky="w", pady=(10, 0))
        self.entity_listbox = tk.Listbox(left_frame, width=40, height=20)
        self.entity_listbox.grid(row=5, column=0, sticky="nsew")
        self.entity_listbox.bind("<<ListboxSelect>>", self.show_entity)

        # Rendre la liste extensible verticalement
        left_frame.grid_rowconfigure(5, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # --- FRAME DROITE ---
        right_frame = tk.Frame(main_pane)
        main_pane.add(right_frame)

        tk.Label(right_frame, text="Contenu GEDCOM :").grid(row=0, column=0, sticky="nw")
        self.text_area = tk.Text(right_frame, width=70, height=30)
        self.text_area.grid(row=1, column=0, sticky="nsew")

        self.highlighter = GedcomHighlighter(self.text_area)

        # Rendre la zone droite extensible
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)

        # Liste filtrée
        self.filtered_entities = []

    # -----------------------------
    # Déclenchement automatique quand le type change
    # -----------------------------
    def on_entity_type_change(self, *args):
        self.list_entities()

    # -----------------------------
    # Charger un fichier GEDCOM
    # -----------------------------
    def load_file(self):
        filename = filedialog.askopenfilename(
            title="Choisir un fichier GEDCOM",
            filetypes=[("GEDCOM files", "*.ged"), ("All files", "*.*")]
        )
        if not filename:
            return

        self.parser.load(filename)

        # Ordre imposé
        ordered_types = list(ENTITY_LABELS.keys())
        types = [t for t in ordered_types if t in self.parser.entities]

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
        entity_type = self.entity_type_var.get().split(" – ")[0]
        self.entity_listbox.delete(0, tk.END)

        if entity_type not in self.parser.entities:
            return

        self.current_entities = self.parser.entities[entity_type]
        self.filtered_entities = list(self.current_entities)

        self.entity_listbox.delete(0, tk.END)

        for entity in self.filtered_entities:
            label = entity.pointer or f"(sans pointeur @ {entity.start_index})"
            self.entity_listbox.insert(tk.END, label)


    # -----------------------------
    # Filtrer les entités
    # -----------------------------
    def filter_entities(self, *args):
        query = self.search_var.get().lower()

        self.entity_listbox.delete(0, tk.END)

        self.filtered_entities = [
            e for e in self.current_entities
            if e.pointer and query in e.pointer.lower()
        ]

        for entity in self.filtered_entities:
            label = entity.pointer or f"(sans pointeur @ {entity.start_index})"
            self.entity_listbox.insert(tk.END, label)

    # -----------------------------
    # Afficher le bloc GEDCOM brut
    # -----------------------------
    def show_entity(self, event):
        if not self.entity_listbox.curselection():
            return

        index = self.entity_listbox.curselection()[0]
        entity = self.filtered_entities[index]
        
        block = entity.raw_block()

        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, block)

        # Coloration syntaxique
        self.highlighter.highlight()

    # -----------------------------
    # Afficher le bloc d'en-tête GEDCOM (0 HEAD)
    # -----------------------------
    def show_header(self):
        """
        Affiche le bloc HEAD extrait par le parser.
        """
        block = self.parser.extract_head()

        if not block:
            messagebox.showerror("Erreur", "Aucun en-tête HEAD trouvé dans le fichier.")
            return

        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, block)
        self.highlighter.highlight()
