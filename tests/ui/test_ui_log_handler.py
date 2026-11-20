"""Tests de mise en file des messages de journalisation."""

import logging
import queue
import unittest

from ui.ui_log_handler import UiLogHandler


def _make_record(message):
    """Construit un record de log minimal portant le message donné."""
    return logging.LogRecord("test", logging.INFO, __file__, 1, message, None, None)


class TestUiLogHandler(unittest.TestCase):
    """Vérifie la mise en file des messages de journalisation."""

    def setUp(self):
        self.log_queue = queue.Queue()
        self.handler = UiLogHandler(self.log_queue)

    # Vérifie emit enqueues the formatted message.
    def test_emit_enqueues_the_formatted_message(self):
        # Given (Arrange) un record de log et un format
        self.handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        record = _make_record("message")
        # When (Act) on émet le record
        self.handler.emit(record)
        # Then (Assert) le message est mis en file sans toucher l'interface
        self.assertEqual(self.log_queue.get_nowait(), "INFO: message")

    # Vérifie emit logs failures without propagating them.
    def test_emit_logs_failures(self):
        """Vérifie qu'un format invalide est journalisé sans propagation."""
        # Given (Arrange) un format qui échoue sur le record
        self.handler.setFormatter(logging.Formatter("%(missing)s"))
        record = _make_record("message")
        # When (Act) on émet le record
        with self.assertLogs("ui.ui_log_handler", level="ERROR") as logs:
            self.handler.emit(record)
        # Then (Assert) rien n'est mis en file et l'échec est journalisé
        self.assertTrue(self.log_queue.empty())
        self.assertIn("mise en file", logs.output[0])


if __name__ == "__main__":
    unittest.main()
