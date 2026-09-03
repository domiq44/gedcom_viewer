import logging
import os
import tempfile
import tkinter as tk
from tkinter import ttk

from ui.views.link_utils import configure_label, configure_text_widget

logger = logging.getLogger(__name__)

try:
    from PIL import Image
except ImportError:
    Image = None


class MultimediaView(ttk.Frame):
    """
    Affiche une fiche multimédia pour les entités OBJE.
    """

    def __init__(self, parent, on_pointer_click):
        super().__init__(parent)

        self.on_pointer_click_callback = on_pointer_click
        self.configure(padding=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#f7f7f7")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.content_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw"
        )
        self.content_frame.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._sync_canvas_width)

        self.title_label = ttk.Label(
            self.content_frame, text="Multimédia", font=("Segoe UI", 12, "bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.preview_label = tk.Label(
            self.content_frame,
            text="Prévisualisation indisponible",
            relief="sunken",
            justify="center",
            anchor="center",
            bg="#f7f7f7",
        )
        self.preview_label.grid(
            row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10)
        )

        self.labels = {}
        fields = [
            ("Fichier", "file"),
            ("Titre", "title"),
            ("Format", "format"),
            ("Note", "note"),
        ]

        for i, (label_text, key) in enumerate(fields, start=2):
            ttk.Label(self.content_frame, text=label_text + " :").grid(
                row=i, column=0, sticky="w"
            )
            if key == "note":
                text_frame = ttk.Frame(self.content_frame, padding=(2, 2, 2, 2))
                text_frame.grid(row=i, column=1, sticky="nsew", padx=10)
                scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
                scrollbar.pack(side="right", fill="y")
                value_widget = tk.Text(
                    text_frame,
                    width=50,
                    height=6,
                    wrap="word",
                    font=("Segoe UI", 10),
                    yscrollcommand=scrollbar.set,
                    relief="sunken",
                    bd=1,
                    bg="#fafafa",
                    padx=6,
                    pady=6,
                )
                value_widget.pack(side="left", fill="both", expand=True)
                scrollbar.config(command=value_widget.yview)
                value_widget.config(state="disabled")
            else:
                value_widget = ttk.Label(
                    self.content_frame, text="", font=("Segoe UI", 10)
                )
                value_widget.grid(row=i, column=1, sticky="w", padx=10)
            self.labels[key] = value_widget

        self.content_frame.grid_columnconfigure(1, weight=1)
        for i in range(len(fields) + 2):
            self.content_frame.grid_rowconfigure(i, pad=4)

        self._preview_photo = None
        self.base_path = None

    def _sync_canvas_width(self, event=None):
        canvas_width = max(event.width, 1) if event else self.canvas.winfo_width()
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        self._update_scrollregion()

    def _update_scrollregion(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def set_base_path(self, base_path):
        self.base_path = base_path if base_path and os.path.isdir(base_path) else None

    def _show_preview_placeholder(self, reason="Prévisualisation indisponible"):
        logger.info("Prévisualisation non disponible: %s", reason)
        self.preview_label.config(text=reason)
        self.preview_label.configure(image="")
        self._preview_photo = None

    def _show_preview(self, file_path):
        if not file_path:
            self._show_preview_placeholder("Aucun chemin multimédia fourni")
            return

        candidates = [file_path]
        if self.base_path:
            candidates.append(os.path.join(self.base_path, file_path))

        resolved_path = None
        for candidate in candidates:
            if os.path.isabs(candidate):
                if os.path.isfile(candidate):
                    resolved_path = candidate
                    break
            else:
                absolute_candidate = os.path.abspath(candidate)
                if os.path.isfile(absolute_candidate):
                    resolved_path = absolute_candidate
                    break

        if resolved_path is None:
            self._show_preview_placeholder(
                f"Fichier introuvable parmi les chemins testés: {candidates}"
            )
            return

        logger.info("Tentative d’affichage preview pour %s", resolved_path)
        if Image is None:
            self._show_preview_placeholder(
                "Pillow indisponible pour la prévisualisation"
            )
            return

        try:
            with Image.open(resolved_path) as image:
                image = image.convert("RGB")
                max_width = 640
                max_height = 480
                image.thumbnail((max_width, max_height))

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    temp_path = tmp.name

                try:
                    image.save(temp_path, format="PNG")
                    photo = tk.PhotoImage(file=temp_path)
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
        except Exception as exc:
            logger.exception("Échec du chargement de l’image %s", resolved_path)
            self._show_preview_placeholder(f"Impossible d’ouvrir l’image: {exc}")
            return

        self._preview_photo = photo
        self.preview_label.image = photo
        self.preview_label.configure(text="", image=photo)

    def display(self, media):
        if not media:
            self.title_label.config(text="Multimédia")
            self._show_preview_placeholder()
            for key, widget in self.labels.items():
                if isinstance(widget, tk.Text):
                    configure_text_widget(widget, "")
                else:
                    configure_label(widget, "")
            return

        self.title_label.config(text=f"Multimédia : {media.pointer}")
        for key, widget in self.labels.items():
            value = getattr(media, key, "")
            if key == "note":
                configure_text_widget(widget, value)
            else:
                configure_label(widget, value)

        self._show_preview(getattr(media, "file", None))

    def on_pointer_click(self, pointer):
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)
