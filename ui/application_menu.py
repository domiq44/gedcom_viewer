import tkinter as tk
from tkinter import messagebox

from ui.i18n import SUPPORTED_LANGUAGES


class ApplicationMenu:
    """Barre de menu de l’application, séparée de la logique de fenêtre."""

    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.language_var = None
        self.recent_menu = None
        self.file_menu = None
        self.inspect_menu = None
        self.navigation_menu = None
        self._build()

    def _build(self):
        menubar = tk.Menu(self.root)
        tr = self.app.translator.get

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=tr("menu.open"), command=self.app.load_file)
        file_menu.add_command(
            label=tr("menu.open_validate"),
            command=self.app.open_validated_file,
        )
        file_menu.add_command(
            label=tr("menu.close_file"),
            command=self.app.close_file,
            state=tk.DISABLED,
        )
        self.file_menu = file_menu
        self.close_file_index = file_menu.index("end")

        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label=tr("menu.recent"), menu=self.recent_menu)
        self.recent_index = file_menu.index("end")
        self.refresh_recent_menu()
        file_menu.add_command(
            label=tr("menu.clear_recent"),
            command=self.clear_recent_files,
            state=tk.DISABLED,
        )
        self.clear_recent_index = file_menu.index("end")

        file_menu.add_separator()

        inspect_menu = tk.Menu(file_menu, tearoff=0)
        inspect_menu.add_command(label=tr("menu.header"), command=self.app.show_header)
        inspect_menu.add_command(
            label=tr("menu.trailer"), command=self.app.show_trailer
        )
        file_menu.add_cascade(label=tr("menu.inspect"), menu=inspect_menu)
        self.inspect_menu = inspect_menu
        self.inspect_index = file_menu.index("end")
        self.file_menu.entryconfigure(self.inspect_index, state=tk.DISABLED)

        file_menu.add_separator()
        navigation_menu = tk.Menu(file_menu, tearoff=0)
        navigation_menu.add_command(
            label=tr("menu.previous"), command=self.app.go_back, state=tk.DISABLED
        )
        navigation_menu.add_command(
            label=tr("menu.next"), command=self.app.go_forward, state=tk.DISABLED
        )
        file_menu.add_cascade(label=tr("menu.navigation"), menu=navigation_menu)
        self.navigation_menu = navigation_menu
        self.navigation_index = file_menu.index("end")
        self.file_menu.entryconfigure(self.navigation_index, state=tk.DISABLED)

        file_menu.add_separator()
        file_menu.add_command(label=tr("menu.quit"), command=self.quit_app)
        menubar.add_cascade(label=tr("menu.file"), menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=tr("menu.about"), command=self.show_about)
        language_menu = tk.Menu(help_menu, tearoff=0)
        self.language_var = tk.StringVar(value=self.app.translator.language)
        for language, label in SUPPORTED_LANGUAGES.items():
            language_menu.add_radiobutton(
                label=label,
                value=language,
                variable=self.language_var,
                command=lambda value=language: self.app.set_language(value),
            )
        help_menu.add_cascade(label=tr("menu.language"), menu=language_menu)
        menubar.add_cascade(label=tr("menu.help"), menu=help_menu)

        self.root.config(menu=menubar)

    def refresh_recent_menu(self):
        self.recent_menu.delete(0, "end")
        recent_files = getattr(self.app, "recent_files", None)
        if not recent_files:
            self.recent_menu.add_command(
                label=self.app.translator.get("menu.no_recent")
            )
        else:
            for filename in recent_files:
                self.recent_menu.add_command(
                    label=filename,
                    command=lambda path=filename: self.app.open_recent_file(path),
                )
        self._update_recent_menu_state()

    def _update_recent_menu_state(self):
        enabled = bool(getattr(self.app, "recent_files", None))
        state = tk.NORMAL if enabled else tk.DISABLED
        if hasattr(self, "recent_index"):
            self.file_menu.entryconfigure(self.recent_index, state=state)
        if hasattr(self, "clear_recent_index"):
            self.file_menu.entryconfigure(self.clear_recent_index, state=state)

    def refresh_state(self):
        controller = getattr(self.app, "controller", None)
        is_loaded = controller is not None and controller.is_loaded()
        state = tk.NORMAL if is_loaded else tk.DISABLED
        self.file_menu.entryconfigure(self.close_file_index, state=state)
        self.file_menu.entryconfigure(self.inspect_index, state=state)
        self.file_menu.entryconfigure(self.navigation_index, state=state)

        history = getattr(self.app, "_navigation_history", None)
        self.navigation_menu.entryconfigure(
            0,
            state=(
                tk.NORMAL
                if is_loaded and history and history.can_go_back
                else tk.DISABLED
            ),
        )
        self.navigation_menu.entryconfigure(
            1,
            state=(
                tk.NORMAL
                if is_loaded and history and history.can_go_forward
                else tk.DISABLED
            ),
        )
        self._update_recent_menu_state()

    def clear_recent_files(self):
        if not getattr(self.app, "recent_files", None):
            return

        confirmed = messagebox.askyesno(
            self.app.translator.get("menu.clear_recent_title"),
            self.app.translator.get("menu.clear_recent_confirm"),
            parent=self.root,
        )
        if confirmed:
            self.app.clear_recent_files()

    def quit_app(self):
        self.root.quit()

    def show_about(self):
        messagebox.showinfo(
            self.app.translator.get("menu.about"),
            self.app.translator.get("menu.about_text"),
        )
