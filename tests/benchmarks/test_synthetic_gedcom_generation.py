"""Tests de génération du fichier GEDCOM synthétique du benchmark."""

import io
import unittest

from tests.benchmarks.test_benchmark_common import benchmark_search


class TestSyntheticGedcomGeneration(unittest.TestCase):
    """Vérifie (boîte blanche) la génération du fichier GEDCOM synthétique."""

    def _scenario(self, **overrides):
        """Construit un scénario de génération minimal."""
        defaults = dict(
            individual_count=2,
            texts_per_individual=1,
            notes_per_individual=1,
            occupations_per_individual=1,
            properties_per_individual=1,
            fams_per_individual=1,
            obje_per_individual=1,
            family_count=1,
            other_entity_count=1,
            events_per_family=1,
            events_per_source=1,
            metadata_per_source=1,
        )
        defaults.update(overrides)
        return benchmark_search.SyntheticGedcom(**defaults)

    # Vérifie synthetic gedcom wraps records between HEAD and TRLR.
    def test_synthetic_gedcom_wraps_records_between_head_and_trailer(self):
        # Given un scénario de génération minimal
        scenario = self._scenario()
        # When on génère le fichier complet
        handle = io.StringIO()
        benchmark_search._write_synthetic_gedcom(handle, scenario)
        # Then les enregistrements sont encadrés par HEAD et TRLR
        output = handle.getvalue()
        self.assertTrue(output.startswith("0 HEAD\n1 SOUR BENCHMARK\n"))
        self.assertTrue(output.endswith("0 TRLR\n"))

    # Vérifie synthetic gedcom writes individual records with their optional lines.
    def test_synthetic_gedcom_writes_individual_records_with_extras(self):
        # Given un scénario d'un individu et de ses lignes optionnelles
        scenario = self._scenario(individual_count=1)
        # When on génère les individus
        handle = io.StringIO()
        benchmark_search._write_individual_records(handle, scenario)
        # Then l'individu et chaque ligne optionnelle sont présents
        output = handle.getvalue()
        self.assertIn("0 @I0@ INDI", output)
        self.assertIn("1 TEXT Synthetic text 0", output)
        self.assertIn("1 NOTE Synthetic note 0", output)
        self.assertIn("1 OCCU Synthetic occupation 0", output)
        self.assertIn("1 PROP Synthetic property 0", output)
        self.assertIn("1 FAMS @F0@", output)
        self.assertIn("1 OBJE @O0@", output)

    # Vérifie synthetic gedcom writes family records with marriages.
    def test_synthetic_gedcom_writes_family_records_with_marriages(self):
        # Given un scénario de deux familles avec deux mariages chacune
        scenario = self._scenario(family_count=2, events_per_family=2)
        # When on génère les familles
        handle = io.StringIO()
        benchmark_search._write_family_records(handle, scenario)
        # Then chaque famille référence ses époux et répète le mariage
        output = handle.getvalue()
        self.assertEqual(output.count("0 @F"), 2)
        self.assertEqual(output.count("1 MARR"), 4)
        self.assertIn("1 HUSB @I0@", output)
        self.assertIn("1 WIFE @I1@", output)

    # Vérifie synthetic gedcom writes source metadata and repository records.
    def test_synthetic_gedcom_writes_source_metadata_and_other_records(self):
        # Given un scénario d'une source avec deux métadonnées
        scenario = self._scenario(metadata_per_source=2)
        # When on génère les autres enregistrements
        handle = io.StringIO()
        benchmark_search._write_other_records(handle, scenario)
        # Then la source porte ses événements et références, les autres types suivent
        output = handle.getvalue()
        self.assertEqual(output.count("1 DATA"), 1)
        self.assertEqual(output.count("1 REFN"), 2)
        self.assertIn("0 @S0@ SOUR", output)
        self.assertIn("0 @R0@ REPO", output)
        self.assertIn("0 @U0@ SUBM", output)
        self.assertIn("0 @O0@ OBJE", output)


if __name__ == "__main__":
    unittest.main()
