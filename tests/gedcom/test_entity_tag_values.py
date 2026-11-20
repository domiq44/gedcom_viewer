"""Tests des valeurs de tags exposées par GedcomEntity."""

import unittest

from gedcom.parser import GedcomParser

MULTILINE_ADDR_PHONE_GEDCOM = """0 @I8@ INDI
1 NAME Emma /Black/
1 ADDR 123 Main Street
2 CONT Apt 4B
2 CONC , New York
1 PHON +1 555 1234
2 CONT ext 567
2 CONC , mobile
1 SEX F
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_BIRT_DATE_BEFORE_PLAC_GEDCOM = """0 @I12@ INDI
1 NAME Eleanor /Frost/
1 BIRT
2 DATE 15 APR 1950
2 PLAC New York
3 CONT NY
3 CONC , USA
1 SEX F
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_BIRT_PLAC_SUBTAG_GEDCOM = """0 @I7@ INDI
1 NAME David /Gray/
1 BIRT
2 DATE 15 APR 1950
2 PLAC New York
3 CONT NY
3 CONC , USA
1 SEX M
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_DEEPER_SUBTAG_LEVEL_GEDCOM = """0 @I13@ INDI
1 NAME Greta /Winter/
1 BIRT
2 DATE 15 APR 1950
3 PLAC New York
4 CONT NY
4 CONC , USA
1 SEX F
0 HEAD
1 SOUR GEDCOM
"""

MULTILINE_MULTIPLE_BIRT_PLAC_GEDCOM = """0 @I7@ INDI
1 NAME David /Gray/
1 BIRT
2 PLAC New York
3 CONT NY
3 CONC , USA
2 DATE 15 APR 1950
1 MARR
2 DATE 1 JAN 1970
1 BIRT
2 PLAC Boston
1 SEX M
0 HEAD
1 SOUR GEDCOM
"""

MULTIPLE_PHON_EMAIL_GEDCOM = """0 @I9@ INDI
1 NAME Fiona /Green/
1 PHON +1 555 0001
2 CONT ext 101
1 PHON +1 555 0002
2 CONC , work
1 EMAIL fiona@example.com
2 CONT secondary@example.com
1 SEX F
0 HEAD
1 SOUR GEDCOM
"""

"""Tests des valeurs de tags exposées par GedcomEntity."""


class TestEntityTagValues(unittest.TestCase):
    """Tests des valeurs de tags exposées par GedcomEntity."""

    # Vérifie birt subtag values for birth place.
    def test_birt_subtag_values_for_birth_place(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_BIRT_PLAC_SUBTAG_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I7@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_subtag_values("BIRT", "PLAC"), ["New York\nNY, USA"]
        )

    # Vérifie multiple birt subtag values continue scanning.
    def test_multiple_birt_subtag_values_continue_scanning(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_MULTIPLE_BIRT_PLAC_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I7@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_subtag_values("BIRT", "PLAC"), ["New York\nNY, USA", "Boston"]
        )

    # Vérifie birt subtag values with date before plac.
    def test_birt_subtag_values_with_date_before_plac(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_BIRT_DATE_BEFORE_PLAC_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I12@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_subtag_values("BIRT", "PLAC"), ["New York\nNY, USA"]
        )

    # Vérifie subtag values ignore grandchild tag.
    def test_subtag_values_ignore_grandchild_tag(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_DEEPER_SUBTAG_LEVEL_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I13@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(entity.get_subtag_values("BIRT", "PLAC"), [])

    # Vérifie address and phone continuation.
    def test_address_and_phone_continuation(self):
        parser = GedcomParser()
        parser.lines = MULTILINE_ADDR_PHONE_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I8@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_tag_values("ADDR"), ["123 Main Street\nApt 4B, New York"]
        )
        self.assertEqual(
            entity.get_tag_values("PHON"), ["+1 555 1234\next 567, mobile"]
        )

    # Vérifie multiple phone and email continuation.
    def test_multiple_phone_and_email_continuation(self):
        parser = GedcomParser()
        parser.lines = MULTIPLE_PHON_EMAIL_GEDCOM.splitlines()
        parser._parse_entities()

        entity = parser.get_entity("@I9@")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.tag, "INDI")
        self.assertEqual(
            entity.get_tag_values("PHON"), ["+1 555 0001\next 101", "+1 555 0002, work"]
        )
        self.assertEqual(
            entity.get_tag_values("EMAIL"), ["fiona@example.com\nsecondary@example.com"]
        )


if __name__ == "__main__":
    unittest.main()
