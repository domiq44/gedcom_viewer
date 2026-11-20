"""Tests du service GEDCOM : chargement, accès aux entités et extraction HEAD/TRLER."""

import tempfile
import unittest

from controllers.gedcom_service import GedcomService
from tests.temp_file_factory import write_temp_text

SAMPLE_GEDCOM = """0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
0 @I2@ INDI
1 NAME Jane /Smith/
1 SEX F
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
0 HEAD
1 SOUR GEDCOM
0 TRLR
"""

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


class TestGedcomService(unittest.TestCase):
    """Vérifie le chargement du service, l'accès aux entités et l'extraction des blocs."""

    def setUp(self):
        self.service = GedcomService()

    # Vérifie is loaded false before load.
    def test_is_loaded_false_before_load(self):
        self.assertFalse(self.service.is_loaded())

    # Vérifie reset unloads parser.
    def test_reset_unloads_parser(self):
        # Given (Arrange) un service avec un parseur chargé
        self.service.parser = object()

        # When (Act) on réinitialise le service
        self.service.reset()

        # Then (Assert) le parseur est déchargé
        self.assertIsNone(self.service.parser)
        self.assertFalse(self.service.is_loaded())

    # Vérifie load file populates service.
    def test_load_file_populates_service(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(SAMPLE_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        self.assertTrue(self.service.is_loaded())
        self.assertIn("INDI", self.service.entities)
        self.assertIn("FAM", self.service.entities)
        self.assertIn("HEAD", self.service.entities)
        self.assertIn("TRLR", self.service.entities)

    # Vérifie strict load keeps previous parser when file is invalid.
    def test_strict_load_keeps_previous_parser_when_file_is_invalid(self):
        valid_path = write_temp_text(self, SAMPLE_GEDCOM)
        self.service.load_file(valid_path)
        previous_parser = self.service.parser

        invalid_path = write_temp_text(self, "0 HEAD\n1 SOUR TEST\n")

        with self.assertRaises(ValueError):
            self.service.load_file(invalid_path, strict=True)

        self.assertIs(self.service.parser, previous_parser)

    # Vérifie get entity returns entity by pointer.
    def test_get_entity_returns_entity_by_pointer(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(SAMPLE_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        entity = self.service.get_entity("@I1@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.pointer, "@I1@")
        self.assertEqual(entity.tag, "INDI")

    # Vérifie get entity types returns keys.
    def test_get_entity_types_returns_keys(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(SAMPLE_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        types = self.service.get_entity_types()

        self.assertIn("INDI", types)
        self.assertIn("FAM", types)
        self.assertIn("HEAD", types)

    # Vérifie extract head returns head block.
    def test_extract_head_returns_head_block(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(SAMPLE_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        head_block = self.service.extract_head()

        self.assertIn("0 HEAD", head_block)
        self.assertIn("1 SOUR GEDCOM", head_block)

    # Vérifie extract trailer returns trailer block.
    def test_extract_trailer_returns_trailer_block(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(SAMPLE_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        trailer_block = self.service.extract_trailer()

        self.assertIn("0 TRLR", trailer_block)

    # Vérifie extract head stops at next record.
    def test_extract_head_stops_at_next_record(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(MALFORMED_HEAD_TRLR_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        head_block = self.service.extract_head()

        self.assertIn("0 HEAD", head_block)
        self.assertIn("1 SOUR GEDCOM", head_block)
        self.assertNotIn("0 @I2@ INDI", head_block)

    # Vérifie extract trailer returns empty when missing.
    def test_extract_trailer_returns_empty_when_missing(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(MISSING_TRLR_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        self.assertEqual(self.service.extract_trailer(), "")

    # Vérifie create entity controller returns none when unloaded.
    def test_create_entity_controller_returns_none_when_unloaded(self):
        # Given (Arrange) un service sans fichier chargé
        # When (Act) on crée le contrôleur d'entités
        controller = self.service.create_entity_controller()
        # Then (Assert) aucun contrôleur n'est créé
        self.assertIsNone(controller)

    # Vérifie create entity controller returns controller when loaded.
    def test_create_entity_controller_returns_controller_when_loaded(self):
        # Given (Arrange) un service chargé
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(SAMPLE_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        # When (Act) on crée le contrôleur d'entités
        controller = self.service.create_entity_controller()
        # Then (Assert) un contrôleur est créé
        self.assertIsNotNone(controller)

    # Vérifie entities returns empty when unloaded.
    def test_entities_returns_empty_when_unloaded(self):
        # Given (Arrange) un service sans fichier chargé
        # When (Act) on lit l'index des entités
        entities = self.service.entities
        # Then (Assert) l'index est vide
        self.assertEqual(entities, {})

    # Vérifie get entity returns none when unloaded.
    def test_get_entity_returns_none_when_unloaded(self):
        # Given (Arrange) un service sans fichier chargé
        # When (Act) on demande une entité
        entity = self.service.get_entity("@I1@")
        # Then (Assert) aucune entité n'est retournée
        self.assertIsNone(entity)

    # Vérifie get entity returns none for empty pointer.
    def test_get_entity_returns_none_for_empty_pointer(self):
        # Given (Arrange) un service chargé
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(SAMPLE_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        # When (Act) on demande une entité sans pointeur
        entity = self.service.get_entity("")
        # Then (Assert) aucune entité n'est retournée
        self.assertIsNone(entity)

    # Vérifie get entity types returns empty when unloaded.
    def test_get_entity_types_returns_empty_when_unloaded(self):
        # Given (Arrange) un service sans fichier chargé
        # When (Act) on demande les types d'entités
        types = self.service.get_entity_types()
        # Then (Assert) la liste est vide
        self.assertEqual(types, [])

    # Vérifie extract head returns empty when unloaded.
    def test_extract_head_returns_empty_when_unloaded(self):
        # Given (Arrange) un service sans fichier chargé
        # When (Act) on extrait le bloc HEAD
        head_block = self.service.extract_head()
        # Then (Assert) le bloc est vide
        self.assertEqual(head_block, "")

    # Vérifie extract trailer returns empty when unloaded.
    def test_extract_trailer_returns_empty_when_unloaded(self):
        # Given (Arrange) un service sans fichier chargé
        # When (Act) on extrait le bloc TRLR
        trailer_block = self.service.extract_trailer()
        # Then (Assert) le bloc est vide
        self.assertEqual(trailer_block, "")


if __name__ == "__main__":
    unittest.main()
