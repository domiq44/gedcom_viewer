"""Tests de publication des messages en attente dans la barre de statut."""

import queue
import tkinter as tk
import unittest

from ui.ui_log_handler import UiLogPump


class TestUiLogPump(unittest.TestCase):
    """Vérifie la publication des messages en attente dans la barre de statut."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.status_var = tk.StringVar()
        self.log_queue = queue.Queue()
        self.pump = UiLogPump(self.root, self.status_var, self.log_queue)

    def tearDown(self):
        self.pump.stop()
        self.root.destroy()

    # Vérifie drain publishes the latest queued message.
    def test_drain_publishes_the_latest_queued_message(self):
        # Given (Arrange) deux messages en attente
        self.log_queue.put("premier")
        self.log_queue.put("dernier")
        # When (Act) on vide la file
        self.pump._drain()
        # Then (Assert) seul le dernier message est publié
        self.assertEqual(self.status_var.get(), "dernier")
        self.assertTrue(self.log_queue.empty())

    # Vérifie drain keeps the status unchanged when the queue is empty.
    def test_drain_keeps_the_status_when_the_queue_is_empty(self):
        # Given (Arrange) une file vide
        # When (Act) on vide la file
        self.pump._drain()
        # Then (Assert) la barre de statut reste inchangée
        self.assertEqual(self.status_var.get(), "")

    # Vérifie start and stop schedule then cancel the polling.
    def test_start_and_stop_schedule_then_cancel_the_polling(self):
        # Given (Arrange) une pompe arrêtée
        # When (Act) on démarre puis on arrête la pompe
        self.pump.start()
        scheduled = self.pump._after_id
        self.pump.stop()
        # Then (Assert) le polling est programmé puis annulé
        self.assertIsNotNone(scheduled)
        self.assertIsNone(self.pump._after_id)


if __name__ == "__main__":
    unittest.main()
