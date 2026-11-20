"""Tests des libellés des types d'entités."""

import unittest

from controllers.entity_labels import ENTITY_LABELS, get_default_entity_labels


class TestEntityLabels(unittest.TestCase):
    """Vérifie la table des libellés et sa copie défensive."""

    # Vérifie default labels cover every entity type.
    def test_default_labels_cover_every_entity_type(self):
        # Given les types d'entités connus
        expected = {
            "INDI",
            "FAM",
            "OBJE",
            "NOTE",
            "SOUR",
            "CITE",
            "SUBM",
            "REPO",
            "ANCESTOR_TREE",
        }

        # When on récupère les libellés par défaut
        labels = get_default_entity_labels()

        # Then chaque type possède un libellé non vide
        self.assertEqual(set(labels), expected)
        self.assertTrue(all(labels.values()))

    # Vérifie default labels return a copy.
    def test_default_labels_return_a_copy(self):
        # Given les libellés par défaut
        labels = get_default_entity_labels()

        # When on modifie la copie
        labels["INDI"] = "Modifié"

        # Then la table d'origine reste inchangée
        self.assertEqual(ENTITY_LABELS["INDI"], "Individu")


if __name__ == "__main__":
    unittest.main()
