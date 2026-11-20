"""Tests du générateur GEDCOM de benchmark."""

import unittest

from benchmarks.generate_gedcom import build_gedcom


class TestGenerateGedcom(unittest.TestCase):
    """Vérifie la structure du GEDCOM synthétique généré."""

    # Vérifie build gedcom contains requested individuals.
    def test_build_gedcom_contains_requested_individuals(self):
        # Given (Arrange) un nombre d'individus demandé
        count = 12

        # When (Act) on génère le GEDCOM
        content = build_gedcom(count)

        # Then (Assert) le fichier contient les en-têtes et les individus
        self.assertTrue(content.startswith("0 HEAD\n"))
        self.assertTrue(content.endswith("0 TRLR\n"))
        self.assertEqual(content.count("0 @I"), count)
        self.assertIn("1 NAME John0 /Doe0/", content)

    # Vérifie build gedcom includes families for every ten individuals.
    def test_build_gedcom_includes_families_for_every_ten_individuals(self):
        # Given (Arrange) un nombre d'individus multiple de dix
        count = 20

        # When (Act) on génère le GEDCOM
        content = build_gedcom(count)

        # Then (Assert) deux familles sont présentes
        self.assertEqual(content.count("0 @F"), 2)
        self.assertIn("1 HUSB @I1@", content)


if __name__ == "__main__":
    unittest.main()
