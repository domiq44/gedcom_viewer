"""Helpers partagés pour les tests du parseur GEDCOM."""

import unittest

MALFORMED_HEAD_TRLR_GEDCOM = """0 @I10@ INDI
1 NAME Ivan /Silver/
0 HEAD
1 SOUR GEDCOM
0 @I11@ INDI
1 NAME John /Gold/
0 TRLR
"""

MISSING_TRLR_GEDCOM = """0 @I10@ INDI
1 NAME Ivan /Silver/
0 HEAD
1 SOUR GEDCOM
0 @I11@ INDI
1 NAME John /Gold/
"""

SAMPLE_GEDCOM = """0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 BIRT
2 DATE 1 JAN 1900
2 PLAC Paris
1 FAMS @F1@
0 @I2@ INDI
1 NAME Jane /Smith/
1 SEX F
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 MARR
2 DATE 12 JUN 1920
1 NOTE Example note
0 HEAD
1 SOUR GEDCOM
"""

if __name__ == "__main__":
    unittest.main()
