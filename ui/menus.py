import tkinter as tk
from tkinter import messagebox, filedialog

class MenuBar:
    def __init__(self, root, app):
        """
        root = fenêtre Tk
        app = instance de GedcomViewer (pour appeler load_file et show_header)
        """
        self.root = root
        self.app = app

        menubar = tk.Menu(root)

        # --- MENU FICHIER ---
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Ouvrir un fichier GEDCOM", command=self.app.load_file)

        # Nouvelle entrée : afficher l'en-tête HEAD
        file_menu.add_command(label="Afficher l'en-tête GEDCOM", command=self.app.show_header)

        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit_app)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        # --- MENU AIDE ---
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="À propos", command=self.show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)

        root.config(menu=menubar)

    def quit_app(self):
        self.root.quit()

    def show_about(self):
        messagebox.showinfo(
            "À propos",
            "GEDCOM Viewer 5.5.1\nDéveloppé avec Python et Tkinter\n© 2026"
        )
