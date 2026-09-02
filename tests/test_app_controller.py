import os
import tempfile
import unittest
from controllers.app_controller import AppController
from controllers.entity_controller import EntityController
from controllers.search_controller import SearchController
from controllers.presentation_controller import PresentationController
from gedcom.parser import GedcomParser, GedcomEntity
from gedcom.models.individual import Individual
from gedcom.models.family import Family
from gedcom.models.source import Source
from gedcom.models.repository import Repository

MALFORMED_HEAD_TRLR_GEDCOM = """0 @I1@ INDI
1 NAME John /Doe/
0 HEAD
1 SOUR GEDCOM
0 @I2@ INDI
1 NAME Jane /Smith/
0 TRLR
"""

MISSING_TRLR_GEDCOM = """0 @I1@ INDI
1 NAME John /Doe/
0 HEAD
1 SOUR GEDCOM
0 @I2@ INDI
1 NAME Jane /Smith/
"""


class DummyEntity:
    def __init__(self, pointer, tag):
        self.pointer = pointer
        self.tag = tag
        self.lines = [f"0 {pointer} {tag}\n"]

    def raw_block(self):
        return "\n".join(self.lines)


class TestAppController(unittest.TestCase):
    def setUp(self):
        self.controller = AppController()
        parser = GedcomParser()
        parser.entities = {
            "INDI": [DummyEntity("@I1@", "INDI")],
            "FAM": [DummyEntity("@F1@", "FAM")],
            "SOUR": [
                GedcomEntity(
                    "@S1@", "SOUR", 0, ["0 @S1@ SOUR\n", "1 TITL Sample source\n"]
                )
            ],
            "REPO": [
                GedcomEntity(
                    "@R1@", "REPO", 0, ["0 @R1@ REPO\n", "1 NAME Sample repo\n"]
                )
            ],
            "NOTE": [
                GedcomEntity(
                    "@N1@", "NOTE", 0, ["0 @N1@ NOTE\n", "1 NOTE Sample note\n"]
                )
            ],
            "OBJE": [
                GedcomEntity("@O1@", "OBJE", 0, ["0 @O1@ OBJE\n", "1 FILE image.jpg\n"])
            ],
            "SUBM": [
                GedcomEntity(
                    "@M1@", "SUBM", 0, ["0 @M1@ SUBM\n", "1 NAME Submitter Name\n"]
                )
            ],
        }
        parser._by_pointer = {
            "@I1@": parser.entities["INDI"][0],
            "@F1@": parser.entities["FAM"][0],
            "@S1@": parser.entities["SOUR"][0],
            "@R1@": parser.entities["REPO"][0],
            "@N1@": parser.entities["NOTE"][0],
            "@O1@": parser.entities["OBJE"][0],
            "@M1@": parser.entities["SUBM"][0],
        }
        self.controller.gedcom_service.parser = parser
        self.controller.entity_controller = EntityController(
            self.controller.gedcom_service.parser
        )
        self.controller.search_controller = SearchController(
            self.controller.gedcom_service,
            self.controller.entity_controller,
            entity_labels=self.controller.ENTITY_LABELS,
        )
        self.controller.presentation_controller = PresentationController(
            self.controller.gedcom_service,
            self.controller.entity_controller,
        )

    def test_get_entity(self):
        entity = self.controller.get_entity("@I1@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.pointer, "@I1@")

    def test_get_raw_block_from_individual(self):
        individual = self.controller.get_individual("@I1@")
        raw = self.controller.get_raw_block(individual)
        self.assertIn("@I1@", raw)

    def test_get_raw_block_from_family(self):
        family = self.controller.get_family("@F1@")
        raw = self.controller.get_raw_block(family)
        self.assertIn("@F1@", raw)

    def test_get_entity_display_info(self):
        individual = self.controller.get_individual("@I1@")
        context = self.controller.get_entity_display_info(individual)

        self.assertEqual(context["type"], "individual")
        self.assertIs(context["entity"], individual)
        self.assertIs(context["raw_entity"], individual.entity)
        self.assertIn("@I1@", context["raw_block"])

        family = self.controller.get_family("@F1@")
        context = self.controller.get_entity_display_info(family)

        self.assertEqual(context["type"], "family")
        self.assertIs(context["entity"], family)
        self.assertIs(context["raw_entity"], family.entity)
        self.assertIn("@F1@", context["raw_block"])

        source = self.controller.get_source("@S1@")
        context = self.controller.get_entity_display_info(source)

        self.assertEqual(context["type"], "source")
        self.assertIs(context["entity"], source)
        self.assertIs(context["raw_entity"], source.entity)
        self.assertIn("@S1@", context["raw_block"])

        repository = self.controller.get_repository("@R1@")
        context = self.controller.get_entity_display_info(repository)

        self.assertEqual(context["type"], "repository")
        self.assertIs(context["entity"], repository)
        self.assertIs(context["raw_entity"], repository.entity)
        self.assertIn("@R1@", context["raw_block"])

        note = self.controller.get_note("@N1@")
        context = self.controller.get_entity_display_info(note)

        self.assertEqual(context["type"], "note")
        self.assertIs(context["entity"], note)
        self.assertIs(context["raw_entity"], note.entity)
        self.assertIn("@N1@", context["raw_block"])

        obj = self.controller.get_object("@O1@")
        context = self.controller.get_entity_display_info(obj)

        self.assertEqual(context["type"], "object")
        self.assertIs(context["entity"], obj)
        self.assertIs(context["raw_entity"], obj.entity)
        self.assertIn("@O1@", context["raw_block"])

        submitter = self.controller.get_submitter("@M1@")
        context = self.controller.get_entity_display_info(submitter)

        self.assertEqual(context["type"], "submitter")
        self.assertIs(context["entity"], submitter)
        self.assertIs(context["raw_entity"], submitter.entity)
        self.assertIn("@M1@", context["raw_block"])

    def test_get_entity_type_menu_display_items(self):
        items = self.controller.get_entity_type_menu_display_items()
        self.assertTrue(
            any(
                "INDI" in label and entity_type == "INDI"
                for label, entity_type in items
            )
        )
        self.assertTrue(
            any("FAM" in label and entity_type == "FAM" for label, entity_type in items)
        )

    def test_format_entity_label_and_context(self):
        entity = self.controller.get_entity("@I1@")
        self.assertEqual(self.controller.format_entity_label(entity), "@I1@")

        individual = self.controller.get_individual("@I1@")
        self.assertEqual(self.controller.format_entity_label(individual), "@I1@")

        context = self.controller.get_entity_view_context(individual)
        self.assertEqual(context["type"], "individual")
        self.assertIs(context["entity"], individual)
        self.assertIs(context["raw_entity"], individual.entity)

        family = self.controller.get_family("@F1@")
        context = self.controller.get_entity_view_context(family)
        self.assertEqual(context["type"], "family")
        self.assertIs(context["entity"], family)
        self.assertIs(context["raw_entity"], family.entity)

    def test_load_initializes_controllers(self):
        controller = AppController()
        parser = GedcomParser()
        parser.entities = {
            "INDI": [DummyEntity("@I2@", "INDI")],
            "FAM": [DummyEntity("@F2@", "FAM")],
        }
        parser._by_pointer = {
            "@I2@": parser.entities["INDI"][0],
            "@F2@": parser.entities["FAM"][0],
        }
        controller.gedcom_service.parser = parser
        controller.entity_controller = EntityController(
            controller.gedcom_service.parser
        )
        controller.search_controller = SearchController(
            controller.gedcom_service,
            controller.entity_controller,
            entity_labels=controller.ENTITY_LABELS,
        )
        controller.presentation_controller = PresentationController(
            controller.gedcom_service, controller.entity_controller
        )

        self.assertTrue(controller.is_loaded())

    def test_load_file_integration(self):
        sample_gedcom = """0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
0 @I2@ INDI
1 NAME Jane /Smith/
1 SEX F
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
0 @S1@ SOUR
1 TITL Sample source
1 AUTH Author Name
1 REPO @R1@
0 @R1@ REPO
1 NAME Sample repo
1 ADDR 123 Main St
1 CITY Paris
0 @N1@ NOTE
1 NOTE Sample note
0 @O1@ OBJE
1 FILE image.jpg
1 TITL Example image
0 @M1@ SUBM
1 NAME Submitter Name
1 EMAIL submitter@example.com
0 HEAD
1 SOUR GEDCOM
0 TRLR
"""
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", delete=False
            ) as temp_file:
                temp_file.write(sample_gedcom)
                temp_path = temp_file.name

            controller = AppController()
            controller.load_file(temp_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        self.assertTrue(controller.is_loaded())
        self.assertIn("INDI", controller.get_entity_types())
        self.assertIn("FAM", controller.get_entity_types())
        self.assertIn("SOUR", controller.get_entity_types())
        self.assertIn("REPO", controller.get_entity_types())
        self.assertIn("NOTE", controller.get_entity_types())
        self.assertIn("OBJE", controller.get_entity_types())
        self.assertIn("SUBM", controller.get_entity_types())

        indi_items = controller.get_entity_list_items("INDI")
        self.assertEqual(len(indi_items), 2)
        # Verify that the label now includes the individual's name
        self.assertIn("@I1@", indi_items[0][1])
        self.assertIn("John", indi_items[0][1])

        individual = controller.get_individual("@I1@")
        context = controller.get_entity_display_info(individual)
        self.assertEqual(context["type"], "individual")
        self.assertIn("@I1@", context["raw_block"])

        self.assertEqual(controller.resolve_pointer("@F1@").pointer, "@F1@")
        self.assertEqual(controller.resolve_pointer("@N1@").pointer, "@N1@")
        self.assertEqual(controller.resolve_pointer("@O1@").pointer, "@O1@")
        self.assertEqual(controller.resolve_pointer("@M1@").pointer, "@M1@")
        self.assertIn("0 HEAD", controller.extract_head())
        self.assertIn("0 TRLR", controller.extract_trailer())

    def test_extract_head_stops_at_next_record(self):
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", delete=False
            ) as temp_file:
                temp_file.write(MALFORMED_HEAD_TRLR_GEDCOM)
                temp_path = temp_file.name

            controller = AppController()
            controller.load_file(temp_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        head_block = controller.extract_head()
        self.assertIn("0 HEAD", head_block)
        self.assertIn("1 SOUR GEDCOM", head_block)
        self.assertNotIn("0 @I2@ INDI", head_block)

    def test_extract_trailer_returns_empty_when_missing(self):
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", delete=False
            ) as temp_file:
                temp_file.write(MISSING_TRLR_GEDCOM)
                temp_path = temp_file.name

            controller = AppController()
            controller.load_file(temp_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        self.assertEqual(controller.extract_trailer(), "")

    def test_resolve_pointer_preference(self):
        self.assertIs(
            self.controller.resolve_pointer("@I1@"),
            self.controller.get_individual("@I1@"),
        )
        self.assertIs(
            self.controller.resolve_pointer("@F1@"), self.controller.get_family("@F1@")
        )

    def test_get_entity_list_items(self):
        items = self.controller.get_entity_list_items("INDI")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "@I1@")

        items = self.controller.get_entity_list_items("FAM", "F1")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][1], "@F1@")

        no_items = self.controller.get_entity_list_items("FAM", "X1")
        self.assertEqual(no_items, [])

    def test_search_entities_by_query(self):
        individuals = self.controller.search_entities("INDI", "I1")
        self.assertEqual(len(individuals), 1)
        self.assertEqual(individuals[0].pointer, "@I1@")

        families = self.controller.search_entities("FAM", "F1")
        self.assertEqual(len(families), 1)
        self.assertEqual(families[0].pointer, "@F1@")

        no_match = self.controller.search_entities("FAM", "X1")
        self.assertEqual(no_match, [])

        all_families = self.controller.search_entities("FAM", "")
        self.assertEqual(len(all_families), 1)


if __name__ == "__main__":
    unittest.main()
