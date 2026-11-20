"""Tests de l'historique de navigation : enregistrement, parcours et réinitialisation."""

import unittest

from controllers.navigation_history import NavigationHistory


class Entity:
    """Doublure d'entité pour les tests de l'historique de navigation."""

    def __init__(self, pointer):
        self.pointer = pointer


def context(pointer):
    entity = Entity(pointer)
    return {"entity": entity, "type": "individual"}


class TestNavigationHistory(unittest.TestCase):
    """Vérifie l'enregistrement, le parcours et la réinitialisation de l'historique."""

    # Vérifie record ignores invalid contexts.
    def test_record_ignores_invalid_contexts(self):
        history = NavigationHistory()

        history.record(None)
        history.record({"entity": None})
        history.record({"entity": Entity(None)})

        self.assertEqual(history.entries, [])
        self.assertEqual(history.index, -1)

    # Vérifie record avoids duplicate current entry.
    def test_record_avoids_duplicate_current_entry(self):
        history = NavigationHistory()
        first = context("@I1@")

        history.record(first)
        history.record(first)

        self.assertEqual(history.entries, [first])
        self.assertFalse(history.can_go_back)
        self.assertFalse(history.can_go_forward)

    # Vérifie record keeps distinct citations with the same source pointer.
    def test_record_keeps_distinct_citations_with_the_same_source_pointer(self):
        history = NavigationHistory()
        first_citation = {
            "type": "citation",
            "entity": Entity("@S1@"),
        }
        second_citation = {
            "type": "citation",
            "entity": Entity("@S1@"),
        }

        history.record(first_citation)
        history.record(second_citation)

        self.assertEqual(history.entries, [first_citation, second_citation])

    # Vérifie back and forward move through entries.
    def test_back_and_forward_move_through_entries(self):
        history = NavigationHistory()
        first = context("@I1@")
        second = context("@I2@")
        history.record(first)
        history.record(second)

        self.assertTrue(history.can_go_back)
        self.assertIs(history.back(), first)
        self.assertFalse(history.can_go_back)
        self.assertTrue(history.can_go_forward)
        self.assertIs(history.forward(), second)

    # Vérifie record after back discards forward entries.
    def test_record_after_back_discards_forward_entries(self):
        history = NavigationHistory()
        first = context("@I1@")
        second = context("@I2@")
        replacement = context("@I3@")
        history.record(first)
        history.record(second)
        history.back()

        history.record(replacement)

        self.assertEqual(history.entries, [first, replacement])
        self.assertFalse(history.can_go_forward)

    # Vérifie record keeps only the most recent entries.
    def test_record_keeps_only_the_most_recent_entries(self):
        history = NavigationHistory()

        for index in range(history.MAX_ENTRIES + 5):
            history.record(context(f"@I{index}@"))

        self.assertEqual(len(history.entries), history.MAX_ENTRIES)
        self.assertEqual(history.entries[0]["entity"].pointer, "@I5@")
        self.assertEqual(history.entries[-1]["entity"].pointer, "@I104@")
        self.assertEqual(history.index, history.MAX_ENTRIES - 1)
        self.assertEqual(history.back()["entity"].pointer, "@I103@")
        self.assertEqual(history.forward()["entity"].pointer, "@I104@")

    # Vérifie reset clears entries and position.
    def test_reset_clears_entries_and_position(self):
        history = NavigationHistory()
        history.record(context("@I1@"))

        history.reset()

        self.assertEqual(history.entries, [])
        self.assertEqual(history.index, -1)


if __name__ == "__main__":
    unittest.main()
