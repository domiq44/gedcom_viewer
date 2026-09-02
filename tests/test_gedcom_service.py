import tempfile
import unittest
from controllers.gedcom_service import GedcomService

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
    def setUp(self):
        self.service = GedcomService()

    def test_is_loaded_false_before_load(self):
        self.assertFalse(self.service.is_loaded())

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

    def test_get_entities_by_type_returns_expected_list(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(SAMPLE_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        individuals = self.service.get_entities_by_type("INDI")
        families = self.service.get_entities_by_type("FAM")

        self.assertEqual(len(individuals), 2)
        self.assertEqual(len(families), 1)
        self.assertEqual(individuals[0].tag, "INDI")
        self.assertEqual(families[0].tag, "FAM")

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

    def test_extract_trailer_returns_trailer_block(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(SAMPLE_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        trailer_block = self.service.extract_trailer()

        self.assertIn("0 TRLR", trailer_block)

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

    def test_extract_trailer_returns_empty_when_missing(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(MISSING_TRLR_GEDCOM)
            temp_path = temp_file.name

        self.service.load_file(temp_path)
        self.assertEqual(self.service.extract_trailer(), "")


if __name__ == "__main__":
    unittest.main()
