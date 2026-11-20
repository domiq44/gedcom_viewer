"""Tests du coordinateur de chargement asynchrone : publication, erreurs et fermeture."""

import time
import unittest
from unittest.mock import Mock, patch

from ui.load_coordinator import LoadCoordinator


class FakeRoot:
    """Doublure de racine Tk pour les tests du coordinateur de chargement."""

    def __init__(self):
        self.after_calls = []

    def after(self, delay, callback):
        self.after_calls.append((delay, callback))


class TestLoadCoordinator(unittest.TestCase):
    """Vérifie le flux de chargement asynchrone, ses erreurs et sa fermeture."""

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

    # Vérifie start publishes success result.
    def test_start_publishes_success_result(self):
        # Given (Arrange) un coordinateur et un worker mocké
        with patch("ui.load_coordinator.threading.Thread") as thread_class:
            # When (Act) on lance le chargement puis on résout le résultat
            self.coordinator.start("/tmp/test.ged", strict=True)
            thread_class.call_args.kwargs["target"]()
            self.coordinator._poll_result()
        # Then (Assert) le succès est publié avec le contrôleur chargé
        self.on_error.assert_not_called()
        self.on_success.assert_called_once()
        self.assertIs(self.on_success.call_args.args[2], self.controller)

    # Vérifie start calls load file in worker.
    def test_start_calls_load_file_in_worker(self):
        # Given (Arrange) un worker mocké
        with patch("ui.load_coordinator.threading.Thread") as thread_class:
            # When (Act) on lance le chargement strict
            self.coordinator.start("/tmp/test.ged", strict=True)
            thread_class.call_args.kwargs["target"]()
        # Then (Assert) le fichier est chargé avec le mode strict et l'annulation
        self.controller.load_file.assert_called_once()
        self.assertEqual(self.controller.load_file.call_args.args, ("/tmp/test.ged",))
        self.assertTrue(self.controller.load_file.call_args.kwargs["strict"])
        self.assertIsNotNone(self.controller.load_file.call_args.kwargs["cancel_event"])

    # Vérifie start returns true when worker is scheduled.
    def test_start_returns_true_when_worker_is_scheduled(self):
        # Given (Arrange) un coordinateur disponible
        with patch("ui.load_coordinator.threading.Thread"):
            # When (Act) on lance le chargement
            started = self.coordinator.start("/tmp/test.ged")
        # Then (Assert) le démarrage est confirmé
        self.assertTrue(started)

    # Vérifie start returns false when already loading.
    def test_start_returns_false_when_already_loading(self):
        # Given (Arrange) un chargement déjà en cours
        with patch("ui.load_coordinator.threading.Thread"):
            self.coordinator.start("/tmp/test.ged")
            # When (Act) on relance un chargement
            started = self.coordinator.start("/tmp/second.ged")
        # Then (Assert) le second démarrage est refusé
        self.assertFalse(started)

    # Vérifie start flags loading.
    def test_start_flags_loading(self):
        # Given (Arrange) un worker mocké
        with patch("ui.load_coordinator.threading.Thread"):
            # When (Act) on lance le chargement
            self.coordinator.start("/tmp/test.ged")
            is_loading = self.coordinator.is_loading
        # Then (Assert) le coordinateur est marqué comme en cours de chargement
        self.assertTrue(is_loading)

    # Vérifie worker error is routed to on error.
    def test_worker_error_is_routed_to_on_error(self):
        # Given (Arrange) un contrôleur qui échoue au chargement
        error = ValueError("invalid GEDCOM")
        self.controller.load_file.side_effect = error
        with patch("ui.load_coordinator.threading.Thread") as thread_class:
            # When (Act) on lance puis résout le résultat
            self.coordinator.start("/tmp/test.ged")
            thread_class.call_args.kwargs["target"]()
            self.coordinator._poll_result()
        # Then (Assert) l'erreur est routée vers on_error, pas on_success
        self.on_success.assert_not_called()
        self.on_error.assert_called_once_with("/tmp/test.ged", error)

    # Vérifie second start is ignored while loading.
    def test_second_start_is_ignored_while_loading(self):
        # Given (Arrange) un coordinateur déjà en cours de chargement
        with patch("ui.load_coordinator.threading.Thread") as thread_class:
            self.coordinator.start("/tmp/first.ged")
            # When (Act) on tente un second lancement
            self.coordinator.start("/tmp/second.ged")
        # Then (Assert) un seul worker a été démarré
        self.assertEqual(thread_class.call_count, 1)

    # Vérifie poll reschedules when result not ready.
    def test_poll_reschedules_when_result_not_ready(self):
        # Given (Arrange) un coordinateur sans résultat disponible
        self.coordinator.start = Mock()
        self.coordinator._is_loading = True
        # When (Act) on interroge le résultat
        self.coordinator._poll_result()
        # Then (Assert) un nouveau poll est reprogrammé
        self.assertEqual(len(self.root.after_calls), 1)
        self.assertEqual(self.root.after_calls[0][0], LoadCoordinator.POLL_INTERVAL_MS)

    # Vérifie close ignores pending result.
    def test_close_ignores_pending_result(self):
        # Given (Arrange) un coordinateur fermé avec un résultat en attente
        self.coordinator.close()
        self.coordinator._results.put((1, "/tmp/test.ged", 1.0, None, self.controller))
        # When (Act) on interroge le résultat
        self.coordinator._poll_result()
        # Then (Assert) aucun callback n'est déclenché
        self.on_success.assert_not_called()
        self.on_error.assert_not_called()

    # Vérifie on success exception does not propagate.
    def test_on_success_exception_does_not_propagate(self):
        # Given (Arrange) un on_success qui lève une exception
        self.on_success.side_effect = RuntimeError("boom")
        self.coordinator._is_loading = True
        self.coordinator._load_token = 1
        self.coordinator._results.put((1, "/tmp/test.ged", 1.0, None, self.controller))
        # When (Act) on résout le résultat
        self.coordinator._poll_result()
        # Then (Assert) aucune exception ne remonte et le chargement est terminé
        self.assertFalse(self.coordinator.is_loading)

    # Vérifie on error exception does not propagate.
    def test_on_error_exception_does_not_propagate(self):
        # Given (Arrange) un on_error qui lève une exception
        error = ValueError("invalid")
        self.on_error.side_effect = RuntimeError("boom")
        self.coordinator._is_loading = True
        self.coordinator._load_token = 1
        self.coordinator._results.put((1, "/tmp/test.ged", 1.0, error, None))
        # When (Act) on résout le résultat
        self.coordinator._poll_result()
        # Then (Assert) aucune exception ne remonte et le chargement est terminé
        self.assertFalse(self.coordinator.is_loading)

    # Vérifie timeout dispatches timeout error.
    def test_timeout_dispatches_timeout_error(self):
        # Given (Arrange) un chargement expiré
        with patch("ui.load_coordinator.threading.Thread"):
            self.coordinator.start("/tmp/slow.ged", timeout=0.01)
        self.coordinator._load_started_at = 0.0

        # When (Act) on interroge le résultat
        self.coordinator._poll_result()

        # Then (Assert) une TimeoutError est routée vers on_error
        self.on_success.assert_not_called()
        self.on_error.assert_called_once()
        self.assertIsInstance(self.on_error.call_args.args[1], TimeoutError)
        self.assertFalse(self.coordinator.is_loading)

    # Vérifie cancel ignores worker result.
    def test_cancel_ignores_worker_result(self):
        # Given (Arrange) un chargement annulé
        with patch("ui.load_coordinator.threading.Thread") as thread_class:
            self.coordinator.start("/tmp/test.ged")
            thread_class.call_args.kwargs["target"]()
            self.coordinator.cancel()

            # When (Act) on interroge le résultat
            self.coordinator._poll_result()

        # Then (Assert) aucun callback n'est déclenché
        self.on_success.assert_not_called()
        self.on_error.assert_not_called()

    # Vérifie cancel signals worker and drains results.
    def test_cancel_signals_worker_and_drains_results(self):
        # Given un chargement en cours avec un résultat en attente
        self.coordinator._is_loading = True
        self.coordinator._load_token = 1
        self.coordinator._results.put((1, "/tmp/test.ged", 1.0, None, self.controller))

        # When on annule le chargement
        self.coordinator.cancel()

        # Then le worker est signalé et la file est vidée
        self.assertTrue(self.coordinator._cancel_event.is_set())
        self.assertTrue(self.coordinator._results.empty())

    # Vérifie cancelled worker does not publish result.
    def test_cancelled_worker_does_not_publish_result(self):
        # Given un chargement annulé avant la fin du worker
        with patch("ui.load_coordinator.threading.Thread") as thread_class:
            self.coordinator.start("/tmp/test.ged")
            self.coordinator.cancel()

            # When le worker se termine
            thread_class.call_args.kwargs["target"]()

        # Then aucun résultat n'est déposé
        self.assertTrue(self.coordinator._results.empty())

    # Vérifie timeout signals worker and drains results.
    def test_timeout_signals_worker_and_drains_results(self):
        # Given un chargement expiré avec un résultat en attente
        self.coordinator._is_loading = True
        self.coordinator._load_token = 1
        self.coordinator._timeout_s = 0.01
        self.coordinator._load_started_at = 0.0
        self.coordinator._results.put((1, "/tmp/test.ged", 1.0, None, self.controller))

        # When on vérifie le délai dépassé
        self.coordinator._poll_timeout()

        # Then le worker est signalé et la file est vidée
        self.assertTrue(self.coordinator._cancel_event.is_set())
        self.assertTrue(self.coordinator._results.empty())

    # Vérifie poll result ignores stale token.
    def test_poll_result_ignores_stale_token(self):
        # Given un résultat portant un jeton obsolète
        self.coordinator._is_loading = True
        self.coordinator._load_token = 2
        self.coordinator._results.put((1, "/tmp/old.ged", 1.0, None, self.controller))

        # When on interroge le résultat
        self.coordinator._poll_result()

        # Then aucun callback n'est déclenché et le chargement continue
        self.on_success.assert_not_called()
        self.on_error.assert_not_called()
        self.assertTrue(self.coordinator._is_loading)

    # Vérifie poll timeout returns when disabled.
    def test_poll_timeout_returns_when_disabled(self):
        # Given un délai désactivé
        self.coordinator._timeout_s = 0
        self.coordinator._load_started_at = 0.0

        # When on vérifie le délai dépassé
        self.coordinator._poll_timeout()

        # Then aucune erreur n'est déclenchée
        self.on_error.assert_not_called()

    # Vérifie poll timeout returns before deadline.
    def test_poll_timeout_returns_before_deadline(self):
        # Given un chargement pas encore expiré
        self.coordinator._timeout_s = 120
        self.coordinator._load_started_at = time.perf_counter()

        # When on vérifie le délai dépassé
        self.coordinator._poll_timeout()

        # Then aucune erreur n'est déclenchée
        self.on_error.assert_not_called()

    # Vérifie cancel without loading is noop.
    def test_cancel_without_loading_is_noop(self):
        # Given aucun chargement en cours
        # When on annule
        self.coordinator.cancel()

        # Then le worker n'est pas signalé
        self.assertFalse(self.coordinator._cancel_event.is_set())


if __name__ == "__main__":
    unittest.main()
