"""Vue de détail des objets multimédia."""

import os
import tkinter as tk

from ui.themes import COLORS
from ui.views.image_preview import ImagePreviewMixin
from ui.views.structured_property_view import StructuredPropertyView


class MultimediaPropertyView(ImagePreviewMixin, StructuredPropertyView):
    """Vue structurée des métadonnées et de l’aperçu d’un objet GEDCOM."""

    def __init__(
        self,
        parent,
        on_pointer_click,
        translator=None,
        entity_type="OBJE",
        tooltip_factory=None,
        base_path=None,
    ):
        """Initialise la vue des objets multimédia."""
        super().__init__(
            parent,
            on_pointer_click,
            translator,
            entity_type,
            title_key="view.multimedia",
            tooltip_factory=tooltip_factory,
        )
        self._init_image_preview()
        self.set_base_path(base_path)
        self.note_widget = None
        self._create_preview_label()

    def _create_preview_label(self):
        """Crée le libellé d'aperçu."""
        self.preview_label = tk.Label(
            self.content,
            text=self.translator.get("view.preview_unavailable"),
            relief="flat",
            justify="center",
            anchor="center",
            bg=COLORS["surface"],
        )
        self.preview_label.pack(fill="x", pady=(0, 8))
        self._bind_scroll_widget(self.preview_label)

    def display(self, multimedia):
        """Affiche un objet multimédia."""
        self._clear()
        self.note_widget = None
        self.title_label.configure(text=self.translator.get("view.multimedia"))
        self._create_preview_label()

        if multimedia is None:
            self._show_preview_placeholder()
            return

        self._display_title(multimedia)
        self._display_identity(multimedia)
        self._show_preview(getattr(multimedia, "file", None))
        self._display_details(multimedia)
        self._display_notes(multimedia)
        self._display_additional_fields(multimedia)

    def _display_title(self, multimedia):
        """Affiche le titre de l'objet multimédia."""
        display_title = self._multimedia_title(multimedia)
        self.title_label.configure(
            text=display_title or self.translator.get("view.multimedia")
        )

    def _multimedia_title(self, multimedia):
        """Retourne le titre affiché de l'objet multimédia."""
        title = getattr(multimedia, "title", None)
        if title:
            return title
        file_title = next(
            (
                record.get("title")
                for record in reversed(getattr(multimedia, "file_records", None) or [])
                if record.get("title")
            ),
            None,
        )
        file_path = getattr(multimedia, "file", None)
        return file_title or os.path.basename(file_path or "")

    def _display_details(self, multimedia):
        """Affiche les métadonnées de l'objet multimédia."""
        rows = self._detail_rows(multimedia)
        if not rows:
            return
        section = self._section(self.translator.get("view.multimedia_details"))
        for row, (label, value) in enumerate(rows):
            self._row(section, row, label, value)

    def _detail_rows(self, multimedia):
        """Retourne les couples libellé/valeur des métadonnées."""
        rows = []
        rows.extend(self._title_rows(multimedia))
        rows.extend(self._file_rows(multimedia))
        rows.extend(self._format_rows(multimedia))
        return rows

    def _title_rows(self, multimedia):
        """Retourne les lignes de titres."""
        titles = list(getattr(multimedia, "titles", None) or [])
        title = getattr(multimedia, "title", None)
        if title and title not in titles:
            titles.append(title)
        return [
            (self.translator.get("view.title"), value)
            for value in titles
            if value not in (None, "")
        ]

    def _file_rows(self, multimedia):
        """Retourne les lignes de fichiers."""
        file_records = list(getattr(multimedia, "file_records", None) or [])
        if file_records:
            return self._file_record_rows(file_records)
        files = list(getattr(multimedia, "files", None) or [])
        file_path = getattr(multimedia, "file", None)
        if not files and file_path:
            files.append(file_path)
        return [
            (self.translator.get("view.file"), value)
            for value in files
            if value not in (None, "")
        ]

    def _file_record_rows(self, file_records):
        """Retourne les lignes d'un enregistrement FILE."""
        rows = []
        for record in file_records:
            path = record.get("file")
            if path:
                rows.append((self.translator.get("view.file"), path))
            if record.get("format"):
                rows.append((self.translator.get("view.format"), record["format"]))
            if record.get("title"):
                rows.append((self.translator.get("view.title"), record["title"]))
            for tag, value in record.get("details") or []:
                rows.append((self._tag_label(tag, value), value or "—"))
        return rows

    def _format_rows(self, multimedia):
        """Retourne les lignes de formats."""
        formats = list(getattr(multimedia, "formats", None) or [])
        format_value = getattr(multimedia, "format", None)
        if format_value and format_value not in formats:
            formats.append(format_value)
        file_formats = {
            record.get("format")
            for record in getattr(multimedia, "file_records", None) or []
            if record.get("format")
        }
        return [
            (self.translator.get("view.format"), value)
            for value in formats
            if value not in file_formats
        ]

    def _display_notes(self, multimedia):
        """Affiche les notes de l'objet multimédia."""
        notes = list(getattr(multimedia, "notes", None) or [])
        note = getattr(multimedia, "note", None)
        if note and note not in notes:
            notes.append(note)
        if not notes:
            return
        section = self._section(self.translator.get("view.note"))
        for row, note_text in enumerate(notes):
            self._row(section, row, self.translator.get("view.text"), note_text)
            self.note_widget = self.value_widgets[-1]
