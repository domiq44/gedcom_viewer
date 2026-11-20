"""Tests des exceptions partagées du domaine GEDCOM."""

import unittest

from gedcom.errors import GedcomLoadCancelled


class TestGedcomLoadCancelled(unittest.TestCase):
    """Vérifie le contrat de l'exception d'annulation de chargement."""

    # Vérifie the exception preserves its message.
    def test_gedcom_load_cancelled_preserves_message(self):
        # Given (Arrange) une exception d'annulation
        error = GedcomLoadCancelled("annulation")
        # When (Act) on la lève puis on la capture
        with self.assertRaises(GedcomLoadCancelled) as context:
            raise error
        # Then (Assert) le message est conservé
        self.assertIs(context.exception, error)
        self.assertEqual(str(error), "annulation")

    # Vérifie the exception derives from Exception.
    def test_gedcom_load_cancelled_derives_from_exception(self):
        # Given (Arrange) l'exception d'annulation
        # When (Act) on vérifie son ancêtre
        # Then (Assert) elle est rattrapable comme une exception standard
        self.assertTrue(issubclass(GedcomLoadCancelled, Exception))


if __name__ == "__main__":
    unittest.main()
