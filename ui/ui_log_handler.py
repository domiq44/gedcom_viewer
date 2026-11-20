"""Publication des messages de journalisation dans la barre de statut.

Le handler ne touche jamais Tkinter : il dépose les messages dans une file
thread-safe, vidée par :class:`UiLogPump` sur le thread de l'interface. Ce
schéma file + polling est celui de :class:`ui.load_coordinator.LoadCoordinator`.
"""

import logging
import queue

logger = logging.getLogger(__name__)


class UiLogHandler(logging.Handler):
    """Dépose les messages de log formatés dans une file thread-safe."""

    def __init__(self, log_queue):
        """Mémorise la file de destination des messages."""
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        """Met en file le message formaté sans jamais toucher l'interface."""
        try:
            self.log_queue.put(self.format(record))
        except Exception:
            logger.exception("Échec de mise en file du message de journalisation")


class UiLogPump:
    """Vide la file de journalisation et met à jour la barre de statut."""

    POLL_INTERVAL_MS = 100

    def __init__(self, root, status_var, log_queue):
        """Initialise la pompe avec la racine Tk, la variable et la file."""
        self.root = root
        self.status_var = status_var
        self.log_queue = log_queue
        self._after_id = None

    def start(self):
        """Démarre le polling de la file sur le thread de l'interface."""
        if self._after_id is None:
            self._schedule()

    def stop(self):
        """Arrête le polling de la file."""
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None

    def _schedule(self):
        """Reprogramme le prochain vidage de la file."""
        self._after_id = self.root.after(self.POLL_INTERVAL_MS, self._drain)

    def _drain(self):
        """Publie le dernier message en attente puis se reprogramme."""
        message = None
        while True:
            try:
                message = self.log_queue.get_nowait()
            except queue.Empty:
                break

        if message is not None:
            self.status_var.set(message)
        self._schedule()
