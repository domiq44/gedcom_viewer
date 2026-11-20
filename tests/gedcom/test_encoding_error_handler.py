"""Tests du parseur GEDCOM : test encoding error handler."""

import unittest

from gedcom.parser import (
    _replace_invalid_utf8,
)


class TestEncodingErrorHandler(unittest.TestCase):
    """Vérifie le remplacement des erreurs de décodage UTF-8."""

    # Vérifie reraises non decode error.
    def test_reraises_non_decode_error(self):
        with self.assertRaises(ValueError):
            _replace_invalid_utf8(ValueError("boom"))


if __name__ == "__main__":
    unittest.main()
