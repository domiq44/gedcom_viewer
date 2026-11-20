"""Tests des vues par entité de la fenêtre principale."""

from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from tests.main_window_test_case import GedcomViewerTestCase


class TestGedcomViewerViews(GedcomViewerTestCase):
    """Vérifie le rendu et les interactions des vues par entité."""

    # Vérifie individual view displays gallery media list.
    def test_individual_view_displays_gallery_media_list(self):
        view = self.viewer.entity_view_manager.views["individual"]
        media_1 = Mock(pointer="@O1@", title="Portrait", file="portrait.jpg")
        media_2 = Mock(pointer="@O2@", title="Family", file="family.png")
        view.set_object_resolver(
            lambda pointer: {"@O1@": media_1, "@O2@": media_2}.get(pointer)
        )
        media_1.entity = SimpleNamespace(tag="OBJE")
        media_2.entity = SimpleNamespace(tag="OBJE")
        view.set_pointer_resolver(
            lambda pointer: {"@O1@": media_1, "@O2@": media_2}.get(pointer)
        )
        view.set_object_display_name_resolver(
            lambda media, entity_type=None: getattr(media, "title", "")
            or getattr(media, "file", "")
        )

        individual = Mock()
        individual.pointer = "@I1@"
        individual.name = "John /DOE/"
        individual.sex = "M"
        individual.birth_date = ""
        individual.birth_place = ""
        individual.baptism_date = ""
        individual.baptism_place = ""
        individual.death_date = ""
        individual.death_place = ""
        individual.death_confirmed = False
        individual.age_at_death = ""
        individual.nickname = ""
        individual.occupations = []
        individual.notes = []
        individual.properties = []
        individual.texts = []
        individual.famc = None
        individual.fams = []
        individual.obje = ["@O1@", "@O2@"]
        individual.events = []

        view.display(individual)
        self.root.update_idletasks()

        self.assertEqual(type(view).__name__, "IndividualPropertyView")
        self.assertEqual(
            type(self.viewer.entity_view_manager.views["family"]).__name__,
            "FamilyPropertyView",
        )
        gallery = view.sections[self.viewer.translator.get("view.gallery")]
        gallery_values = [
            self._widget_text(widget) for widget in gallery.winfo_children()
        ]
        self.assertTrue(any("Portrait" in value for value in gallery_values))
        self.assertTrue(any("Family" in value for value in gallery_values))
        self.assertIn("@O1@", view.links)
        self.assertIn("@O2@", view.links)

    # Vérifie individual view displays scalar and list properties.
    def test_individual_view_displays_scalar_and_list_properties(self):
        view = self.viewer.entity_view_manager.views["individual"]
        self.viewer.controller.format_entity_display_name.return_value = "Lovelace, Ada"
        individual = SimpleNamespace(
            pointer="@I50@",
            name="Ada /Lovelace/",
            sex="F",
            famc=None,
            nickname="Enchantress of Numbers",
            birth_date="10 DEC 1815",
            birth_place="London",
            baptism_date="",
            baptism_place="",
            death_date="27 NOV 1852",
            death_place="Marylebone",
            death_confirmed=True,
            age_at_death="36",
            marriage_count=1,
            occupations=[{"occupation": "Writer", "date": "1843"}],
            properties=["Nationality: British"],
            texts=["First text", "Second text", "Long value " * 500],
            notes=["Research note"],
            fams=[],
            obje=[],
            events=[
                {
                    "tag": "BIRT",
                    "value": "",
                    "children": [
                        {"tag": "DATE", "value": "10 DEC 1815", "children": []}
                    ],
                },
                {"tag": "NICK", "value": "Enchantress of Numbers", "children": []},
                {
                    "tag": "EVEN",
                    "value": "Public lecture",
                    "children": [{"tag": "DATE", "value": "1843", "children": []}],
                },
            ],
        )

        view.display(individual)
        self.assertEqual(type(view).__name__, "IndividualPropertyView")
        self.assertEqual(view.title_label.cget("text"), "Lovelace, Ada")
        overview = view.sections[self.viewer.translator.get("view.individual_overview")]
        self.assertEqual(overview.cget("style"), "DetailSection.TLabelframe")
        overview_values = [
            self._widget_text(widget) for widget in overview.winfo_children()
        ]
        self.assertIn("10 DEC 1815", overview_values)
        self.assertIn("London", overview_values)
        self.assertIn("27 NOV 1852", overview_values)
        self.assertIn(self.viewer.translator.get("common.yes"), overview_values)
        self.assertIn("1", overview_values)

        occupations = view.sections[self.viewer.translator.get("view.occupations")]
        occupation_values = [
            self._widget_text(widget) for widget in occupations.winfo_children()
        ]
        self.assertIn("Writer · 1843", occupation_values)

        properties = view.sections[self.viewer.translator.get("view.properties")]
        property_values = [
            self._widget_text(widget) for widget in properties.winfo_children()
        ]
        self.assertIn("Nationality: British", property_values)

        texts = view.sections[self.viewer.translator.get("view.texts")]
        text_values = [self._widget_text(widget) for widget in texts.winfo_children()]
        self.assertIn("Long value " * 500, text_values)

        events = view.sections[self.viewer.translator.get("view.events")]
        event_values = [self._widget_text(widget) for widget in events.winfo_children()]
        self.assertIn("Public lecture", event_values)
        self.assertIn("1843", event_values)

        individual.death_confirmed = False
        view.display(individual)
        overview = view.sections[self.viewer.translator.get("view.individual_overview")]
        overview_values = [
            self._widget_text(widget) for widget in overview.winfo_children()
        ]
        self.assertIn(self.viewer.translator.get("common.no"), overview_values)

    # Vérifie individual text is selectable copyable and not duplicated.
    def test_individual_text_is_selectable_copyable_and_not_duplicated(self):
        text = "First line of the citation\nContinuation of the citation"
        individual = SimpleNamespace(
            pointer="@I67@",
            name="Charles Henri René /ARBON/",
            events=[
                {
                    "tag": "SOUR",
                    "value": "@S1@",
                    "children": [
                        {
                            "tag": "DATA",
                            "value": "",
                            "children": [
                                {
                                    "tag": "TEXT",
                                    "value": "First line of the citation",
                                    "children": [
                                        {
                                            "tag": "CONT",
                                            "value": "Continuation of the citation",
                                            "children": [],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
            texts=[text],
        )

        self.viewer.entity_view_manager.views["individual"].display(individual)
        view = self.viewer.entity_view_manager.views["individual"]
        self.root.update_idletasks()
        event_values = [
            self._widget_text(widget)
            for widget in view.sections[
                self.viewer.translator.get("view.events")
            ].winfo_children()
        ]
        text_values = [
            self._widget_text(widget)
            for widget in view.sections[
                self.viewer.translator.get("view.texts")
            ].winfo_children()
        ]
        self.assertNotIn("First line of the citation", event_values)
        self.assertNotIn("Continuation of the citation", event_values)
        self.assertIn(text, text_values)

        text_widget = next(
            widget for widget in view.value_widgets if self._widget_text(widget) == text
        )
        self.assertEqual(text_widget.cget("state"), "disabled")
        text_widget.tag_add("sel", "1.0", "end-1c")
        text_widget.event_generate("<<Copy>>")
        self.assertEqual(self.root.clipboard_get(), text)

        tag_widget = next(
            widget
            for widget in view.tag_widgets
            if self._widget_text(widget) == self.viewer.translator.get("view.source")
        )
        self.assertEqual(tag_widget.cget("state"), "disabled")
        tag_widget.tag_add("sel", "1.0", "end-1c")
        tag_widget.event_generate("<<Copy>>")
        self.assertEqual(
            self.root.clipboard_get(), self.viewer.translator.get("view.source")
        )

    # Vérifie individual event labels translate known tags and keep unknown codes.
    def test_individual_event_labels_translate_known_tags_and_keep_unknown_codes(self):
        view = self.viewer.entity_view_manager.views["individual"]
        callback = Mock()
        view.on_pointer_click_callback = callback
        target = SimpleNamespace(
            name="Jean /DUPONT/",
            entity=SimpleNamespace(tag="INDI"),
        )
        view.set_pointer_resolver(
            lambda pointer: target if pointer == "@X510@" else None
        )
        view.set_display_name_resolver(lambda entity, entity_type=None: "Dupont, Jean")
        view.display(
            SimpleNamespace(
                pointer="@I67@",
                name="Charles Henri René /ARBON/",
                events=[
                    {
                        "tag": "SOUR",
                        "value": "@S1@",
                        "children": [
                            {"tag": "PAGE", "value": "17", "children": []},
                            {"tag": "QUAY", "value": "2", "children": []},
                            {"tag": "_CUSTOM", "value": "Value", "children": []},
                        ],
                    },
                    {"tag": "ASSO", "value": "@X510@", "children": []},
                    {
                        "tag": "BIRT",
                        "value": "",
                        "children": [
                            {
                                "tag": "PLAC",
                                "value": "Paris",
                                "children": [
                                    {
                                        "tag": "MAP",
                                        "value": "",
                                        "children": [
                                            {
                                                "tag": "LATI",
                                                "value": "N48.8",
                                                "children": [],
                                            },
                                            {
                                                "tag": "LONG",
                                                "value": "E2.3",
                                                "children": [],
                                            },
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                ],
                texts=[],
            )
        )

        labels = [self._widget_text(widget) for widget in view.tag_widgets]
        self.assertIn(self.viewer.translator.get("view.source"), labels)
        self.assertIn(self.viewer.translator.get("view.page"), labels)
        self.assertIn(self.viewer.translator.get("view.source_quality"), labels)
        self.assertIn(self.viewer.translator.get("view.map_coordinates"), labels)
        self.assertIn(self.viewer.translator.get("view.latitude"), labels)
        self.assertIn(self.viewer.translator.get("view.longitude"), labels)
        for tag, key in (
            ("ADOP", "view.adoption"),
            ("BURI", "view.burial"),
            ("CREM", "view.cremation"),
            ("DSCR", "view.description"),
            ("GRAD", "view.graduation"),
            ("RETI", "view.retirement"),
            ("OBJE", "view.multimedia"),
        ):
            self.assertEqual(view._tag_label(tag), self.viewer.translator.get(key))
        self.assertIn(self.viewer.translator.get("view.referenced_individual"), labels)
        for tag, key in (
            ("CHAN", "view.change_information"),
            ("TIME", "view.time"),
            ("BAPM", "view.baptism"),
            ("CENS", "view.census"),
            ("RESI", "view.residence"),
            ("GIVN", "view.given_name"),
            ("SURN", "view.surname"),
            ("ADDR", "view.address"),
            ("ASSO", "view.association"),
            ("HUSB", "view.husband"),
            ("WIFE", "view.wife"),
            ("CHIL", "view.children"),
            ("FAMC", "view.child_family"),
            ("FAMS", "view.family_parent_families"),
            ("NCHI", "view.children_count"),
            ("NICK", "view.nickname"),
            ("SEX", "view.sex"),
            ("ENGA", "view.engagement"),
            ("MARB", "view.marriage_banns"),
            ("MARC", "view.marriage_contract"),
            ("MARL", "view.marriage_license"),
        ):
            self.assertEqual(view._tag_label(tag), self.viewer.translator.get(key))
        self.assertIn("_CUSTOM", labels)
        self.assertEqual(view._tag_label("_TIME"), "_TIME")
        self.assertEqual(view._tag_label("_SOSADABOVILLE"), "_SOSADABOVILLE")
        self.assertEqual(
            view._tag_label("ZZZZ"),
            self.viewer.translator.get("view.other_gedcom_tag", tag="ZZZZ"),
        )
        individual_link = view.links["@X510@"][0]
        self.assertIn("Dupont, Jean", self._widget_text(individual_link))
        self.assertTrue(
            individual_link.tk.call(
                individual_link._w, "tag", "bind", "pointer", "<Button-1>"
            )
        )
        self.assertTrue(
            individual_link.tk.call(
                individual_link._w,
                "tag",
                "bind",
                "pointer",
                "<ButtonRelease-1>",
            )
        )
        self.assertFalse(
            individual_link.tk.call(
                individual_link._w, "tag", "bind", "pointer", "<Double-1>"
            )
        )
        self.assertIn("pointer", individual_link.tag_names("1.0"))
        view._navigate_pointer("@X510@")
        callback.assert_called_once_with("@X510@")

    # Vérifie individual section copy includes title labels and values.
    def test_individual_section_copy_includes_title_labels_and_values(self):
        view = self.viewer.entity_view_manager.views["individual"]
        tooltip_factory = Mock()
        view.tooltip_factory = tooltip_factory
        view.display(
            SimpleNamespace(
                pointer="@I67@",
                name="Charles Henri René /ARBON/",
                birth_date="12 MAR 1840",
                birth_place="Paris",
                events=[],
                texts=[],
            )
        )
        title = self.viewer.translator.get("view.individual_overview")
        section = view.sections[title]
        copy_button = view.section_copy_buttons[section]
        first_tag = next(
            widget for widget in view.tag_widgets if widget.master is section
        )
        self.assertEqual(int(copy_button.grid_info()["row"]), 0)
        self.assertEqual(int(first_tag.grid_info()["row"]), 1)
        self.assertEqual(copy_button.cget("text"), "⧉")
        self.assertEqual(copy_button.cget("style"), "Copy.TButton")
        self.assertLessEqual(int(copy_button.cget("width")), 2)
        tooltip_factory.assert_any_call(
            copy_button, self.viewer.translator.get("ui.copy_section")
        )
        gedcom_copy_button = self.viewer.detail_panel.copy_button
        self.assertEqual(copy_button.cget("width"), gedcom_copy_button.cget("width"))
        self.assertEqual(
            copy_button.cget("padding"), gedcom_copy_button.cget("padding")
        )

        copy_button.invoke()

        self.assertEqual(copy_button.cget("text"), "✓")
        copied = self.root.clipboard_get()
        self.assertEqual(copied.splitlines()[0], title)
        self.assertIn(
            f"{self.viewer.translator.get('view.birth_date')}: 12 MAR 1840",
            copied,
        )
        self.assertIn(
            f"{self.viewer.translator.get('view.birth_place')}: Paris",
            copied,
        )

    # Vérifie individual view scrolls with linux wheel and trackpad.
    def test_individual_view_scrolls_with_linux_wheel_and_trackpad(self):
        self.viewer.entity_view_manager.views["individual"].display(
            SimpleNamespace(
                pointer="@I67@",
                name="Charles Henri René /ARBON/",
                events=[],
                texts=["Long text " * 100],
            )
        )
        view = self.viewer.entity_view_manager.views["individual"]
        self.root.update_idletasks()
        view.canvas.configure(scrollregion=(0, 0, 500, 2000))
        view.canvas.yview_moveto(0)
        tag_widget = view.tag_widgets[0]
        overview = view.sections[self.viewer.translator.get("view.individual_overview")]
        self.assertEqual(int(overview.grid_columnconfigure(0)["minsize"]), 140)
        self.assertIn("e", tag_widget.grid_info()["sticky"])
        self.assertTrue(tag_widget.bind("<MouseWheel>"))
        self.assertTrue(tag_widget.bind("<Button-4>"))
        self.assertTrue(tag_widget.bind("<Button-5>"))
        self.assertTrue(view.canvas.bind("<MouseWheel>"))
        self.assertTrue(view.canvas.bind("<Button-4>"))
        self.assertTrue(view.canvas.bind("<Button-5>"))

        with patch.object(view.canvas, "yview_scroll") as scroll:
            self.assertEqual(
                view._on_mousewheel(SimpleNamespace(num=5, delta=0)), "break"
            )
            scroll.assert_called_once_with(1, "units")

        with patch.object(view.canvas, "yview_scroll") as scroll:
            self.assertEqual(
                view._on_mousewheel(SimpleNamespace(num=None, delta=-1)), "break"
            )
            scroll.assert_called_once_with(1, "units")

    # Vérifie repository view displays identity address and additional fields.
    def test_repository_view_displays_identity_address_and_additional_fields(self):
        repository = SimpleNamespace(
            pointer="@R50@",
            name="Archives de Paris",
            record_id="PAR-8",
            address="18 rue des Archives",
            address_line_1="Bâtiment A",
            address_line_2="Salle 4",
            city="Paris",
            state="Île-de-France",
            postal_code="75004",
            country="France",
            change_date="1 JAN 2020",
            change_time="12:00:00",
            notes=["Inventaire des registres\nComplément"],
            references=["Cote 8"],
            phones=["03 20 00 00 00", "03 20 00 00 01"],
            emails=["archives@example.org"],
            websites=["https://archives.example.org"],
            additional_fields=[
                {"tag": "_CUSTOM", "value": "Valeur conservée", "details": []}
            ],
        )
        view = self.viewer.entity_view_manager.views["repo"]
        view.display(repository)

        self.assertEqual(view.title_label.cget("text"), "Archives de Paris")
        details = view.sections[self.viewer.translator.get("view.repository_details")]
        self.assertEqual(details.cget("style"), "DetailSection.TLabelframe")
        self.assertIn(
            (self.viewer.translator.get("view.internal_id"), "PAR-8"),
            view._section_rows[details],
        )
        address = view.sections[self.viewer.translator.get("view.repository_address")]
        self.assertIn(
            (self.viewer.translator.get("view.city"), "Paris"),
            view._section_rows[address],
        )
        self.assertIn(
            (self.viewer.translator.get("view.additional_address_2"), "Salle 4"),
            view._section_rows[address],
        )
        contacts = view.sections[self.viewer.translator.get("view.contact_information")]
        self.assertIn(
            (self.viewer.translator.get("view.phone"), "03 20 00 00 01"),
            view._section_rows[contacts],
        )
        self.assertIn(
            (self.viewer.translator.get("view.email"), "archives@example.org"),
            view._section_rows[contacts],
        )
        self.assertIn(
            (
                self.viewer.translator.get("view.website"),
                "https://archives.example.org",
            ),
            view._section_rows[contacts],
        )
        notes = view.sections[self.viewer.translator.get("view.notes")]
        self.assertIn(
            ("", "Inventaire des registres\nComplément"),
            view._section_rows[notes],
        )
        additional = view.sections[self.viewer.translator.get("view.additional_fields")]
        self.assertIn(("_CUSTOM", "Valeur conservée"), view._section_rows[additional])

    # Vérifie every entity type uses a structured view.
    def test_every_entity_type_uses_a_structured_view(self):
        for entity_type, (
            view,
            _tab,
        ) in self.viewer.entity_view_manager.entity_view_map.items():
            with self.subTest(entity_type=entity_type):
                self.assertEqual(view.entity_type, entity_type)
                self.assertTrue(hasattr(view, "sections"))

    # Vérifie submitter view displays identity and multiple contacts.
    def test_submitter_view_displays_identity_and_multiple_contacts(self):
        submitter = SimpleNamespace(
            pointer="@M50@",
            name="Jean Dupont",
            address="12 rue des Lilas\nParis",
            address_line_1="12 rue des Lilas",
            address_line_2="Appartement 2",
            city="Lille",
            state="Nord",
            postal_code="59000",
            country="France",
            phone="01 02 03 04",
            phones=["01 02 03 04", "+33 6 11 22 33"],
            email="jean@example.org",
            emails=["jean@example.org", "contact@example.org"],
            fax="03 20 00 00 01",
            faxes=["03 20 00 00 01"],
            website="https://example.org",
            websites=["https://example.org"],
            language="English",
            languages=["French", "English"],
            registered_number="REG-50",
            record_id="INT-50",
            restriction="privacy",
            change_date="1 JAN 2020",
            change_time="12:00:00",
            additional_fields=[
                {"tag": "_CUSTOM", "value": "custom value", "details": []}
            ],
        )
        view = self.viewer.entity_view_manager.views["submitter"]
        view.display(submitter)

        self.assertEqual(view.title_label.cget("text"), "Jean Dupont")
        details = view.sections[self.viewer.translator.get("view.submitter_details")]
        self.assertIn(
            (self.viewer.translator.get("view.address"), submitter.address),
            view._section_rows[details],
        )
        for label_key, value in (
            ("view.address_line", submitter.address_line_1),
            ("view.additional_address_2", submitter.address_line_2),
            ("view.city", submitter.city),
            ("view.state_country", submitter.state),
            ("view.postal_code", submitter.postal_code),
            ("view.country", submitter.country),
            ("view.registered_number", submitter.registered_number),
            ("view.internal_id", submitter.record_id),
            ("view.restriction", submitter.restriction),
            ("view.change_date", submitter.change_date),
            ("view.change_time", submitter.change_time),
        ):
            self.assertIn(
                (self.viewer.translator.get(label_key), value),
                view._section_rows[details],
            )
        contacts = view.sections[self.viewer.translator.get("view.contact_information")]
        contact_rows = view._section_rows[contacts]
        for label_key, value in (
            ("view.phone", "01 02 03 04"),
            ("view.phone", "+33 6 11 22 33"),
            ("view.email", "jean@example.org"),
            ("view.email", "contact@example.org"),
            ("view.fax", "03 20 00 00 01"),
            ("view.website", "https://example.org"),
            ("view.language", "French"),
            ("view.language", "English"),
        ):
            self.assertIn((self.viewer.translator.get(label_key), value), contact_rows)
        additional = view.sections[self.viewer.translator.get("view.additional_fields")]
        self.assertIn(("_CUSTOM", "custom value"), view._section_rows[additional])

    # Vérifie note view displays text metadata and links.
    def test_note_view_displays_text_metadata_and_links(self):
        note_text = "Consulter https://example.org/note\nSuite de la note"
        note = SimpleNamespace(
            pointer="@N50@",
            text=note_text,
            source="@S51@",
            sources=["@S51@"],
            references=["REF-1"],
            record_id="NOTE-50",
            submitters=["@M51@"],
            change_date="1 JAN 2020",
            change_time="12:00:00",
            additional_fields=[{"tag": "_CUSTOM", "value": "value", "details": []}],
        )
        view = self.viewer.entity_view_manager.views["note"]
        view.display(note)

        self.assertEqual(self._widget_text(view.text_widget), note_text)
        self.assertTrue(view.text_widget.tag_ranges("url"))
        details = view.sections[self.viewer.translator.get("view.note_details")]
        self.assertIn(
            (self.viewer.translator.get("view.internal_id"), "NOTE-50"),
            view._section_rows[details],
        )
        self.assertIn("@S51@", view.links)
        self.assertIn("@M51@", view.links)
        additional = view.sections[self.viewer.translator.get("view.additional_fields")]
        self.assertIn(("_CUSTOM", "value"), view._section_rows[additional])

    # Vérifie source view displays sections links and copyable data.
    def test_source_view_displays_sections_links_and_copyable_data(self):
        view = self.viewer.entity_view_manager.views["source"]
        repository = SimpleNamespace(
            name="Archives de Paris",
            entity=SimpleNamespace(tag="REPO"),
        )
        view.set_pointer_resolver(
            lambda pointer: repository if pointer == "@R1@" else None
        )
        view.set_display_name_resolver(
            lambda entity, entity_type=None: getattr(entity, "name", "")
            or getattr(entity, "title", "")
        )

        source_text = "Description longue de la source"
        data_text = "Événement de recensement\nSuite de l’événement"
        source = SimpleNamespace(
            pointer="@S1@",
            title="Recensement de Paris",
            author="Archives municipales",
            pub_date="1901",
            publication="Registre paroissial",
            abbreviation="RP",
            agency="Commune de Paris",
            record_id="R-1901",
            repository="@R1@",
            call_number="1E 20",
            media="Microfilm",
            repo_note="Salle 4",
            text=source_text,
            notes=["Note sur la source"],
            sources=["@S2@"],
            references=["Shelf 7"],
            data_events=[
                {
                    "value": "Dénombrement",
                    "details": [
                        ("DATE", "1 JAN 1901"),
                        ("TEXT", "Événement de recensement"),
                        ("CONT", "Suite de l’événement"),
                    ],
                }
            ],
            additional_fields=[
                {"tag": "_CUSTOM", "value": "Valeur étendue", "details": []}
            ],
        )
        view.display(source)

        self.assertEqual(type(view).__name__, "SourcePropertyView")
        self.assertEqual(view.title_label.cget("text"), "Recensement de Paris")
        for key in (
            "view.source_bibliography",
            "view.source_repository",
            "view.source_content",
            "view.data_events",
            "view.notes",
            "view.source_links",
            "view.references",
            "view.additional_fields",
        ):
            self.assertIn(self.viewer.translator.get(key), view.sections)

        self.assertIn("@R1@", view.links)
        self.assertIn("Archives de Paris", self._widget_text(view.links["@R1@"][0]))
        self.assertIn("@S2@", view.links)
        data_values = [
            self._widget_text(widget)
            for widget in view.sections[
                self.viewer.translator.get("view.data_events")
            ].winfo_children()
        ]
        self.assertIn(data_text, data_values)
        self.assertIn(
            "_CUSTOM", [self._widget_text(widget) for widget in view.tag_widgets]
        )

        content = view.sections[self.viewer.translator.get("view.source_content")]
        view.section_copy_buttons[content].invoke()
        copied = self.root.clipboard_get()
        self.assertIn(source_text, copied)

    # Vérifie submitter view displays multiple phones and emails.
    def test_submitter_view_displays_multiple_phones_and_emails(self):
        class DummySubmitter:
            pointer = "@M1@"
            name = "Submitter"
            address = None
            phone = "legacy-phone"
            email = "legacy-email"
            phones = ["01 02 03 04 05", "06 07 08 09 10"]
            emails = ["first@example.org", "second@example.org"]

        self.viewer.entity_view_manager.views["submitter"].display(DummySubmitter())

        contacts = self.viewer.entity_view_manager.views["submitter"].sections[
            self.viewer.translator.get("view.contact_information")
        ]
        contact_rows = self.viewer.entity_view_manager.views["submitter"]._section_rows[
            contacts
        ]
        phone_values = [
            value
            for label, value in contact_rows
            if label == self.viewer.translator.get("view.phone")
        ]
        email_values = [
            value
            for label, value in contact_rows
            if label == self.viewer.translator.get("view.email")
        ]
        self.assertIn("01 02 03 04 05", phone_values)
        self.assertIn("06 07 08 09 10", phone_values)
        self.assertIn("first@example.org", email_values)
        self.assertIn("second@example.org", email_values)

    # Vérifie individual view pointer click calls callback.
    def test_individual_view_pointer_click_calls_callback(self):
        callback = Mock()
        self.viewer.entity_view_manager.views[
            "individual"
        ].on_pointer_click_callback = callback
        self.viewer.controller.get_family.return_value = None

        class DummyIndividual:
            pointer = "@I1@"
            famc = None
            fams = ["@F1@"]

        individual = DummyIndividual()
        self.viewer.entity_view_manager.views["individual"].display(individual)
        link = self.viewer.entity_view_manager.views["individual"].links["@F1@"][0]
        self.assertIn("pointer", link.tag_names("1.0"))
        self.viewer.entity_view_manager.views["individual"]._navigate_pointer("@F1@")

        callback.assert_called_once_with("@F1@")

    # Vérifie individual view famc and fams click callback.
    def test_individual_view_famc_and_fams_click_callback(self):
        callback = Mock()
        self.viewer.entity_view_manager.views[
            "individual"
        ].on_pointer_click_callback = callback
        self.viewer.controller.get_family.return_value = None

        class DummyIndividual:
            pointer = "@I1@"
            famc = "@F0@"
            famc_links = [{"pointer": "@F0@", "details": [("PEDI", "adopted")]}]
            fams = ["@F1@", "@F2@"]

        individual = DummyIndividual()
        self.viewer.entity_view_manager.views["individual"].display(individual)
        self.assertIn(
            "pointer",
            self.viewer.entity_view_manager.views["individual"]
            .links["@F0@"][0]
            .tag_names("1.0"),
        )
        self.assertIn(
            "pointer",
            self.viewer.entity_view_manager.views["individual"]
            .links["@F2@"][0]
            .tag_names("1.0"),
        )
        family_section = self.viewer.entity_view_manager.views["individual"].sections[
            self.viewer.translator.get("view.individual_family_links")
        ]
        self.assertIn(
            (self.viewer.translator.get("view.pedigree"), "adopted"),
            self.viewer.entity_view_manager.views["individual"]._section_rows[
                family_section
            ],
        )
        self.viewer.entity_view_manager.views["individual"]._navigate_pointer("@F0@")
        self.viewer.entity_view_manager.views["individual"]._navigate_pointer("@F2@")

        callback.assert_has_calls([call("@F0@"), call("@F2@")], any_order=True)

    # Vérifie individual view family links include names.
    def test_individual_view_family_links_include_names(self):
        families = {
            "@F0@": type(
                "DummyFamily",
                (),
                {
                    "pointer": "@F0@",
                    "husband": "@I1@",
                    "wife": "@I2@",
                    "entity": SimpleNamespace(tag="FAM"),
                },
            )(),
            "@F1@": type(
                "DummyFamily",
                (),
                {
                    "pointer": "@F1@",
                    "husband": "@I3@",
                    "wife": "@I4@",
                    "entity": SimpleNamespace(tag="FAM"),
                },
            )(),
        }
        individuals = {
            "@I1@": type("DummyIndividual", (), {"name": "Jean"})(),
            "@I2@": type("DummyIndividual", (), {"name": "Claire"})(),
            "@I3@": type("DummyIndividual", (), {"name": "Paul"})(),
            "@I4@": type("DummyIndividual", (), {"name": "Anne"})(),
        }

        def member_resolver(pointer):
            return individuals.get(pointer)

        def names_for(entity):
            husband = member_resolver(getattr(entity, "husband", None))
            wife = member_resolver(getattr(entity, "wife", None))
            return " & ".join(p.name for p in (husband, wife) if p)

        def display_name_resolver(entity, entity_type=None):
            return names_for(entity) or entity.pointer

        self.viewer.entity_view_manager.views["individual"].set_family_name_resolver(
            families.get
        )
        self.viewer.entity_view_manager.views["individual"].set_pointer_resolver(
            families.get
        )
        self.viewer.entity_view_manager.views["individual"].set_family_member_resolver(
            member_resolver
        )
        self.viewer.entity_view_manager.views[
            "individual"
        ].set_family_display_name_resolver(display_name_resolver)

        class DummyIndividual:
            pointer = "@I9@"
            famc = "@F0@"
            fams = ["@F1@"]

        self.viewer.entity_view_manager.views["individual"].display(DummyIndividual())
        self.assertIn(
            "Jean",
            self._widget_text(
                self.viewer.entity_view_manager.views["individual"].links["@F0@"][0]
            ),
        )
        self.assertIn(
            "Paul",
            self._widget_text(
                self.viewer.entity_view_manager.views["individual"].links["@F1@"][0]
            ),
        )

    # Vérifie family view children click calls callback.
    def test_family_view_children_click_calls_callback(self):
        callback = Mock()
        self.viewer.entity_view_manager.views["family"].on_pointer_click_callback = (
            callback
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

        family = DummyFamily()
        self.viewer.entity_view_manager.views["family"].display(family)
        self.assertIn("@I3@", self.viewer.entity_view_manager.views["family"].links)
        self.viewer.entity_view_manager.views["family"]._navigate_pointer("@I3@")

        callback.assert_called_once_with("@I3@")

    # Vérifie family view parents click calls callback.
    def test_family_view_parents_click_calls_callback(self):
        callback = Mock()
        self.viewer.entity_view_manager.views["family"].on_pointer_click_callback = (
            callback
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

        family = DummyFamily()
        self.viewer.entity_view_manager.views["family"].display(family)
        self.assertIn("@I1@", self.viewer.entity_view_manager.views["family"].links)
        self.assertIn("@I2@", self.viewer.entity_view_manager.views["family"].links)
        self.viewer.entity_view_manager.views["family"]._navigate_pointer("@I1@")
        self.viewer.entity_view_manager.views["family"]._navigate_pointer("@I2@")

        callback.assert_has_calls([call("@I1@"), call("@I2@")], any_order=True)

    # Vérifie family view displays names for parents and children.
    def test_family_view_displays_names_for_parents_and_children(self):
        callback = Mock()
        self.viewer.entity_view_manager.views["family"].on_pointer_click_callback = (
            callback
        )
        self.viewer.entity_view_manager.views["family"].set_pointer_resolver(None)

        class DummyIndividual:
            def __init__(self, pointer, name):
                self.pointer = pointer
                self.name = name

        self.viewer.entity_view_manager.views["family"].set_name_resolver(
            lambda pointer: {
                "@I1@": DummyIndividual("@I1@", "Marcel/ANSELIN/"),
                "@I2@": DummyIndividual("@I2@", "/BIROT/Angèle"),
                "@I3@": DummyIndividual("@I3@", "Jean/LENCARTÉ/"),
                "@I4@": DummyIndividual("@I4@", "Cunégonde"),
            }.get(pointer)
        )
        self.viewer.entity_view_manager.views["family"].set_display_name_resolver(
            lambda entity, entity_type=None: entity.name
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

        self.viewer.entity_view_manager.views["family"].display(DummyFamily())

        family_links = self.viewer.entity_view_manager.views["family"].links
        self.assertIn("Marcel/ANSELIN/", self._widget_text(family_links["@I1@"][0]))
        self.assertIn("/BIROT/Angèle", self._widget_text(family_links["@I2@"][0]))
        self.assertIn("Jean/LENCARTÉ/", self._widget_text(family_links["@I3@"][0]))
        self.assertIn("Cunégonde", self._widget_text(family_links["@I4@"][0]))

    # Vérifie family view children display.
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
        self.viewer.entity_view_manager.views["family"].display(family)
        self.assertIn("@I3@", self.viewer.entity_view_manager.views["family"].links)
        self.assertIn("@I4@", self.viewer.entity_view_manager.views["family"].links)

    # Vérifie family view displays multiple marriages.
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

        self.viewer.entity_view_manager.views["family"].display(DummyFamily())
        marriages = self.viewer.entity_view_manager.views["family"].sections[
            self.viewer.translator.get("view.marriages")
        ]
        marriage_values = [
            self._widget_text(widget) for widget in marriages.winfo_children()
        ]
        self.assertIn("1900", marriage_values)
        self.assertIn("1920", marriage_values)

    # Vérifie family view displays all structured sections and copies marriage.
    def test_family_view_displays_all_structured_sections_and_copies_marriage(self):
        view = self.viewer.entity_view_manager.views["family"]
        full_marriage_text = (
            "Texte initial complété\nContinuation sur la ligne suivante\nDernière ligne"
        )
        full_first_note = "Première note de l’acte\nsuite de la note collée"
        full_second_note = "Deuxième note\navec sa continuation"
        view.display(
            SimpleNamespace(
                pointer="@F25@",
                husband="@I50@",
                wife="@I51@",
                children=["@I52@"],
                number_of_children=1,
                marriages=[
                    {
                        "tag": "MARR",
                        "value": "",
                        "details": [
                            ("DATE", "1900"),
                            ("PLAC", "Paris"),
                            ("MAP", ""),
                            ("LATI", "N48.8"),
                            ("LONG", "E2.3"),
                            ("TEXT", "Texte initial"),
                            ("CONC", " complété"),
                            ("CONT", "Continuation sur la ligne suivante"),
                            ("CONT", "Dernière ligne"),
                            ("NOTE", "Première note de l’acte"),
                            ("CONT", "suite de la note"),
                            ("CONC", " collée"),
                            ("NOTE", "Deuxième note"),
                            ("CONT", "avec sa continuation"),
                        ],
                    },
                    {"tag": "MARR", "value": "", "details": [("DATE", "1920")]},
                ],
                divorces=[{"tag": "DIV", "value": "", "details": [("DATE", "1930")]}],
                events=[{"tag": "EVEN", "value": "Contrat", "children": []}],
                notes=["Note de famille"],
                sources=["@S50@"],
                additional_fields=[
                    {
                        "tag": "CHAN",
                        "value": "",
                        "details": [("DATE", "1 JAN 1900"), ("TIME", "12:30:00")],
                    },
                    {"tag": "_CUSTOM", "value": "Valeur", "details": []},
                ],
            )
        )

        section_titles = set(view.sections)
        for key in (
            "view.family_members",
            "view.children",
            "view.marriages",
            "view.divorces",
            "view.events",
            "view.notes",
            "view.sources",
            "view.additional_fields",
        ):
            self.assertIn(self.viewer.translator.get(key), section_titles)

        marriage_section = view.sections[self.viewer.translator.get("view.marriages")]
        marriage_values = [
            self._widget_text(widget) for widget in marriage_section.winfo_children()
        ]
        self.assertIn(full_marriage_text, marriage_values)
        self.assertIn(full_first_note, marriage_values)
        self.assertIn(full_second_note, marriage_values)
        self.assertIn(
            self.viewer.translator.get("view.map_coordinates"), marriage_values
        )
        self.assertIn(self.viewer.translator.get("view.latitude"), marriage_values)
        self.assertIn(self.viewer.translator.get("view.longitude"), marriage_values)
        additional = view.sections[self.viewer.translator.get("view.additional_fields")]
        additional_labels = [
            self._widget_text(widget)
            for widget in additional.winfo_children()
            if widget in view.tag_widgets
        ]
        self.assertIn(
            self.viewer.translator.get("view.change_information"), additional_labels
        )
        self.assertIn(self.viewer.translator.get("view.time"), additional_labels)
        self.assertNotIn(
            self.viewer.translator.get("view.continuation"), marriage_values
        )
        self.assertEqual(
            marriage_values.count(self.viewer.translator.get("view.text")), 1
        )
        view.section_copy_buttons[marriage_section].invoke()
        copied = self.root.clipboard_get()
        self.assertIn("1900", copied)
        self.assertIn("Paris", copied)
        self.assertIn("1920", copied)
        self.assertIn(full_marriage_text, copied)
        self.assertIn(full_first_note, copied)
        self.assertIn(full_second_note, copied)
