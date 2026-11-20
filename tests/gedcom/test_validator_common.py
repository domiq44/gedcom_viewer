"""Helpers partagés pour les tests du validateur GEDCOM."""

import os
import tempfile
import unittest

from gedcom.line_parser import parse_line
from gedcom.parser import GedcomParser
from gedcom.validator import GedcomValidator


def load_parser(text):
    """Charge un GEDCOM (mode tolérant) et retourne le parser peuplé."""
    parser = GedcomParser()
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".ged", delete=False
    ) as handle:
        handle.write(text)
        path = handle.name
    try:
        parser.load(path)
    finally:
        os.unlink(path)
    return parser


def validate_text(text):
    """Valide directement le texte via GedcomValidator (sans strict)."""
    parser = load_parser(text)
    validator = GedcomValidator(parse_line)
    return validator.validate(parser.lines, parser._by_pointer)


VALID_GEDCOM = """0 HEAD
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
0 @I3@ INDI
1 NAME Kid /Doe/
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
0 TRLR
"""


if __name__ == "__main__":
    unittest.main()
