"""Tests de la vue multimédia de la fenêtre principale."""

import os
import tempfile
import unittest
from types import SimpleNamespace

from tests.main_window_test_case import GedcomViewerTestCase
from ui.views.image_preview import pdfium


class TestGedcomViewerMultimedia(GedcomViewerTestCase):
    """Vérifie l'aperçu et les métadonnées des objets multimédia."""

    # Vérifie multimedia view displays image preview when local file exists.
    def test_multimedia_view_displays_image_preview_when_local_file_exists(self):
        class DummyMedia:
            pointer = "@O1@"
            file = None
            title = "Preview"
            format = "ppm"
            note = "Preview test"

        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, "preview.ppm")
            with open(image_path, "wb") as tmp:
                tmp.write(b"P6\n1 1\n255\n\x00\x00\xff")

            media = DummyMedia()
            media.file = os.path.basename(image_path)

            self.viewer.entity_view_manager.views["object"].set_base_path(tmpdir)
            with self.assertLogs("ui.views.image_preview", level="INFO") as logs:
                self.viewer.entity_view_manager.views["object"].display(media)
            self.viewer.entity_view_manager.views["object"].update_idletasks()

            preview_image = self.viewer.entity_view_manager.views[
                "object"
            ].preview_label.cget("image")
            self.assertIsNotNone(preview_image)
            self.assertNotEqual(preview_image, "")
            self.assertNotIn(tmpdir, "\n".join(logs.output))

    # Vérifie multimedia view displays first page of local pdf.
    @unittest.skipUnless(pdfium is not None, "pypdfium2 non installé")
    def test_multimedia_view_displays_first_page_of_local_pdf(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "preview.pdf")
            Image.new("RGB", (40, 60), "white").save(pdf_path, format="PDF")
            media = SimpleNamespace(
                pointer="@M31@",
                file=os.path.basename(pdf_path),
                title="PDF preview",
                format="pdf",
                note=None,
            )
            view = self.viewer.entity_view_manager.views["object"]
            view.set_base_path(tmpdir)
            view.display(media)
            view.update_idletasks()

            self.assertNotEqual(view.preview_label.cget("image"), "")
            self.assertIsNotNone(view._preview_photo)

    # Vérifie multimedia preview failure does not log file path.
    def test_multimedia_preview_failure_does_not_log_file_path(self):
        class DummyMedia:
            pointer = "@O1@"
            file = "private-family-photo.ppm"
            title = "Preview"
            format = "ppm"
            note = "Preview test"

        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, DummyMedia.file)
            with open(image_path, "wb") as image_file:
                image_file.write(b"not an image")

            self.viewer.entity_view_manager.views["object"].set_base_path(tmpdir)
            with self.assertLogs("ui.views.image_preview", level="INFO") as logs:
                self.viewer.entity_view_manager.views["object"].display(DummyMedia())

            output = "\n".join(logs.output)
            self.assertNotIn(tmpdir, output)
            self.assertNotIn(DummyMedia.file, output)

    # Vérifie multimedia view displays metadata and clickable note.
    def test_multimedia_view_displays_metadata_and_clickable_note(self):
        multimedia = SimpleNamespace(
            pointer="@O2@",
            file="portrait.png",
            title="Portrait de famille",
            format="png",
            note="Informations complémentaires https://example.org/photo",
        )
        view = self.viewer.entity_view_manager.views["object"]
        view.display(multimedia)

        self.assertEqual(view.title_label.cget("text"), multimedia.title)
        details = view.sections[self.viewer.translator.get("view.multimedia_details")]
        detail_rows = view._section_rows[details]
        self.assertIn(
            (self.viewer.translator.get("view.file"), multimedia.file), detail_rows
        )
        self.assertIn(
            (self.viewer.translator.get("view.format"), multimedia.format), detail_rows
        )
        self.assertTrue(view.note_widget.tag_ranges("url"))

    # Vérifie multimedia view displays repeated files notes and extensions.
    def test_multimedia_view_displays_repeated_files_notes_and_extensions(self):
        multimedia = SimpleNamespace(
            pointer="@O3@",
            file="second.pdf",
            files=["portrait.jpg", "second.pdf"],
            file_records=[
                {
                    "file": "portrait.jpg",
                    "format": "jpeg",
                    "title": "Portrait",
                    "details": [],
                },
                {
                    "file": "second.pdf",
                    "format": "pdf",
                    "title": "Second scan",
                    "details": [("TYPE", "document")],
                },
            ],
            title=None,
            titles=[],
            format="pdf",
            formats=["jpeg", "pdf"],
            note="Second note",
            notes=["First note", "Second note"],
            additional_fields=[{"tag": "_CUSTOM", "value": "extension", "details": []}],
        )
        view = self.viewer.entity_view_manager.views["object"]
        view.display(multimedia)

        self.assertEqual(view.title_label.cget("text"), "Second scan")
        details = view.sections[self.viewer.translator.get("view.multimedia_details")]
        detail_rows = view._section_rows[details]
        for label_key, value in (
            ("view.title", "Portrait"),
            ("view.title", "Second scan"),
            ("view.file", "portrait.jpg"),
            ("view.file", "second.pdf"),
            ("view.format", "jpeg"),
            ("view.format", "pdf"),
            ("view.type", "document"),
        ):
            self.assertIn((self.viewer.translator.get(label_key), value), detail_rows)

        notes = view.sections[self.viewer.translator.get("view.note")]
        self.assertIn(
            (self.viewer.translator.get("view.text"), "First note"),
            view._section_rows[notes],
        )
        self.assertIn(
            (self.viewer.translator.get("view.text"), "Second note"),
            view._section_rows[notes],
        )
        additional = view.sections[self.viewer.translator.get("view.additional_fields")]
        self.assertIn(("_CUSTOM", "extension"), view._section_rows[additional])
