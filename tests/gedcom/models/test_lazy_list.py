"""Tests du descripteur de liste paresseuse."""

import unittest

from gedcom.models.lazy_list import _LazyList


class _Host:
    """Hôte de test exposant une liste paresseuse."""

    items = _LazyList()

    __slots__ = ("_items",)

    def __init__(self):
        """Initialise le stockage paresseux à None."""
        self._items = None


class TestLazyList(unittest.TestCase):
    """Vérifie la création paresseuse et la réinitialisation."""

    # Vérifie get creates the list on first access.
    def test_get_creates_the_list_on_first_access(self):
        # Given un hôte dont la liste n'est pas initialisée
        host = _Host()

        # When on accède à la liste
        values = host.items

        # Then une liste vide est créée et mémorisée
        self.assertEqual(values, [])
        self.assertIs(host.items, values)

    # Vérifie set none resets the lazy list.
    def test_set_none_resets_the_lazy_list(self):
        # Given un hôte avec une liste existante
        host = _Host()
        host.items.append("a")

        # When on affecte None
        host.items = None

        # Then une nouvelle liste vide est créée au prochain accès
        self.assertEqual(host.items, [])

    # Vérifie class access returns the descriptor.
    def test_class_access_returns_the_descriptor(self):
        # Given la classe hôte
        # When on accède à l'attribut sur la classe
        descriptor = _Host.items

        # Then le descripteur lui-même est renvoyé
        self.assertIsInstance(descriptor, _LazyList)


if __name__ == "__main__":
    unittest.main()
