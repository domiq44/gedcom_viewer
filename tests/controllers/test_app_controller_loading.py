"""Tests du chargement et de la réinitialisation du contrôleur applicatif."""

import os
import tempfile
import threading
import unittest
from unittest.mock import patch

from controllers.app_controller import AppController
from controllers.citation_controller import CitationController
from controllers.entity_controller import EntityController
from controllers.presentation_controller import PresentationController
from controllers.search_controller import SearchController
from gedcom.errors import GedcomLoadCancelled
from gedcom.parser import GedcomParser
from tests.controllers.app_controller_test_case import (
    AppControllerTestMixin,
    DummyEntity,
)
from tests.temp_file_factory import write_temp_text

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


class TestAppControllerLoading(AppControllerTestMixin, unittest.TestCase):
    """Vérifie le chargement, l'extraction et la réinitialisation."""

    # Vérifie get entity.
    def test_get_entity(self):
        entity = self.controller.get_entity("@I1@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.pointer, "@I1@")

    # Vérifie get raw block from individual.
    def test_get_raw_block_from_individual(self):
        individual = self.controller.get_individual("@I1@")
        raw = self.controller.get_raw_block(individual)
        self.assertIn("@I1@", raw)

    # Vérifie get raw block from family.
    def test_get_raw_block_from_family(self):
        family = self.controller.get_family("@F1@")
        raw = self.controller.get_raw_block(family)
        self.assertIn("@F1@", raw)

    # Vérifie get entity display info.
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

    # Vérifie load initializes controllers.
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

    # Vérifie load file cancels before initialization.
    def test_load_file_cancels_before_initialization(self):
        # Given un contrôleur et une annulation déjà demandée
        controller = AppController()
        cancel_event = threading.Event()
        cancel_event.set()

        # When on charge un fichier avec annulation
        with patch.object(controller.gedcom_service, "load_file") as load_file:
            with self.assertRaises(GedcomLoadCancelled):
                controller.load_file("/tmp/cancel.ged", cancel_event=cancel_event)

        # Then le chargement est propagé mais les contrôleurs ne sont pas initialisés
        load_file.assert_called_once_with(
            "/tmp/cancel.ged", strict=False, cancel_event=cancel_event
        )
        self.assertIsNone(controller.entity_controller)

    # Vérifie load file rolls back when initialization fails.
    def test_load_file_rolls_back_when_initialization_fails(self):
        # Given un fichier valide et une initialisation qui échoue
        temp_path = write_temp_text(self, "0 HEAD\n1 SOUR X\n0 TRLR\n")
        controller = AppController()

        # When on charge le fichier
        with patch.object(
            controller, "_initialize_controllers", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(RuntimeError):
                controller.load_file(temp_path)

        # Then le service et les contrôleurs sont réinitialisés
        self.assertFalse(controller.gedcom_service.is_loaded())
        self.assertIsNone(controller.entity_controller)

    # Vérifie load file integration.
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

        family = controller.get_family("@F1@")
        self.assertEqual(
            controller.format_entity_display_name(family, "FAM"),
            "Doe, John & Smith, Jane",
        )
        self.assertEqual(
            controller.format_entity_label(family, "FAM"),
            "@F1@ – Doe, John & Smith, Jane",
        )

        indi_items = controller.get_entity_list_items("INDI")
        self.assertEqual(len(indi_items), 2)
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

    # Vérifie citation controller indexes linked sources and context.
    def test_citation_controller_indexes_linked_sources_and_context(self):
        content = """0 HEAD
1 SOUR TEST
0 @I1@ INDI
1 NAME Ada /Lovelace/
1 BIRT
2 SOUR @S1@
3 PAGE 17
3 QUAY 2
3 EVEN Census
4 ROLE Witness
3 DATA
4 DATE 1900
4 TEXT Long citation detail
3 NOTE Citation note
0 @I2@ INDI
1 NAME Unlinked /Source/
1 SOUR Register mentioned in text
0 @F1@ FAM
1 SOUR @S1@
0 @S1@ SOUR
1 TITL Estrées-lès-Crécy, 1848-1872, 173 medias
1 AUTH registre
1 PUBL FR AD 80, Estrées-lès-Crécy, 1848-1872
1 NOTE https://archives.somme.fr/ark:/58483/g9zb5dfv386q
1 REPO @R10@
2 CALN 5MI_D1106
3 MEDI électronique
1 CHAN
2 DATE 30 OCT 2026
3 TIME 19:45:25
0 @R10@ REPO
1 NAME Archives départementales de la Somme
0 TRLR
"""
        temp_path = write_temp_text(self, content)

        parser = GedcomParser()
        parser.load(temp_path)

        citations = CitationController(parser).list_citations()

        self.assertEqual(len(citations), 2)
        self.assertEqual(citations[0].source_pointer, "@S1@")
        self.assertEqual(citations[0].owner_pointer, "@I1@")
        self.assertEqual(citations[0].owner_type, "INDI")
        self.assertEqual(citations[0].level, 2)
        self.assertEqual(citations[0].context_tag, "BIRT")
        self.assertEqual(citations[0].page, "17")
        self.assertEqual(
            citations[0].raw_block,
            "2 SOUR @S1@\n"
            "3 PAGE 17\n"
            "3 QUAY 2\n"
            "3 EVEN Census\n"
            "4 ROLE Witness\n"
            "3 DATA\n"
            "4 DATE 1900\n"
            "4 TEXT Long citation detail\n"
            "3 NOTE Citation note\n",
        )
        self.assertEqual(
            [field["tag"] for field in citations[0].details],
            [
                "PAGE",
                "QUAY",
                "EVEN",
                "EVEN/ROLE",
                "DATA",
                "DATA/DATE",
                "DATA/TEXT",
                "NOTE",
            ],
        )
        self.assertNotIn("0 @S1@ SOUR", citations[0].raw_block)
        self.assertEqual(citations[1].owner_pointer, "@F1@")
        self.assertEqual(citations[1].context_tag, "")

    # Vérifie extract head stops at next record.
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

    # Vérifie extract trailer returns empty when missing.
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

    # Vérifie reset unloads file and controllers.
    def test_reset_unloads_file_and_controllers(self):
        # Given (Arrange) un contrôleur avec un fichier chargé
        self.assertTrue(self.controller.is_loaded())

        # When (Act) on réinitialise le contrôleur
        self.controller.reset()

        # Then (Assert) le fichier et les contrôleurs sont déchargés
        self.assertIsNone(self.controller.entity_controller)
        self.assertIsNone(self.controller.citation_controller)
        self.assertIsNone(self.controller.search_controller)
        self.assertIsNone(self.controller.presentation_controller)
        self.assertFalse(self.controller.is_loaded())


if __name__ == "__main__":
    unittest.main()
