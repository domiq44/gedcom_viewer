"""Tests des correspondances entre types et contextes d'affichage."""

import unittest

from controllers.entity_types import ENTITY_CONTEXT_BY_TYPE, ENTITY_TYPE_BY_CONTEXT


class TestEntityTypes(unittest.TestCase):
    """Vérifie la bijection entre tags GEDCOM et contextes d'affichage."""

    # Vérifie context by type maps known tags.
    def test_context_by_type_maps_known_tags(self):
        # Given un tag GEDCOM connu
        # When on résout son contexte
        context = ENTITY_CONTEXT_BY_TYPE.get("INDI")

        # Then le contexte correspondant est renvoyé
        self.assertEqual(context, "individual")

    # Vérifie type by context is the inverse mapping.
    def test_type_by_context_is_the_inverse_mapping(self):
        # Given la table de correspondance
        # When on parcourt chaque type
        for entity_type, context in ENTITY_CONTEXT_BY_TYPE.items():
            # Then la table inverse redonne le type
            self.assertEqual(ENTITY_TYPE_BY_CONTEXT[context], entity_type)


if __name__ == "__main__":
    unittest.main()
