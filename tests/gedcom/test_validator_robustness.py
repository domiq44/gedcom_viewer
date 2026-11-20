"""Tests de robustesse du validateur (entrées arbitraires, bornes)."""

import random
import string
import unittest
from unittest.mock import patch

from gedcom.line_parser import parse_line
from gedcom.validator import GedcomValidator, _ValidationState


class TestValidatorRobustness(unittest.TestCase):
    """Vérifie la robustesse du validateur sur des entrées arbitraires."""

    @staticmethod
    def _random_lines(count, seed=20261116):
        """Génère des lignes pseudo-aléatoires déterministes."""
        generator = random.Random(seed)
        return [
            "".join(
                generator.choice(string.printable)
                for _ in range(generator.randint(0, 40))
            )
            for _ in range(count)
        ]

    # Vérifie validate returns error strings for arbitrary lines.
    def test_validate_returns_error_strings_for_arbitrary_lines(self):
        # Given (Arrange) des lignes arbitraires
        validator = GedcomValidator(parse_line)
        lines = self._random_lines(300)
        # When (Act) on valide les lignes
        errors = validator.validate(lines, {})
        # Then (Assert) la liste ne contient que des chaînes
        self.assertIsInstance(errors, list)
        self.assertTrue(all(isinstance(error, str) for error in errors))

    # Vérifie validate reports malformed non numeric lines.
    def test_validate_reports_malformed_non_numeric_lines(self):
        # Given (Arrange) des lignes sans niveau entier
        lines = ["not-a-level", "x y", "@I1@ INDI"]
        # When (Act) on valide les lignes
        errors = GedcomValidator(parse_line).validate(lines, {})
        # Then (Assert) chaque ligne est signalée comme malformée
        for line_number in (1, 2, 3):
            self.assertIn(f"ligne {line_number} malformée", errors)

    # Vérifie validate does not mutate input lines.
    def test_validate_does_not_mutate_input_lines(self):
        # Given (Arrange) des lignes arbitraires
        lines = self._random_lines(100)
        snapshot = list(lines)
        # When (Act) on valide les lignes
        GedcomValidator(parse_line).validate(lines, {})
        # Then (Assert) la liste d'entrée est inchangée
        self.assertEqual(lines, snapshot)

    # Vérifie validation errors are bounded.
    def test_validation_errors_are_bounded(self):
        # Given (Arrange) un validateur avec une limite d'erreurs très basse
        with patch.object(_ValidationState, "MAX_ERRORS", 3):
            lines = ["not-a-level"] * 10

            # When (Act) on valide les lignes
            errors = GedcomValidator(parse_line).validate(lines, {})

        # Then (Assert) le rapport est tronqué avec un message explicite
        self.assertEqual(len(errors), 4)
        self.assertIn("erreurs supplémentaires ignorées", errors[-1])


if __name__ == "__main__":
    unittest.main()
