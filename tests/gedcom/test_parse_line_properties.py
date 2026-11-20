"""Tests des propriétés de `parse_line` sur des entrées arbitraires."""

import random
import string
import unittest

from gedcom.line_parser import parse_line


class TestParseLineProperties(unittest.TestCase):
    """Vérifie les propriétés de `parse_line` sur des entrées arbitraires."""

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

    # Vérifie parse line returns four fields for arbitrary text.
    def test_parse_line_returns_four_fields_for_arbitrary_text(self):
        # Given (Arrange) des lignes arbitraires
        lines = self._random_lines(500)
        # When (Act) on analyse chaque ligne
        results = [parse_line(line) for line in lines]
        # Then (Assert) chaque résultat est un quadruplet typé
        for level, pointer, tag, value in results:
            self.assertTrue(level is None or isinstance(level, int))
            self.assertTrue(pointer is None or isinstance(pointer, str))
            self.assertTrue(tag is None or isinstance(tag, str))
            self.assertTrue(value is None or isinstance(value, str))

    # Vérifie parse line is deterministic for arbitrary text.
    def test_parse_line_is_deterministic_for_arbitrary_text(self):
        # Given (Arrange) des lignes arbitraires
        lines = self._random_lines(200)
        # When (Act) on analyse deux fois chaque ligne
        first = [parse_line(line) for line in lines]
        second = [parse_line(line) for line in lines]
        # Then (Assert) les résultats sont identiques
        self.assertEqual(first, second)

    # Vérifie parse line preserves conc leading space.
    def test_parse_line_preserves_conc_leading_space(self):
        # Given (Arrange) une continuation CONC avec un espace significatif
        line = "2 CONC  continuation"
        # When (Act) on analyse la ligne
        parsed = parse_line(line)
        # Then (Assert) l'espace de tête est conservé
        self.assertEqual(parsed, (2, None, "CONC", " continuation"))

    # Vérifie parse line reads generated valid lines.
    def test_parse_line_reads_generated_valid_lines(self):
        # Given (Arrange) des lignes valides générées
        cases = [
            ("0 HEAD", (0, None, "HEAD", "")),
            ("1 NAME John /Doe/", (1, None, "NAME", "John /Doe/")),
            ("0 @I1@ INDI", (0, "@I1@", "INDI", "")),
            ("2 NOTE", (2, None, "NOTE", "")),
        ]
        # When (Act) on analyse les lignes
        results = [parse_line(line) for line, _expected in cases]
        # Then (Assert) les champs correspondent aux attentes
        self.assertEqual(results, [expected for _line, expected in cases])


if __name__ == "__main__":
    unittest.main()
