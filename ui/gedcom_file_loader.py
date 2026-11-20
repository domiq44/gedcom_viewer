"""Chargement asynchrone des fichiers GEDCOM."""

from ui.load_coordinator import LoadCoordinator


class GedcomFileLoader:
    """Charge un GEDCOM via un worker asynchrone."""

    def __init__(
        self,
        root,
        controller_factory,
        on_loaded,
        on_error,
        on_loading,
    ):
        """Initialise le chargeur et son coordinateur."""
        self._controller_factory = controller_factory
        self._on_loaded = on_loaded
        self._load_coordinator = LoadCoordinator(
            root=root,
            controller_factory=controller_factory,
            on_success=self._on_loaded,
            on_error=on_error,
            on_loading=on_loading,
        )

    @property
    def load_coordinator(self):
        """Retourne le coordinateur de chargement."""
        return self._load_coordinator

    def load_async(self, filename, strict=False):
        """Lance un chargement asynchrone et indique s'il a été lancé."""
        return self._load_coordinator.start(filename, strict=strict)

    def close(self):
        """Ferme le coordinateur de chargement."""
        self._load_coordinator.close()
