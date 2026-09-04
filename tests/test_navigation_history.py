import unittest

from controllers.navigation_history import NavigationHistory


class Entity:
    def __init__(self, pointer):
        self.pointer = pointer


def context(pointer):
    entity = Entity(pointer)
    return {"entity": entity, "type": "individual"}


class TestNavigationHistory(unittest.TestCase):
    def test_record_ignores_invalid_contexts(self):
        history = NavigationHistory()

        history.record(None)
        history.record({"entity": None})
        history.record({"entity": Entity(None)})

        self.assertEqual(history.entries, [])
        self.assertEqual(history.index, -1)

    def test_record_avoids_duplicate_current_entry(self):
        history = NavigationHistory()
        first = context("@I1@")

        history.record(first)
        history.record(first)

        self.assertEqual(history.entries, [first])
        self.assertFalse(history.can_go_back)
        self.assertFalse(history.can_go_forward)

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

    def test_reset_clears_entries_and_position(self):
        history = NavigationHistory()
        history.record(context("@I1@"))

        history.reset()

        self.assertEqual(history.entries, [])
        self.assertEqual(history.index, -1)


if __name__ == "__main__":
    unittest.main()
