"""Tests du modèle d'événement GEDCOM."""

import unittest

from gedcom.models.event import Event


class TestEvent(unittest.TestCase):
    """Vérifie les détails et l'accès compatible dictionnaire."""

    # Vérifie add detail appends tag value pairs.
    def test_add_detail_appends_tag_value_pairs(self):
        # Given un événement sans détail
        event = Event("MARR", "12 JUN 1920")

        # When on ajoute un sous-tag
        event.add_detail("PLAC", "Paris")

        # Then le détail est conservé sous forme de tuple
        self.assertEqual(event.details, [("PLAC", "Paris")])

    # Vérifie get returns known fields and default.
    def test_get_returns_known_fields_and_default(self):
        # Given un événement avec un détail
        event = Event("DIV", "")
        event.add_detail("DATE", "1900")

        # When on interroge les champs connus et inconnus
        # Then les champs connus sont renvoyés et l'inconnu vaut le défaut
        self.assertEqual(event.get("tag"), "DIV")
        self.assertEqual(event.get("details"), [("DATE", "1900")])
        self.assertIsNone(event.get("unknown"))


if __name__ == "__main__":
    unittest.main()
