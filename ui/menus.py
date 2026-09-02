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
        file_menu.add_command(
            label="Ouvrir un fichier GEDCOM", command=self.app.load_file
        )

        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Récents", menu=self.recent_menu)
        self.refresh_recent_menu()

        file_menu.add_command(
            label="Afficher l'en-tête GEDCOM", command=self.app.show_header
        )
        file_menu.add_command(
            label="Afficher le bloc TRLR", command=self.app.show_trailer
        )
        file_menu.add_separator()
        file_menu.add_command(label="Précédent", command=self.app.go_back)
        file_menu.add_command(label="Suivant", command=self.app.go_forward)

        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit_app)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        # --- MENU AIDE ---
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="À propos", command=self.show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)

        root.config(menu=menubar)

    def refresh_recent_menu(self):
        self.recent_menu.delete(0, "end")
        if not getattr(self.app, "recent_files", None):
            self.recent_menu.add_command(label="Aucun fichier récent")
            return

        for filename in self.app.recent_files:
            self.recent_menu.add_command(
                label=filename,
                command=lambda path=filename: self.app.open_recent_file(path),
            )

    def quit_app(self):
        self.root.quit()

    def show_about(self):
        messagebox.showinfo(
            "À propos", "GEDCOM Viewer 5.5.1\nDéveloppé avec Python et Tkinter\n© 2026"
        )
