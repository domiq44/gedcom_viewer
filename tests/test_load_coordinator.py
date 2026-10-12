import unittest
from unittest.mock import Mock, patch

from ui.load_coordinator import LoadCoordinator


class FakeRoot:
    def __init__(self):
        self.after_calls = []

    def after(self, delay, callback):
        self.after_calls.append((delay, callback))


class TestLoadCoordinator(unittest.TestCase):
    def setUp(self):
        self.root = FakeRoot()
        self.controller = Mock()
        self.controller_factory = Mock(return_value=self.controller)
        self.on_success = Mock()
        self.on_error = Mock()
        self.on_loading = Mock()
        self.coordinator = LoadCoordinator(
            self.root,
            self.controller_factory,
            self.on_success,
            self.on_error,
            self.on_loading,
        )

    def test_start_loads_in_worker_and_publishes_success(self):
        with patch("ui.load_coordinator.threading.Thread") as thread_class:
            self.coordinator.start("/tmp/test.ged", strict=True)
            worker_target = thread_class.call_args.kwargs["target"]
            worker_target()

        self.on_loading.assert_called_once_with()
        self.controller.load_file.assert_called_once_with("/tmp/test.ged", strict=True)
        self.assertTrue(self.coordinator.is_loading)

        self.coordinator._poll_result()

        self.assertFalse(self.coordinator.is_loading)
        self.on_error.assert_not_called()
        self.on_success.assert_called_once()
        self.assertEqual(self.on_success.call_args.args[0], "/tmp/test.ged")
        self.assertIs(self.on_success.call_args.args[2], self.controller)

    def test_start_propagates_worker_error(self):
        error = ValueError("invalid GEDCOM")
        self.controller.load_file.side_effect = error

        with patch("ui.load_coordinator.threading.Thread") as thread_class:
            self.coordinator.start("/tmp/test.ged")
            thread_class.call_args.kwargs["target"]()

        self.coordinator._poll_result()

        self.assertFalse(self.coordinator.is_loading)
        self.on_success.assert_not_called()
        self.on_error.assert_called_once_with("/tmp/test.ged", error)

    def test_start_ignores_second_load_while_loading(self):
        with patch("ui.load_coordinator.threading.Thread") as thread_class:
            self.coordinator.start("/tmp/first.ged")
            self.coordinator.start("/tmp/second.ged")

        self.assertEqual(thread_class.call_count, 1)
        self.on_loading.assert_called_once_with()

    def test_poll_reschedules_when_result_is_not_ready(self):
        self.coordinator.start = Mock()
        self.coordinator._is_loading = True
        self.coordinator._poll_result()

        self.assertEqual(len(self.root.after_calls), 1)
        self.assertEqual(self.root.after_calls[0][0], LoadCoordinator.POLL_INTERVAL_MS)

    def test_close_ignores_pending_result(self):
        self.coordinator.close()
        self.coordinator._results.put(("/tmp/test.ged", 1.0, None, self.controller))

        self.coordinator._poll_result()

        self.assertTrue(self.coordinator.is_closing)
        self.assertFalse(self.coordinator.is_loading)
        self.on_success.assert_not_called()
        self.on_error.assert_not_called()
        self.assertEqual(self.root.after_calls, [])


if __name__ == "__main__":
    unittest.main()
