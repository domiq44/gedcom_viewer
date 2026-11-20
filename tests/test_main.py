"""Tests du démarrage de l'application et de la gestion des erreurs."""

import logging
import os
import tempfile
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch

from main import main


class _FakeRoot:
    """Fenêtre Tk factice enregistrant les bindings et callbacks."""

    def __init__(self):
        """Initialise les collections d'appels."""
        self.bind_all_calls = []
        self.bind_calls = []
        self.unbind_all_calls = []
        self.unbind_calls = []
        self.after_calls = []
        self.after_idle_calls = []
        self.mainloop_calls = 0

    def bind_all(self, sequence, func, add=None):
        """Enregistre un binding global."""
        self.bind_all_calls.append((sequence, func, add))
        return "bind-all"

    def bind(self, sequence, func, add=None):
        """Enregistre un binding."""
        self.bind_calls.append((sequence, func, add))
        return "binding"

    def unbind_all(self, sequence):
        """Enregistre la suppression d'un binding global."""
        self.unbind_all_calls.append(sequence)

    def unbind(self, sequence, funcid):
        """Enregistre la suppression d'un binding."""
        self.unbind_calls.append((sequence, funcid))

    def after(self, delay, func, *args):
        """Enregistre une planification différée."""
        self.after_calls.append((delay, func, args))
        return f"after-{len(self.after_calls)}"

    def after_idle(self, func, *args):
        """Enregistre une planification idle."""
        self.after_idle_calls.append((func, args))
        return f"idle-{len(self.after_idle_calls)}"

    def mainloop(self):
        """Compte l'appel à la boucle principale."""
        self.mainloop_calls += 1


class TestMain(unittest.TestCase):
    """Vérifie le démarrage de l'application et la gestion des erreurs."""

    def _run_main(self, root):
        """Exécute main() avec une fenêtre Tk factice et restaure les logs."""
        root_logger = logging.getLogger()
        saved_handlers = root_logger.handlers[:]
        root_logger.handlers = []
        try:
            main()
        finally:
            for handler in root_logger.handlers:
                handler.close()
            root_logger.handlers = saved_handlers
        return root

    # Vérifie main wires and drives startup diagnostics.
    def test_main_wires_and_drives_startup_diagnostics(self):
        # Given une fenêtre Tk factice et un dossier temporaire
        root = _FakeRoot()
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "gedcom.log")
            with ExitStack() as stack:
                stack.enter_context(
                    patch("main.os.path.expanduser", return_value=log_path)
                )
                dump_later = stack.enter_context(
                    patch("main.faulthandler.dump_traceback_later")
                )
                cancel_later = stack.enter_context(
                    patch("main.faulthandler.cancel_dump_traceback_later")
                )
                stack.enter_context(patch("tkinter.Tk", return_value=root))
                viewer_class = stack.enter_context(patch("ui.main_window.GedcomViewer"))
                stack.enter_context(patch("ui.themes.apply_app_theme"))

                self._run_main(root)

                # Then les bindings et callbacks de démarrage sont installés
                self.assertEqual(root.bind_all_calls[0][0], "<Configure>")
                self.assertEqual(root.bind_all_calls[0][2], "+")
                self.assertEqual(root.bind_calls[0][0], "<Map>")
                self.assertEqual(root.bind_calls[0][2], "+")
                self.assertEqual(root.after_calls[0][0], 2000)
                self.assertEqual(root.after_calls[1][0], 0)
                self.assertEqual(root.after_idle_calls[0][0].__name__, "log_first_idle")
                viewer_class.assert_called_once_with(root)
                self.assertEqual(root.mainloop_calls, 1)
                dump_later.assert_called_once()

                # When on simule les événements de démarrage
                configure_callback = root.bind_all_calls[0][1]
                configure_callback(SimpleNamespace())
                progress_callback = root.after_calls[0][1]
                with self.assertLogs(level="INFO") as logs:
                    progress_callback()
                self.assertIn("Attente démarrage Tk", "\n".join(logs.output))
                self.assertEqual(len(root.after_calls), 3)

                map_callback = root.bind_calls[0][1]
                with self.assertLogs(level="INFO") as logs:
                    map_callback(SimpleNamespace(widget=root))
                self.assertIn("1 événements Configure", "\n".join(logs.output))
                self.assertIn(("<Map>", "binding"), root.unbind_calls)
                cancel_later.assert_called_once()

                idle_callback = root.after_idle_calls[0][0]
                with self.assertLogs(level="INFO"):
                    idle_callback()
                self.assertIn("<Configure>", root.unbind_all_calls)

                # Then le suivi ne replanifie plus après idle
                after_count = len(root.after_calls)
                progress_callback()
                self.assertEqual(len(root.after_calls), after_count)

                # Then le lambda de la boucle Tk journalise son état
                zero_callback = root.after_calls[1][1]
                with self.assertLogs(level="INFO") as logs:
                    zero_callback()
                self.assertIn("Boucle d'événements Tk active", "\n".join(logs.output))

    # Vérifie main builds viewer and runs mainloop.
    def test_main_builds_viewer_and_runs_mainloop(self):
        # Given une fenêtre Tk factice et un dossier temporaire
        root = Mock()
        root.bind = Mock(return_value="binding")
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "gedcom.log")
            with patch("main.os.path.expanduser", return_value=log_path):
                with patch("main.faulthandler.dump_traceback_later") as dump_later:
                    with patch("tkinter.Tk", return_value=root):
                        with patch("ui.main_window.GedcomViewer") as viewer_class:
                            with patch("ui.themes.apply_app_theme"):
                                # When on démarre l'application
                                self._run_main(root)
        # Then la vue est construite et la boucle Tk est lancée
        viewer_class.assert_called_once_with(root)
        root.mainloop.assert_called_once_with()
        dump_later.assert_called_once()

    # Vérifie main logs and reraises on exception.
    def test_main_logs_and_reraises_on_exception(self):
        # Given une erreur de création de la fenêtre Tk
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "gedcom.log")
            with patch("main.os.path.expanduser", return_value=log_path):
                with patch("main.faulthandler.dump_traceback_later"):
                    with patch("tkinter.Tk", side_effect=RuntimeError("boom")):
                        with patch("ui.themes.apply_app_theme"):
                            # When on démarre l'application
                            # Then l'exception est journalisée puis relancée
                            with self.assertRaises(RuntimeError):
                                self._run_main(Mock())


if __name__ == "__main__":
    unittest.main()
