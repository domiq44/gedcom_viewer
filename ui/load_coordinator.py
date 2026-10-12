import queue
import threading
import time


class LoadCoordinator:
    """Coordonne le chargement GEDCOM hors du thread Tkinter."""

    POLL_INTERVAL_MS = 25

    def __init__(self, root, controller_factory, on_success, on_error, on_loading):
        self.root = root
        self.controller_factory = controller_factory
        self.on_success = on_success
        self.on_error = on_error
        self.on_loading = on_loading
        self._results = queue.Queue()
        self._is_loading = False
        self._is_closing = False

    @property
    def is_loading(self):
        return self._is_loading

    @property
    def is_closing(self):
        return self._is_closing

    def start(self, filename, strict=False):
        if not filename or self._is_loading or self._is_closing:
            return

        self._is_loading = True
        load_started_at = time.perf_counter()
        self.on_loading()

        def load_in_worker():
            error = None
            loaded_controller = None
            try:
                loaded_controller = self.controller_factory()
                loaded_controller.load_file(filename, strict=strict)
            except Exception as exc:
                error = exc
            self._results.put((filename, load_started_at, error, loaded_controller))

        threading.Thread(target=load_in_worker, daemon=True).start()
        self.root.after(self.POLL_INTERVAL_MS, self._poll_result)

    def _poll_result(self):
        if self._is_closing:
            return

        try:
            result = self._results.get_nowait()
        except queue.Empty:
            self.root.after(self.POLL_INTERVAL_MS, self._poll_result)
            return

        self._is_loading = False
        filename, load_started_at, error, loaded_controller = result
        if error is not None:
            self.on_error(filename, error)
            return

        self.on_success(filename, load_started_at, loaded_controller)

    def close(self):
        self._is_closing = True
        self._is_loading = False
