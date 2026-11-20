"""Coordonne le résultat du chargement asynchrone."""

import logging
import queue
import threading
import time

logger = logging.getLogger(__name__)


class LoadCoordinator:
    """Coordonne le chargement GEDCOM hors du thread Tkinter."""

    POLL_INTERVAL_MS = 25
    DEFAULT_TIMEOUT_S = 120

    def __init__(self, root, controller_factory, on_success, on_error, on_loading):
        """Initialise le coordinateur et sa file de résultats."""
        self.root = root
        self.controller_factory = controller_factory
        self.on_success = on_success
        self.on_error = on_error
        self.on_loading = on_loading
        self._results: queue.Queue = queue.Queue()
        self._is_loading = False
        self._is_closing = False
        self._load_token = 0
        self._current_filename = None
        self._load_started_at = None
        self._timeout_s = self.DEFAULT_TIMEOUT_S
        self._cancel_event = threading.Event()

    @property
    def is_loading(self):
        """Indique si un chargement est en cours."""
        return self._is_loading

    def start(self, filename, strict=False, timeout=None):
        """Démarre le chargement dans un worker et indique s'il a été lancé."""
        if not filename or self._is_loading or self._is_closing:
            return False

        self._drain_results()
        cancel_event = threading.Event()
        self._cancel_event = cancel_event
        self._is_loading = True
        self._load_token += 1
        load_token = self._load_token
        self._current_filename = filename
        self._timeout_s = self.DEFAULT_TIMEOUT_S if timeout is None else timeout
        load_started_at = time.perf_counter()
        self._load_started_at = load_started_at
        self.on_loading()

        def load_in_worker():
            """Exécute le chargement dans le thread worker."""
            error = None
            loaded_controller = None
            try:
                loaded_controller = self.controller_factory()
                loaded_controller.load_file(
                    filename, strict=strict, cancel_event=cancel_event
                )
            except Exception as exc:
                error = exc
            if cancel_event.is_set():
                return
            self._results.put(
                (load_token, filename, load_started_at, error, loaded_controller)
            )

        threading.Thread(target=load_in_worker, daemon=True).start()
        self.root.after(self.POLL_INTERVAL_MS, self._poll_result)
        return True

    def _poll_result(self):
        """Récupère et traite le résultat du chargement."""
        if self._is_closing or not self._is_loading:
            self._drain_results()
            return

        try:
            result = self._results.get_nowait()
        except queue.Empty:
            self._poll_timeout()
            if self._is_loading:
                self.root.after(self.POLL_INTERVAL_MS, self._poll_result)
            return

        load_token, filename, load_started_at, error, loaded_controller = result
        if load_token != self._load_token:
            if self._is_loading:
                self.root.after(self.POLL_INTERVAL_MS, self._poll_result)
            return

        self._is_loading = False
        if error is not None:
            self._dispatch(self.on_error, "on_error", filename, error)
            return

        self._dispatch(
            self.on_success, "on_success", filename, load_started_at, loaded_controller
        )

    def _poll_timeout(self):
        """Déclenche l'erreur de délai dépassé si nécessaire."""
        if self._timeout_s is None or self._timeout_s <= 0:
            return
        if self._load_started_at is None:
            return
        if time.perf_counter() - self._load_started_at < self._timeout_s:
            return

        filename = self._current_filename
        self._load_token += 1
        self._is_loading = False
        self._cancel_event.set()
        self._drain_results()
        self._dispatch(
            self.on_error,
            "on_error",
            filename,
            TimeoutError(f"Chargement de {filename} expiré après {self._timeout_s}s"),
        )

    def _dispatch(self, callback, callback_name, *args):
        """Invoque un callback en journalisant les erreurs."""
        try:
            callback(*args)
        except Exception:
            logger.exception(
                "Exception dans le callback %s du chargement", callback_name
            )

    def cancel(self):
        """Annule le chargement en cours."""
        if not self._is_loading:
            return
        self._load_token += 1
        self._is_loading = False
        self._cancel_event.set()
        self._drain_results()

    def close(self):
        """Empêche tout nouveau chargement."""
        self._is_closing = True
        self._load_token += 1
        self._is_loading = False
        self._cancel_event.set()
        self._drain_results()

    def _drain_results(self):
        """Vide la file des résultats en attente."""
        while True:
            try:
                self._results.get_nowait()
            except queue.Empty:
                return
