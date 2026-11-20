"""Tests des liens cliquables de la fenêtre principale."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests.main_window_test_case import GedcomViewerTestCase


class TestGedcomViewerLinks(GedcomViewerTestCase):
    """Vérifie les URL et les pointeurs GEDCOM cliquables."""

    # Vérifie family note urls are clickable.
    def test_family_note_urls_are_clickable(self):
        note = (
            "Détails sur https://archives.example.org/record, "
            "voir aussi http://source.example.net/page."
        )
        self.viewer.entity_view_manager.views["family"].display(
            SimpleNamespace(
                pointer="@FURL@",
                husband=None,
                wife=None,
                children=[],
                notes=[note],
                sources=[],
                events=[],
                marriages=[],
                divorces=[],
                additional_fields=[],
            )
        )
        self.root.update_idletasks()
        note_widget = next(
            widget
            for widget in self.viewer.entity_view_manager.views["family"].value_widgets
            if self._widget_text(widget) == note
        )

        self.assertEqual(len(note_widget.tag_ranges("url")), 4)
        self.assertEqual(note_widget.cget("state"), "disabled")

    # Vérifie pointer link activates on click but not drag.
    def test_pointer_link_activates_on_click_but_not_drag(self):
        view = self.viewer.entity_view_manager.views["individual"]
        view._navigate_pointer = Mock()

        for release_x, expected_activation in ((12, True), (20, False)):
            with self.subTest(release_x=release_x):
                widget = SimpleNamespace(after_idle=Mock())
                press = SimpleNamespace(widget=widget, x=10, y=10)
                release = SimpleNamespace(widget=widget, x=release_x, y=10)

                view._begin_pointer_activation(press, "@I1@")
                view._finish_pointer_activation(release, "@I1@")

                if expected_activation:
                    widget.after_idle.assert_called_once_with(
                        view._navigate_pointer, "@I1@"
                    )
                else:
                    widget.after_idle.assert_not_called()

    # Vérifie individual event multimedia pointer shows title and navigates.
    def test_individual_event_multimedia_pointer_shows_title_and_navigates(self):
        view = self.viewer.entity_view_manager.views["individual"]
        callback = Mock()
        view.on_pointer_click_callback = callback
        media = SimpleNamespace(
            title="Portrait de Charles",
            entity=SimpleNamespace(tag="OBJE"),
        )
        view.set_pointer_resolver(
            lambda pointer: media if pointer == "@X510@" else None
        )
        view.set_object_resolver(lambda pointer: None)
        view.set_object_display_name_resolver(
            lambda entity, entity_type=None: entity.title
        )
        view.display(
            SimpleNamespace(
                pointer="@I67@",
                name="Charles Henri René /ARBON/",
                events=[{"tag": "_PHOTO", "value": "@X510@", "children": []}],
                texts=[],
            )
        )

        labels = [self._widget_text(widget) for widget in view.tag_widgets]
        self.assertIn(self.viewer.translator.get("view.multimedia"), labels)
        media_link = view.links["@X510@"][0]
        self.assertIn("Portrait de Charles", self._widget_text(media_link))
        self.assertIn("pointer", media_link.tag_names("1.0"))
        view._navigate_pointer("@X510@")
        callback.assert_called_once_with("@X510@")

    # Vérifie submitter value url is marked clickable.
    def test_submitter_value_url_is_marked_clickable(self):
        with patch("ui.views.link_utils.webbrowser.open") as open_browser:
            self.viewer.entity_view_manager.views["submitter"].display(
                type(
                    "DummySubmitter",
                    (),
                    {
                        "pointer": "@M1@",
                        "name": "https://example.org/submitter",
                        "address": None,
                        "phone": None,
                        "email": None,
                        "phones": [],
                        "emails": [],
                    },
                )()
            )
            view = self.viewer.entity_view_manager.views["submitter"]
            self.assertTrue(view.value_widgets[0].tag_ranges("url"))
            open_browser.assert_not_called()

    # Vérifie multiline form marks urls as clickable.
    def test_multiline_form_marks_urls_as_clickable(self):
        self.viewer.entity_view_manager.views["note"].display(
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
        self.assertTrue(
            self.viewer.entity_view_manager.views["note"].text_widget.tag_ranges("url")
        )
