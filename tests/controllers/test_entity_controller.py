"""Tests du contrôleur d'entités : accès aux individus, familles et sources par pointeur."""

import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from controllers.entity_controller import EntityController
from controllers.gedcom_service import GedcomService
from gedcom.models.entity import GedcomEntity

GEDCOM = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
1 SUBM @U1@
0 @U1@ SUBM
1 NAME John /Doe/
0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 FAMS @F1@
0 @I2@ INDI
1 NAME Jane /Smith/
1 SEX F
1 FAMS @F1@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
0 @S1@ SOUR
1 TITL Birth Register
0 @R1@ REPO
1 NAME City Archives
0 @N1@ NOTE
1 CONT This is a note
0 @O1@ OBJE
1 FILE photo.jpg
0 TRLR
"""


class TestEntityController(unittest.TestCase):
    """Vérifie l'accès aux entités par pointeur et la conservation de la première occurrence."""

    def setUp(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".ged", delete=False
        ) as handle:
            handle.write(GEDCOM)
            self.path = handle.name
        self.service = GedcomService()
        self.service.load_file(self.path)
        self.controller = EntityController(self.service.parser)

    def tearDown(self):
        os.unlink(self.path)

    # Vérifie list individuals returns all individuals.
    def test_list_individuals_returns_all_individuals(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on liste les individus
        individuals = self.controller.list_individuals()
        # Then (Assert) deux individus sont retournés
        self.assertEqual(len(individuals), 2)

    # Vérifie get individual returns entity by pointer.
    def test_get_individual_returns_entity_by_pointer(self):
        # Given (Arrange) un pointeur existant
        pointer = "@I1@"
        # When (Act) on récupère l'individu
        individual = self.controller.get_individual(pointer)
        # Then (Assert) l'individu est trouvé
        self.assertIsNotNone(individual)
        self.assertEqual(individual.pointer, pointer)

    # Vérifie get individual returns none for unknown pointer.
    def test_get_individual_returns_none_for_unknown_pointer(self):
        # Given (Arrange) un pointeur inconnu
        pointer = "@I999@"
        # When (Act) on récupère l'individu
        individual = self.controller.get_individual(pointer)
        # Then (Assert) aucune entité n'est retournée
        self.assertIsNone(individual)

    # Vérifie get family returns family by pointer.
    def test_get_family_returns_family_by_pointer(self):
        # Given (Arrange) un pointeur de famille existant
        pointer = "@F1@"
        # When (Act) on récupère la famille
        family = self.controller.get_family(pointer)
        # Then (Assert) la famille est trouvée
        self.assertIsNotNone(family)
        self.assertEqual(family.pointer, pointer)

    # Vérifie get source returns source by pointer.
    def test_get_source_returns_source_by_pointer(self):
        # Given (Arrange) un pointeur de source existant
        pointer = "@S1@"
        # When (Act) on récupère la source
        source = self.controller.get_source(pointer)
        # Then (Assert) la source est trouvée
        self.assertIsNotNone(source)
        self.assertEqual(source.pointer, pointer)

    # Vérifie duplicate pointer keeps first occurrence.
    def test_duplicate_pointer_keeps_first_occurrence(self):
        # Given (Arrange) un GEDCOM avec deux enregistrements de même pointeur
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".ged", delete=False
        ) as handle:
            handle.write(
                "0 HEAD\n1 SOUR X\n0 @I1@ INDI\n1 NAME First /One/\n"
                "0 @I1@ INDI\n1 NAME Second /Two/\n0 TRLR\n"
            )
            path = handle.name
        try:
            service = GedcomService()
            service.load_file(path)
            controller = EntityController(service.parser)
            # When (Act) on récupère l'individu dupliqué
            individual = controller.get_individual("@I1@")
            # Then (Assert) la première occurrence est conservée
            self.assertIn("First", individual.name)
        finally:
            os.unlink(path)

    # Vérifie index is built on first access.
    def test_index_is_built_on_first_access(self):
        # Given un contrôleur dont aucun index n'est encore construit
        entity = GedcomEntity(
            "@I9@", "INDI", 0, ["0 @I9@ INDI\n", "1 NAME New /Person/\n"]
        )
        self.service.parser.entities.setdefault("INDI", []).append(entity)
        # When on accède à un individu
        individual = self.controller.get_individual("@I9@")
        # Then l'index construit après l'ajout contient la nouvelle entité
        self.assertIsNotNone(individual)

    # Vérifie white box index is built only once.
    def test_white_box_index_is_built_only_once(self):
        # Given un contrôleur chargé
        # When on accède plusieurs fois au même index
        with patch.object(
            self.controller, "_build_index", wraps=self.controller._build_index
        ) as build:
            self.controller.get_individual("@I1@")
            self.controller.get_individual("@I2@")
        # Then l'index n'est construit qu'une seule fois
        self.assertEqual(build.call_count, 1)

    # Vérifie white box index retry after build failure.
    def test_white_box_index_retry_after_build_failure(self):
        # Given un contrôleur dont la construction d'index échoue
        with patch.object(
            self.controller, "_build_index", side_effect=RuntimeError("boom")
        ):
            # When on accède à un individu
            with self.assertRaises(RuntimeError):
                self.controller.get_individual("@I1@")

        # Then l'index n'est pas marqué comme construit
        self.assertNotIn("individuals", self.controller._built_indexes)

        # And un nouvel accès relance la construction
        self.assertIsNotNone(self.controller.get_individual("@I1@"))

    # Vérifie white box qu'une entité dont le modèle échoue est ignorée.
    def test_white_box_skips_entity_whose_model_raises(self):
        # Given un contrôleur dont le modèle des individus échoue
        entity = GedcomEntity("@I9@", "INDI", 0, ["0 @I9@ INDI\n"])
        self.service.parser.entities.setdefault("INDI", []).append(entity)

        class RaisingModel:
            def __init__(self, entity):
                raise ValueError("boom")

        original_specs = EntityController.INDEX_SPECS
        EntityController.INDEX_SPECS = {
            **original_specs,
            "individuals": ("INDI", RaisingModel),
        }
        try:
            # When on construit l'index des individus
            with self.assertLogs("controllers.entity_controller", level="ERROR"):
                self.controller._build_index("individuals")
        finally:
            EntityController.INDEX_SPECS = original_specs

        # Then l'entité défaillante est ignorée
        self.assertEqual(self.controller.individuals, {})

    # Vérifie white box ensure index is thread safe.
    def test_white_box_ensure_index_is_thread_safe(self):
        # Given un contrôleur dont la construction d'index est ralentie
        original_build = self.controller._build_index
        build_calls = []
        first_started = threading.Event()
        release = threading.Event()

        def build(name):
            build_calls.append(name)
            first_started.set()
            release.wait()
            original_build(name)

        self.controller._build_index = build
        first = threading.Thread(
            target=lambda: self.controller._ensure_index("individuals")
        )
        first.start()
        self.assertTrue(first_started.wait(timeout=1))
        second = threading.Thread(
            target=lambda: self.controller._ensure_index("individuals")
        )
        second.start()

        try:
            # When un second thread tente le même accès
            time.sleep(0.05)

            # Then il attend le verrou et ne reconstruit pas l'index
            self.assertEqual(build_calls, ["individuals"])
        finally:
            release.set()
            first.join(timeout=1)
            second.join(timeout=1)

        # Then un seul appel de construction a eu lieu
        self.assertEqual(build_calls, ["individuals"])


if __name__ == "__main__":
    unittest.main()
