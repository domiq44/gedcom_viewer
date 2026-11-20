"""Tests de validité du GEDCOM synthétique de référence."""

import os
import unittest

from gedcom.parser import GedcomParser

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "synthetic_5_5_1.ged"
)


class TestSyntheticFixture(unittest.TestCase):
    """Vérifie que le GEDCOM synthétique reste valide et exploitable."""

    # Vérifie que le fichier synthétique ne produit aucune erreur de validation.
    def test_synthetic_fixture_is_valid(self):
        # Given le fichier synthétique
        parser = GedcomParser()
        # When on le charge puis on le valide
        parser.load(FIXTURE_PATH)
        # Then aucune anomalie n'est remontée
        self.assertEqual(parser.validation_errors, [])

    # Vérifie que le fichier synthétique expose les enregistrements attendus.
    def test_synthetic_fixture_exposes_expected_entities(self):
        # Given le fichier synthétique chargé
        parser = GedcomParser()
        parser.load(FIXTURE_PATH)
        # When on compte les entités par type
        counts = {tag: len(entities) for tag, entities in parser.entities.items()}
        # Then les enregistrements attendus sont présents
        self.assertEqual(counts.get("INDI"), 3)
        self.assertEqual(counts.get("FAM"), 1)
        self.assertEqual(counts.get("SOUR"), 1)
        self.assertEqual(counts.get("REPO"), 1)
        self.assertEqual(counts.get("SUBM"), 1)
