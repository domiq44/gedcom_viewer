import logging
import os
import tempfile
import tkinter as tk
import unittest
from unittest.mock import Mock, patch, call

from ui.main_window import GedcomViewer
from ui.views.link_utils import find_urls


class TestGedcomViewer(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        with patch.object(GedcomViewer, "_load_recent_files", return_value=[]):
            self.viewer = GedcomViewer(self.root)
        self.viewer.family_view.set_name_resolver(lambda pointer: None)
        self.viewer.highlighter = Mock()
        self.viewer.controller = Mock()

    def tearDown(self):
        self.root.destroy()

    def test_opens_last_recent_file_on_startup(self):
        root = tk.Tk()
        root.withdraw()

        try:
            with patch.object(
                GedcomViewer,
                "_load_recent_files",
                return_value=["/tmp/last_gedcom.ged"],
            ), patch("ui.main_window.os.path.isfile", return_value=True), patch.object(
                GedcomViewer, "_load_file_from_path"
            ) as load_file:
                viewer = GedcomViewer(root)
                root.update()
                self.assertEqual(load_file.call_count, 1)
                self.assertEqual(load_file.call_args[0][0], "/tmp/last_gedcom.ged")
                try:
                    viewer.root.destroy()
                except Exception:
                    pass
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_open_validated_file_uses_strict_loading(self):
        with patch(
            "ui.main_window.filedialog.askopenfilename",
            return_value="/tmp/validated.ged",
        ):
            with patch.object(self.viewer, "_load_file_from_path") as load_file:
                self.viewer.open_validated_file()

        load_file.assert_called_once_with("/tmp/validated.ged", strict=True)

    def test_show_header_displays_head_block(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.extract_head.return_value = "0 HEAD\n1 SOUR GEDCOM"

        self.viewer.show_header()

        content = self.viewer.text_area.get("1.0", tk.END).strip()
        self.assertEqual(content, "0 HEAD\n1 SOUR GEDCOM")
        self.viewer.highlighter.highlight.assert_called_once()

    def test_show_header_shows_error_when_missing(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.extract_head.return_value = ""

        with patch("ui.main_window.messagebox.showerror") as showerror:
            self.viewer.show_header()
            showerror.assert_called_once_with(
                "Erreur", "Aucun en-tête HEAD trouvé dans le fichier."
            )

    def test_show_trailer_displays_trailer_block(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.extract_trailer.return_value = "0 TRLR"

        self.viewer.show_trailer()

        content = self.viewer.text_area.get("1.0", tk.END).strip()
        self.assertEqual(content, "0 TRLR")
        self.viewer.highlighter.highlight.assert_called_once()

    def test_show_trailer_shows_error_when_missing(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.extract_trailer.return_value = ""

        with patch("ui.main_window.messagebox.showerror") as showerror:
            self.viewer.show_trailer()
            showerror.assert_called_once_with(
                "Erreur", "Aucun bloc TRLR trouvé dans le fichier."
            )

    def test_navigate_to_displays_entity_context(self):
        class DummyIndividual:
            pointer = "@I1@"
            famc = None
            fams = []

        target = DummyIndividual()
        context = {
            "type": "individual",
            "entity": target,
            "raw_entity": target,
            "raw_block": "0 @I1@ INDI",
        }

        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.resolve_pointer.return_value = target
        self.viewer.controller.get_entity_display_info.return_value = context

        self.viewer.navigate_to("@I1@")

        content = self.viewer.text_area.get("1.0", tk.END).strip()
        self.assertEqual(content, "0 @I1@ INDI")
        self.viewer.highlighter.highlight.assert_called_once()

    def test_navigate_to_shows_error_when_entity_not_found(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.resolve_pointer.return_value = None

        with patch("ui.main_window.messagebox.showerror") as showerror:
            self.viewer.navigate_to("@X1@")
            showerror.assert_called_once_with("Erreur", "Entité introuvable : @X1@")

    def test_navigation_history_can_go_back_and_forward(self):
        class DummyEntity:
            pointer = None

        first = DummyEntity()
        first.pointer = "@I1@"
        second = DummyEntity()
        second.pointer = "@I2@"

        first_context = {
            "type": "individual",
            "entity": first,
            "raw_entity": first,
            "raw_block": "0 @I1@ INDI",
        }
        second_context = {
            "type": "family",
            "entity": second,
            "raw_entity": second,
            "raw_block": "0 @I2@ FAM",
        }

        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.resolve_pointer.side_effect = [first, second]
        self.viewer.controller.get_entity_display_info.side_effect = [
            first_context,
            second_context,
        ]

        self.viewer.navigate_to("@I1@")
        self.viewer.navigate_to("@I2@")

        self.viewer.go_back()
        content = self.viewer.text_area.get("1.0", tk.END).strip()
        self.assertEqual(content, "0 @I1@ INDI")

        self.viewer.go_forward()
        content = self.viewer.text_area.get("1.0", tk.END).strip()
        self.assertEqual(content, "0 @I2@ FAM")

    def test_display_entity_context_records_navigation_history(self):
        class DummyEntity:
            pointer = "@I1@"

        context = {
            "type": "individual",
            "entity": DummyEntity(),
            "raw_entity": DummyEntity(),
            "raw_block": "0 @I1@ INDI",
        }

        self.viewer.display_entity_context(context)

        self.assertEqual(len(self.viewer._nav_history), 1)
        self.assertEqual(self.viewer._nav_index, 0)

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

            self.viewer.object_view.set_base_path(tmpdir)
            self.viewer.object_view.display(media)
            self.viewer.object_view.update_idletasks()

            preview_image = self.viewer.object_view.preview_label.cget("image")
            self.assertIsNotNone(preview_image)
            self.assertNotEqual(preview_image, "")

    def test_source_view_repository_pointer_includes_name(self):
        self.viewer.source_view.set_reference_resolver(
            lambda pointer: {
                "@R1@": type("DummyRepository", (), {"name": "Archives de Paris"})(),
            }.get(pointer)
        )

        class DummySource:
            pointer = "@S1@"
            title = "Titre source"
            author = "Auteur"
            pub_date = None
            text = "Texte"
            repository = "@R1@"

        self.viewer.source_view.display(DummySource())
        label = self.viewer.source_view.labels["repository"]

        self.assertIn("@R1@", label.cget("text"))
        self.assertIn("Archives de Paris", label.cget("text"))

    def test_submitter_view_displays_multiple_phones_and_emails(self):
        class DummySubmitter:
            pointer = "@M1@"
            name = "Submitter"
            address = None
            phone = "legacy-phone"
            email = "legacy-email"
            phones = ["01 02 03 04 05", "06 07 08 09 10"]
            emails = ["first@example.org", "second@example.org"]

        self.viewer.submitter_view.display(DummySubmitter())

        self.assertEqual(
            self.viewer.submitter_view.labels["phone"].cget("text"),
            "01 02 03 04 05, 06 07 08 09 10",
        )
        self.assertEqual(
            self.viewer.submitter_view.labels["email"].cget("text"),
            "first@example.org, second@example.org",
        )

    def test_empty_entity_list_clears_raw_and_detail_views(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.get_entity_types.return_value = ["INDI"]
        self.viewer.controller.get_entity_list_items.return_value = []
        self.viewer.entity_type_var.set("INDI")

        self.viewer._show_entity_view("INDI", object())
        self.viewer._display_raw_text("0 @I1@ INDI")

        self.viewer.list_entities()

        self.assertEqual(self.viewer.text_area.get("1.0", tk.END).strip(), "")
        self.assertEqual(self.viewer.individual_view.title_label.cget("text"), "Fiche individu")

    def test_ui_status_reflects_last_log_message(self):
        logger = logging.getLogger("ui.main_window")
        logger.error("test log ui status")

        self.root.update_idletasks()
        self.assertIn("test log ui status", self.viewer.status_var.get())
        self.assertEqual(self.viewer.status_label.cget("state"), "readonly")

        self.viewer.status_label.selection_range(0, tk.END)
        self.viewer.status_label.event_generate("<<Copy>>")

    def test_load_file_logs_elapsed_time(self):
        self.viewer.controller.get_entity_types.return_value = ["INDI"]
        self.viewer.controller.get_all_entity_type_menu_display_items.return_value = [
            ("INDI - Individu", "INDI")
        ]

        with patch("ui.main_window.time.perf_counter", side_effect=[10.0, 12.345]):
            with patch.object(self.viewer, "list_entities"):
                with self.assertLogs("ui.main_window", level="INFO") as logs:
                    self.viewer._load_file_from_path("/tmp/test.ged")

        self.assertIn("GEDCOM chargé avec succès en 2.345 s", logs.output[-1])

    def test_clear_recent_files_removes_all_entries(self):
        self.viewer.recent_files = ["/tmp/one.ged", "/tmp/two.ged"]
        with patch.object(self.viewer, "_save_recent_files") as save_recent:
            self.viewer.clear_recent_files()

        self.assertEqual(self.viewer.recent_files, [])
        save_recent.assert_called_once_with()

    def test_save_recent_files_logs_write_errors(self):
        self.viewer.recent_files = ["/tmp/example.ged"]

        with patch("ui.main_window.open", side_effect=OSError("permission denied")):
            with self.assertLogs("ui.main_window", level="WARNING") as logs:
                self.viewer._save_recent_files()

        self.assertIn("Impossible d'enregistrer la liste des fichiers récents", logs.output[0])

    def test_load_recent_files_logs_read_errors(self):
        with patch("ui.main_window.os.path.isfile", return_value=True):
            with patch("ui.main_window.open", side_effect=OSError("permission denied")):
                with self.assertLogs("ui.main_window", level="WARNING") as logs:
                    recent_files = self.viewer._load_recent_files()

        self.assertEqual(recent_files, [])
        self.assertIn("Impossible de lire la liste des fichiers récents", logs.output[0])

    def test_find_urls_in_form_value(self):
        value = "Voir https://example.org/document, puis http://example.net."
        self.assertEqual(
            find_urls(value),
            ["https://example.org/document", "http://example.net"],
        )

    def test_simple_form_url_opens_in_web_browser(self):
        with patch("ui.views.link_utils.webbrowser.open") as open_browser:
            self.viewer.submitter_view.display(
                type(
                    "DummySubmitter",
                    (),
                    {
                        "pointer": "@M1@",
                        "name": "https://example.org/submitter",
                        "address": None,
                        "phone": None,
                        "email": None,
                    },
                )()
            )
            self.viewer.submitter_view.labels["name"].event_generate("<Button-1>")
            open_browser.assert_called_once_with("https://example.org/submitter")

    def test_multiline_form_marks_urls_as_clickable(self):
        self.viewer.note_view.display(
            type(
                "DummyNote",
                (),
                {
                    "pointer": "@N1@",
                    "text": "Consulter https://example.org/note",
                    "source": None,
                    "references": [],
                    "record_id": None,
                    "submitters": [],
                    "change_date": None,
                    "change_time": None,
                    "additional_fields": [],
                },
            )
        )
        self.assertTrue(self.viewer.note_view.text_widget.tag_ranges("url"))

    def test_individual_view_pointer_click_calls_callback(self):
        callback = Mock()
        self.viewer.individual_view.on_pointer_click_callback = callback

        class DummyIndividual:
            pointer = "@I1@"
            famc = None
            fams = ["@F1@"]

        individual = DummyIndividual()
        self.viewer.individual_view.display(individual)

        container = self.viewer.individual_view.labels["fams"]
        pointer_labels = [
            child
            for child in container.winfo_children()
            if child.cget("text") == "@F1@"
        ]
        self.assertTrue(pointer_labels)

        pointer_labels[0].event_generate("<Button-1>")
        self.viewer.individual_view.update_idletasks()

        callback.assert_called_once_with("@F1@")

    def test_individual_view_famc_and_fams_click_callback(self):
        callback = Mock()
        self.viewer.individual_view.on_pointer_click_callback = callback

        class DummyIndividual:
            pointer = "@I1@"
            famc = "@F0@"
            fams = ["@F1@", "@F2@"]

        individual = DummyIndividual()
        self.viewer.individual_view.display(individual)

        famc_label = self.viewer.individual_view.labels["famc"]
        self.assertEqual(famc_label.cget("text"), "@F0@")
        famc_label.event_generate("<Button-1>")

        container = self.viewer.individual_view.labels["fams"]
        pointer_labels = [
            child
            for child in container.winfo_children()
            if child.cget("text") == "@F2@"
        ]
        self.assertTrue(pointer_labels)
        pointer_labels[0].event_generate("<Button-1>")

        self.viewer.individual_view.update_idletasks()
        callback.assert_has_calls([call("@F0@"), call("@F2@")], any_order=True)

    def test_individual_view_family_links_include_names(self):
        self.viewer.individual_view.set_family_name_resolver(
            lambda pointer: {
                "@F0@": type("DummyFamily", (), {"husband": "@I1@", "wife": "@I2@"})(),
                "@F1@": type("DummyFamily", (), {"husband": "@I3@", "wife": "@I4@"})(),
            }.get(pointer)
        )
        self.viewer.individual_view._family_member_resolver = lambda pointer: {
            "@I1@": type("DummyIndividual", (), {"name": "Jean"})(),
            "@I2@": type("DummyIndividual", (), {"name": "Claire"})(),
            "@I3@": type("DummyIndividual", (), {"name": "Paul"})(),
            "@I4@": type("DummyIndividual", (), {"name": "Anne"})(),
        }.get(pointer)

        class DummyIndividual:
            pointer = "@I9@"
            famc = "@F0@"
            fams = ["@F1@"]

        self.viewer.individual_view.display(DummyIndividual())

        famc_label = self.viewer.individual_view.labels["famc"]
        fams_container = self.viewer.individual_view.labels["fams"]

        self.assertIn("Jean", famc_label.cget("text"))
        self.assertTrue(
            any(
                "Paul" in child.cget("text")
                for child in fams_container.winfo_children()
            )
        )

    def test_family_view_children_click_calls_callback(self):
        callback = Mock()
        self.viewer.family_view.on_pointer_click_callback = callback

        class DummyFamily:
            pointer = "@F1@"
            husband = "@I1@"
            wife = "@I2@"
            children = ["@I3@", "@I4@"]
            marriage_date = None
            marriage_place = None
            divorce_date = None
            divorce_place = None

        family = DummyFamily()
        self.viewer.family_view.display(family)

        container = self.viewer.family_view.labels["children"]
        pointer_labels = [
            child
            for child in container.winfo_children()
            if child.cget("text").startswith("@I3@")
        ]
        self.assertTrue(pointer_labels)

        pointer_labels[0].event_generate("<Button-1>")
        self.viewer.family_view.update_idletasks()

        callback.assert_called_once_with("@I3@")

    def test_family_view_parents_click_calls_callback(self):
        callback = Mock()
        self.viewer.family_view.on_pointer_click_callback = callback

        class DummyFamily:
            pointer = "@F1@"
            husband = "@I1@"
            wife = "@I2@"
            children = ["@I3@", "@I4@"]
            marriage_date = None
            marriage_place = None
            divorce_date = None
            divorce_place = None

        family = DummyFamily()
        self.viewer.family_view.display(family)

        husband_label = self.viewer.family_view.labels["husband"]
        wife_label = self.viewer.family_view.labels["wife"]

        self.assertEqual(husband_label.cget("text"), "@I1@")
        self.assertEqual(wife_label.cget("text"), "@I2@")

        husband_label.event_generate("<Button-1>")
        wife_label.event_generate("<Button-1>")
        self.viewer.family_view.update_idletasks()

        callback.assert_has_calls([call("@I1@"), call("@I2@")], any_order=True)

    def test_family_view_displays_names_for_parents_and_children(self):
        callback = Mock()
        self.viewer.family_view.on_pointer_click_callback = callback

        class DummyIndividual:
            def __init__(self, pointer, name):
                self.pointer = pointer
                self.name = name

        self.viewer.family_view.set_name_resolver(
            lambda pointer: {
                "@I1@": DummyIndividual("@I1@", "Marcel/ANSELIN/"),
                "@I2@": DummyIndividual("@I2@", "/BIROT/Angèle"),
                "@I3@": DummyIndividual("@I3@", "Jean/LENCARTÉ/"),
                "@I4@": DummyIndividual("@I4@", "Cunégonde"),
            }.get(pointer)
        )

        class DummyFamily:
            pointer = "@F1@"
            husband = "@I1@"
            wife = "@I2@"
            children = ["@I3@", "@I4@"]
            marriage_date = None
            marriage_place = None
            divorce_date = None
            divorce_place = None

        self.viewer.family_view.display(DummyFamily())

        husband_label = self.viewer.family_view.labels["husband"]
        wife_label = self.viewer.family_view.labels["wife"]
        self.assertIn("Marcel/ANSELIN/", husband_label.cget("text"))
        self.assertIn("/BIROT/Angèle", wife_label.cget("text"))

        container = self.viewer.family_view.labels["children"]
        children_texts = [child.cget("text") for child in container.winfo_children()]
        self.assertTrue(any("Jean/LENCARTÉ/" in text for text in children_texts))
        self.assertTrue(any("Cunégonde" in text for text in children_texts))

    def test_family_view_children_display(self):
        class DummyFamily:
            pointer = "@F1@"
            husband = "@I1@"
            wife = "@I2@"
            children = ["@I3@", "@I4@"]
            marriage_date = None
            marriage_place = None
            divorce_date = None
            divorce_place = None

        family = DummyFamily()
        self.viewer.family_view.display(family)

        container = self.viewer.family_view.labels["children"]
        self.assertEqual(len(container.winfo_children()), 2)
        self.assertTrue(
            any(
                child.cget("text").startswith("@I3@")
                for child in container.winfo_children()
            )
        )
        self.assertTrue(
            any(
                child.cget("text").startswith("@I4@")
                for child in container.winfo_children()
            )
        )

    def test_family_view_displays_multiple_marriages(self):
        class DummyFamily:
            pointer = "@F1@"
            husband = None
            wife = None
            children = []
            marriage_date = None
            marriage_place = None
            marriages = [
                {"tag": "MARR", "value": "", "details": [("DATE", "1900")]},
                {"tag": "MARR", "value": "", "details": [("DATE", "1920")]},
            ]
            divorce_date = None
            divorce_place = None

        self.viewer.family_view.display(DummyFamily())

        container = self.viewer.family_view.labels["marriages"]
        marriage_texts = [child.cget("text") for child in container.winfo_children()]
        self.assertEqual(marriage_texts, ["DATE: 1900", "DATE: 1920"])


if __name__ == "__main__":
    unittest.main()
