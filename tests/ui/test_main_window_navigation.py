"""Tests de navigation et de sélection de la fenêtre principale."""

import tkinter as tk
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from tests.main_window_test_case import GedcomViewerTestCase
from ui.entity_navigator import EntityNavigator


class TestGedcomViewerNavigation(GedcomViewerTestCase):
    """Vérifie la navigation, les sélections et l'historique."""

    # Vérifie entity navigator tracks history and display.
    def test_entity_navigator_tracks_history_and_display(self):
        class DummyEntity:
            pointer = "@I1@"

        target = DummyEntity()
        context = {
            "type": "individual",
            "entity": target,
            "raw_entity": target,
            "raw_block": "0 @I1@ INDI",
        }
        controller = Mock()
        controller.is_loaded.return_value = True
        controller.resolve_pointer.return_value = target
        controller.get_entity_display_info.return_value = context
        displayed = []

        navigator = EntityNavigator(
            controller=controller,
            history=self.viewer._navigation_history,
            on_display=lambda ctx: displayed.append(ctx),
            on_error=lambda *args, **kwargs: None,
        )

        navigator.navigate_to("@I1@")

        self.assertEqual(len(self.viewer._navigation_history.entries), 1)
        self.assertEqual(displayed[0]["raw_block"], "0 @I1@ INDI")

    # Vérifie detail view resolvers use replaced controller.
    def test_detail_view_resolvers_use_replaced_controller(self):
        replacement_controller = Mock()
        self.viewer.controller = replacement_controller

        self.viewer.entity_view_manager.views["individual"].family_name_resolver("@F1@")

        replacement_controller.get_family.assert_called_once_with("@F1@")

    # Vérifie clear search clears filter.
    def test_clear_search_clears_filter(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.get_entity_types.return_value = []
        self.viewer.entity_browser.search_var.set("Doe")

        self.assertEqual(
            self.viewer.entity_browser.clear_search_button.cget("style"),
            "ClearSearch.TButton",
        )
        self.viewer.entity_browser.clear_search_button.invoke()

        self.assertEqual(self.viewer.entity_browser.search_var.get(), "")

    # Vérifie filter entities debounces refresh.
    def test_filter_entities_debounces_refresh(self):
        self.viewer.controller.is_loaded.return_value = True
        with patch.object(self.viewer.root, "after", return_value="search-id"):
            self.viewer.filter_entities()

        self.assertEqual(self.viewer.entity_browser._search_after_id, "search-id")

        with patch.object(self.viewer.root, "after_cancel") as cancel:
            with patch.object(self.viewer.root, "after", return_value="next-search-id"):
                self.viewer.filter_entities()

        cancel.assert_called_once_with("search-id")
        self.assertEqual(self.viewer.entity_browser._search_after_id, "next-search-id")

    # Vérifie entity browser lists with replaced controller.
    def test_entity_browser_lists_with_replaced_controller(self):
        class DummyEntity:
            pointer = "@I2@"

        replacement_controller = Mock()
        replacement_controller.is_loaded.return_value = True
        replacement_controller.get_entity_types.return_value = ["INDI"]
        replacement_controller.get_entity_list_items.return_value = [
            (DummyEntity(), "@I2@")
        ]
        replacement_controller.format_entity_display_name.return_value = "Test Person"
        self.viewer.controller = replacement_controller

        self.viewer.entity_type_var.set("INDI")

        replacement_controller.get_entity_list_items.assert_called_once_with("INDI", "")
        self.assertEqual(
            self.viewer.entity_browser.entity_tree.item("0", "values"),
            ("Test Person", "@I2@"),
        )

    # Vérifie loading file selects and displays first entity.
    def test_loading_file_selects_and_displays_first_entity(self):
        first_individual = SimpleNamespace(pointer="@I1@")
        replacement_controller = Mock()
        replacement_controller.is_loaded.return_value = True
        replacement_controller.get_entity_types.return_value = ["INDI"]
        replacement_controller.get_all_entity_type_menu_display_items.return_value = [
            ("Individual", "INDI")
        ]
        replacement_controller.get_entity_list_items.return_value = [
            (first_individual, "@I1@")
        ]
        replacement_controller.format_entity_display_name.return_value = "First person"
        replacement_controller.get_entity_display_info.return_value = {
            "entity": first_individual
        }
        self.viewer.controller = replacement_controller

        with patch.object(self.viewer, "display_entity_context") as display_context:
            self.viewer.entity_type_var.set("INDI")
            self.root.update()
            display_context.assert_called_once_with({"entity": first_individual})
            display_context.reset_mock()
            replacement_controller.get_entity_list_items.reset_mock()

            self.viewer._apply_loaded_file("/tmp/loaded.ged", 0)
            self.root.update()

        self.assertEqual(self.viewer.entity_type_var.get(), "INDI")
        self.assertEqual(self.viewer.entity_browser.entity_tree.selection(), ("0",))
        replacement_controller.get_entity_list_items.assert_called_once_with("INDI", "")
        display_context.assert_called_once_with({"entity": first_individual})

    # Vérifie entity type change selects and displays first item.
    def test_entity_type_change_selects_and_displays_first_item(self):
        first_individual = SimpleNamespace(pointer="@I1@")
        first_family = SimpleNamespace(pointer="@F1@")
        replacement_controller = Mock()
        replacement_controller.is_loaded.return_value = True
        replacement_controller.get_entity_types.return_value = ["INDI", "FAM"]
        replacement_controller.get_entity_list_items.side_effect = {
            "INDI": [(first_individual, "@I1@")],
            "FAM": [(first_family, "@F1@")],
        }.get
        replacement_controller.format_entity_display_name.side_effect = (
            lambda entity, _entity_type: entity.pointer
        )
        replacement_controller.get_entity_display_info.side_effect = lambda entity: {
            "entity": entity
        }
        self.viewer.controller = replacement_controller

        with patch.object(self.viewer, "display_entity_context") as display_context:
            self.viewer.entity_type_var.set("INDI")
            self.root.update()

            self.assertEqual(self.viewer.entity_browser.entity_tree.selection(), ("0",))
            display_context.assert_called_once_with({"entity": first_individual})

            display_context.reset_mock()
            self.viewer.entity_type_var.set("FAM")
            self.root.update()

            self.assertEqual(self.viewer.entity_browser.entity_tree.selection(), ("0",))
            display_context.assert_called_once_with({"entity": first_family})

    # Vérifie entity type change restores last selection for each type.
    def test_entity_type_change_restores_last_selection_for_each_type(self):
        entity_types = ["INDI", "FAM", "SOUR", "REPO", "NOTE", "OBJE", "SUBM", "CITE"]
        entities_by_type = {
            entity_type: [
                SimpleNamespace(
                    pointer=("@S1@" if entity_type == "CITE" else f"@{entity_type}1@"),
                    name=f"{entity_type} first",
                    entity_type=entity_type,
                    raw_block=(
                        "2 SOUR @S1@\n3 PAGE first\n"
                        if entity_type == "CITE"
                        else f"0 @{entity_type}1@ {entity_type}\n1 NOTE first\n"
                    ),
                ),
                SimpleNamespace(
                    pointer=("@S1@" if entity_type == "CITE" else f"@{entity_type}2@"),
                    name=f"{entity_type} second",
                    entity_type=entity_type,
                    raw_block=(
                        "2 SOUR @S1@\n3 PAGE second\n"
                        if entity_type == "CITE"
                        else f"0 @{entity_type}2@ {entity_type}\n1 NOTE second\n"
                    ),
                ),
            ]
            for entity_type in entity_types
        }
        context_types = {
            "INDI": "individual",
            "FAM": "family",
            "SOUR": "source",
            "REPO": "repository",
            "NOTE": "note",
            "OBJE": "object",
            "SUBM": "submitter",
            "CITE": "citation",
        }
        replacement_controller = Mock()
        replacement_controller.is_loaded.return_value = True
        replacement_controller.get_entity_types.return_value = entity_types
        replacement_controller.get_entity_list_items.side_effect = (
            lambda entity_type, _query: [
                (entity, entity.pointer) for entity in entities_by_type[entity_type]
            ]
        )
        replacement_controller.format_entity_display_name.side_effect = (
            lambda entity, _entity_type: entity.name
        )
        replacement_controller.get_entity_display_info.side_effect = lambda entity: {
            "type": context_types[entity.entity_type],
            "entity": entity,
            "raw_entity": entity,
            "raw_block": entity.raw_block,
        }
        replacement_controller.format_entity_summary.return_value = {
            "title": "",
            "subtitle": "",
            "facts": [],
        }
        self.viewer.controller = replacement_controller

        with patch.object(self.viewer.entity_view_manager, "show"):
            for entity_type in entity_types:
                self.viewer.entity_type_var.set(entity_type)
                self.root.update()
                self.assertEqual(
                    self.viewer.entity_browser.entity_tree.selection(), ("0",)
                )
                self.assertEqual(
                    self.viewer.detail_panel.text_area.get("1.0", tk.END).strip(),
                    self.viewer.detail_panel._format_gedcom_block(
                        entities_by_type[entity_type][0].raw_block
                    ).strip(),
                )

                self.viewer.entity_browser.entity_tree.selection_set("1")
                self.root.update()
                self.assertIs(
                    self.viewer.entity_browser.get_entity("1"),
                    entities_by_type[entity_type][1],
                )
                self.assertEqual(
                    self.viewer.detail_panel.text_area.get("1.0", tk.END).strip(),
                    self.viewer.detail_panel._format_gedcom_block(
                        entities_by_type[entity_type][1].raw_block
                    ).strip(),
                )

            for entity_type in entity_types:
                self.viewer.entity_type_var.set(entity_type)
                self.root.update()

                selected_item = self.viewer.entity_browser.entity_tree.selection()[0]
                self.assertIs(
                    self.viewer.entity_browser.get_entity(selected_item),
                    entities_by_type[entity_type][1],
                    entity_type,
                )
                self.assertEqual(
                    self.viewer.detail_panel.text_area.get("1.0", tk.END).strip(),
                    self.viewer.detail_panel._format_gedcom_block(
                        entities_by_type[entity_type][1].raw_block
                    ).strip(),
                    entity_type,
                )

        self.assertEqual(
            entities_by_type["CITE"][0].pointer,
            entities_by_type["CITE"][1].pointer,
        )

    # Vérifie selecting citation displays only its own details.
    def test_selecting_citation_displays_only_its_own_details(self):
        citation = type(
            "CitationItem",
            (),
            {
                "source_pointer": "@S1@",
                "raw_block": "2 SOUR @S1@\n3 PAGE 17\n",
            },
        )()
        self.viewer.controller.is_loaded.return_value = False
        self.viewer.entity_type_var.set("CITE")
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.entity_browser.entity_tree.insert(
            "", "end", iid="citation-0", values=("Source", "@S1@")
        )
        self.viewer.entity_browser.entity_tree.selection_set("citation-0")
        self.viewer.entity_browser._entity_by_item_id["citation-0"] = citation
        context = {
            "type": "citation",
            "entity": citation,
            "raw_entity": citation,
            "raw_block": citation.raw_block,
        }
        self.viewer.controller.get_entity_display_info.return_value = context

        with patch.object(self.viewer, "display_entity_context") as display_context:
            self.viewer.show_entity(None)

        self.viewer.controller.get_source.assert_not_called()
        self.viewer.controller.get_entity_display_info.assert_called_once_with(citation)
        display_context.assert_called_once_with(context)

    # Vérifie citation view shows citation fields not source record.
    def test_citation_view_shows_citation_fields_not_source_record(self):
        source = SimpleNamespace(
            title="Registre paroissial",
            entity=SimpleNamespace(tag="SOUR"),
        )
        owner = SimpleNamespace(
            name="Jean /DUPONT/",
            entity=SimpleNamespace(tag="INDI"),
        )
        callback = Mock()
        view = self.viewer.entity_view_manager.views["citation"]
        view.on_pointer_click_callback = callback
        view.set_pointer_resolver(
            lambda pointer: {"@S1@": source, "@X1@": owner}.get(pointer)
        )
        view.set_display_name_resolver(
            lambda entity, entity_type=None: (
                "Registre paroissial" if entity_type == "SOUR" else "Jean Dupont"
            )
        )
        citation = type(
            "CitationItem",
            (),
            {
                "pointer": "@S1@",
                "source_pointer": "@S1@",
                "owner_pointer": "@X1@",
                "owner_type": "INDI",
                "context_tag": "BIRT",
                "level": 2,
                "details": [
                    {"tag": "PAGE", "value": "17", "level": 1},
                    {"tag": "EVEN/ROLE", "value": "Witness", "level": 2},
                    {
                        "tag": "DATA/EVEN/TEXT",
                        "value": "Citation text\ncontinued here and continued inline",
                        "level": 3,
                    },
                ],
                "raw_block": "2 SOUR @S1@\n3 PAGE 17\n4 ROLE Witness\n",
                "page": "17",
            },
        )()

        view.display(citation)

        self.assertEqual(type(view).__name__, "CitationPropertyView")
        self.assertIn("Registre paroissial", view.title_label.cget("text"))
        self.assertIn("Jean Dupont", view.title_label.cget("text"))
        self.assertIn("@S1@", view.links)
        self.assertIn("@X1@", view.links)

        information = view.sections[
            self.viewer.translator.get("view.citation_information")
        ]
        information_values = [
            self._widget_text(widget) for widget in information.winfo_children()
        ]
        self.assertIn("17", information_values)
        self.assertIn(self.viewer.translator.get("view.birth_date"), information_values)

        details = view.sections[self.viewer.translator.get("view.citation_details")]
        detail_values = [
            self._widget_text(widget) for widget in details.winfo_children()
        ]
        self.assertIn("Witness", detail_values)
        full_text = "Citation text\ncontinued here and continued inline"
        self.assertIn(full_text, detail_values)
        self.assertNotIn("continued here", detail_values)
        self.assertIn(
            " / ".join(
                (
                    self.viewer.translator.get("view.events"),
                    self.viewer.translator.get("view.role"),
                )
            ),
            detail_values,
        )
        view.section_copy_buttons[details].invoke()
        self.assertIn(full_text, self.root.clipboard_get())
        view._navigate_pointer("@S1@")
        view._navigate_pointer("@X1@")
        callback.assert_has_calls([call("@S1@"), call("@X1@")], any_order=True)

    # Vérifie show header displays head block.
    def test_show_header_displays_head_block(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.extract_head.return_value = "0 HEAD\n1 SOUR GEDCOM"

        self.viewer.show_header()

        content = self.viewer.detail_panel.text_area.get("1.0", tk.END).strip()
        self.assertEqual(content, "0 HEAD\n  1 SOUR GEDCOM")
        self.viewer.highlighter.highlight.assert_called_once()

    # Vérifie show header shows error when missing.
    def test_show_header_shows_error_when_missing(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.extract_head.return_value = ""

        with patch("ui.main_window.messagebox.showerror") as showerror:
            self.viewer.show_header()
            showerror.assert_called_once_with(
                self.viewer.translator.get("ui.error"),
                self.viewer.translator.get("ui.no_header"),
            )

    # Vérifie show trailer displays trailer block.
    def test_show_trailer_displays_trailer_block(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.extract_trailer.return_value = "0 TRLR"

        self.viewer.show_trailer()

        content = self.viewer.detail_panel.text_area.get("1.0", tk.END).strip()
        self.assertEqual(content, "0 TRLR")
        self.viewer.highlighter.highlight.assert_called_once()

    # Vérifie show trailer shows error when missing.
    def test_show_trailer_shows_error_when_missing(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.extract_trailer.return_value = ""

        with patch("ui.main_window.messagebox.showerror") as showerror:
            self.viewer.show_trailer()
            showerror.assert_called_once_with(
                self.viewer.translator.get("ui.error"),
                self.viewer.translator.get("ui.no_trailer"),
            )

    # Vérifie navigate to displays entity context.
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

        content = self.viewer.detail_panel.text_area.get("1.0", tk.END).strip()
        self.assertEqual(content, "0 @I1@ INDI")
        self.viewer.highlighter.highlight.assert_called_once()

    # Vérifie navigate to syncs entity type list and selection.
    def test_navigate_to_syncs_entity_type_list_and_selection(self):
        individual = SimpleNamespace(pointer="@I1@")
        first_family = SimpleNamespace(pointer="@F1@")
        target_family = SimpleNamespace(
            pointer="@F2@",
            husband=None,
            wife=None,
            children=[],
            number_of_children=None,
            marriages=[],
            divorces=[],
            events=[],
            notes=[],
            sources=[],
            additional_fields=[],
        )
        entities_by_pointer = {
            entity.pointer: entity
            for entity in (individual, first_family, target_family)
        }
        controller = Mock()
        controller.is_loaded.return_value = True
        controller.get_entity_types.return_value = ["INDI", "FAM"]
        controller.get_entity_list_items.side_effect = lambda entity_type, _query: [
            (entity, entity.pointer)
            for entity in (
                [individual] if entity_type == "INDI" else [first_family, target_family]
            )
        ]
        controller.format_entity_display_name.side_effect = (
            lambda entity, _entity_type: entity.pointer
        )
        controller.resolve_pointer.side_effect = entities_by_pointer.get
        controller.format_entity_summary.return_value = {
            "title": "",
            "subtitle": "",
            "facts": [],
        }
        contexts = {
            "@I1@": {
                "type": "individual",
                "entity": individual,
                "raw_entity": None,
                "raw_block": "0 @I1@ INDI",
            },
            "@F1@": {
                "type": "family",
                "entity": first_family,
                "raw_entity": None,
                "raw_block": "0 @F1@ FAM",
            },
            "@F2@": {
                "type": "family",
                "entity": target_family,
                "raw_entity": None,
                "raw_block": "0 @F2@ FAM",
            },
        }
        controller.get_entity_display_info.side_effect = lambda entity: contexts[
            entity.pointer
        ]
        self.viewer.controller = controller

        self.viewer.entity_type_var.set("INDI")
        self.root.update()
        self.viewer._navigation_history.reset()

        self.viewer.navigate_to("@F2@")
        self.root.update()

        self.assertEqual(self.viewer.entity_type_var.get(), "FAM")
        self.assertEqual(self.viewer.entity_browser.entity_tree.selection(), ("1",))
        self.assertIs(self.viewer.entity_browser.get_entity("1"), target_family)
        self.assertEqual(
            self.viewer.detail_panel.text_area.get("1.0", tk.END).strip(), "0 @F2@ FAM"
        )
        self.assertEqual(
            self.viewer.entity_view_manager.views["family"].title_label.cget("text"),
            self.viewer.translator.get("view.family"),
        )
        self.assertEqual(len(self.viewer._navigation_history.entries), 1)

        self.viewer.navigate_to("@I1@")
        self.root.update()
        self.assertEqual(self.viewer.entity_type_var.get(), "INDI")
        self.assertEqual(self.viewer.entity_browser.entity_tree.selection(), ("0",))
        self.assertEqual(len(self.viewer._navigation_history.entries), 2)

        self.viewer.go_back()
        self.root.update()
        self.assertEqual(self.viewer.entity_type_var.get(), "FAM")
        self.assertEqual(self.viewer.entity_browser.entity_tree.selection(), ("1",))
        self.assertEqual(self.viewer._navigation_history.index, 0)

        self.viewer.go_forward()
        self.root.update()
        self.assertEqual(self.viewer.entity_type_var.get(), "INDI")
        self.assertEqual(self.viewer.entity_browser.entity_tree.selection(), ("0",))
        self.assertEqual(self.viewer._navigation_history.index, 1)

    # Vérifie citation navigation selects the exact occurrence.
    def test_citation_navigation_selects_the_exact_occurrence(self):
        first_citation = SimpleNamespace(
            pointer="@S1@",
            source_pointer="@S1@",
            owner_pointer="@I1@",
            owner_type="INDI",
            context_tag="BIRT",
            level=2,
            page="1",
            details=[],
            raw_block="2 SOUR @S1@\n3 PAGE 1\n",
        )
        second_citation = SimpleNamespace(
            pointer="@S1@",
            source_pointer="@S1@",
            owner_pointer="@I2@",
            owner_type="INDI",
            context_tag="DEAT",
            level=2,
            page="2",
            details=[],
            raw_block="2 SOUR @S1@\n3 PAGE 2\n",
        )
        controller = Mock()
        controller.is_loaded.return_value = True
        controller.get_entity_types.return_value = ["CITE"]
        controller.get_entity_list_items.return_value = [
            (first_citation, first_citation.pointer),
            (second_citation, second_citation.pointer),
        ]
        controller.format_entity_display_name.side_effect = (
            lambda citation, _entity_type: citation.owner_pointer
        )
        controller.format_entity_summary.return_value = {
            "title": "",
            "subtitle": "",
            "facts": [],
        }
        self.viewer.controller = controller

        self.viewer.entity_type_var.set("CITE")
        self.root.update()
        self.assertEqual(self.viewer.entity_browser.entity_tree.selection(), ("0",))
        self.viewer._navigation_history.reset()
        self.viewer.display_entity_context(
            {
                "type": "citation",
                "entity": first_citation,
                "raw_entity": None,
                "raw_block": first_citation.raw_block,
            }
        )

        self.viewer.display_entity_context(
            {
                "type": "citation",
                "entity": second_citation,
                "raw_entity": None,
                "raw_block": second_citation.raw_block,
            }
        )
        self.root.update()

        self.assertEqual(self.viewer.entity_type_var.get(), "CITE")
        self.assertEqual(self.viewer.entity_browser.entity_tree.selection(), ("1",))
        self.assertEqual(len(self.viewer._navigation_history.entries), 2)

        self.viewer.go_back()
        self.root.update()

        self.assertEqual(self.viewer.entity_browser.entity_tree.selection(), ("0",))
        self.assertIs(self.viewer.entity_browser.get_entity("0"), first_citation)

    # Vérifie navigate to shows error when entity not found.
    def test_navigate_to_shows_error_when_entity_not_found(self):
        self.viewer.controller.is_loaded.return_value = True
        self.viewer.controller.resolve_pointer.return_value = None

        with patch("ui.main_window.messagebox.showerror") as showerror:
            self.viewer.navigate_to("@X1@")
            showerror.assert_called_once_with(
                self.viewer.translator.get("ui.error"),
                self.viewer.translator.get("ui.entity_not_found", pointer="@X1@"),
            )

    # Vérifie navigation history can go back and forward.
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
        content = self.viewer.detail_panel.text_area.get("1.0", tk.END).strip()
        self.assertEqual(content, "0 @I1@ INDI")

        self.viewer.go_forward()
        content = self.viewer.detail_panel.text_area.get("1.0", tk.END).strip()
        self.assertEqual(content, "0 @I2@ FAM")

    # Vérifie navigation bar updates history state.
    def test_navigation_bar_updates_history_state(self):
        self.viewer.nav_toolbar.update_state(True, False, 2, 3)

        self.assertEqual(
            self.viewer.nav_toolbar.back_button.instate(("disabled",)), False
        )
        self.assertEqual(
            self.viewer.nav_toolbar.forward_button.instate(("disabled",)), True
        )
        self.assertIn("2", self.viewer.nav_toolbar.history_status.cget("text"))
        self.assertIn("3", self.viewer.nav_toolbar.history_status.cget("text"))

    # Vérifie display entity context records navigation history.
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

        self.assertEqual(len(self.viewer.entity_navigator.history.entries), 1)
        self.assertEqual(self.viewer.entity_navigator.history.index, 0)
