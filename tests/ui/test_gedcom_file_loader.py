"""Tests du chargeur de fichiers GEDCOM."""

import unittest
from unittest.mock import Mock

from ui.gedcom_file_loader import GedcomFileLoader


class TestGedcomFileLoader(unittest.TestCase):
    """Vérifie le chargement asynchrone."""

    def _loader(self, controller, on_loaded, on_error):
        """Construit un chargeur avec un contrôleur et des callbacks simulés."""
        return GedcomFileLoader(
            root=Mock(),
            controller_factory=lambda: controller,
            on_loaded=on_loaded,
            on_error=on_error,
            on_loading=Mock(),
        )

    # Vérifie load async delegates to coordinator.
    def test_load_async_delegates_to_coordinator(self):
        # Given un chargeur
        loader = self._loader(Mock(), Mock(), Mock())

        # When on lance un chargement asynchrone
        loader.load_coordinator.start = Mock(return_value=True)
        started = loader.load_async("/tmp/fichier.ged", strict=True)

        # Then le coordinateur reçoit la demande et le démarrage est confirmé
        loader.load_coordinator.start.assert_called_once_with(
            "/tmp/fichier.ged", strict=True
        )
        self.assertTrue(started)


if __name__ == "__main__":
    unittest.main()
