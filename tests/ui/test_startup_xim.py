"""Tests de la politique de désactivation de l'XIM IBus au démarrage."""

import logging
import os
import unittest
from unittest.mock import patch

from main import _disable_slow_ibus_xim


class TestStartupXimPolicy(unittest.TestCase):
    """Vérifie la politique de désactivation de l'XIM IBus au démarrage."""

    # Vérifie disables only ibus xim by default.
    def test_disables_only_ibus_xim_by_default(self):
        # Given XMODIFIERS vaut @im=ibus et aucune variable de garde
        with patch.dict(os.environ, {"XMODIFIERS": "@im=ibus"}):
            os.environ.pop("GEDCOM_VIEWER_KEEP_XIM", None)

            # When on désactive le XIM lent
            _disable_slow_ibus_xim(logging.getLogger("test.startup"))

            # Then XMODIFIERS est retiré
            self.assertNotIn("XMODIFIERS", os.environ)

        # Quand XMODIFIERS vaut @im=other
        with patch.dict(os.environ, {"XMODIFIERS": "@im=other"}):
            # When on désactive le XIM lent
            _disable_slow_ibus_xim(logging.getLogger("test.startup"))

            # Then XMODIFIERS est préservé
            self.assertEqual(os.environ["XMODIFIERS"], "@im=other")

    # Vérifie can keep ibus xim explicitly.
    def test_can_keep_ibus_xim_explicitly(self):
        # Given XMODIFIERS vaut @im=ibus et la garde est activée
        with patch.dict(
            os.environ,
            {"XMODIFIERS": "@im=ibus", "GEDCOM_VIEWER_KEEP_XIM": "1"},
        ):
            # When on désactive le XIM lent
            _disable_slow_ibus_xim(logging.getLogger("test.startup"))

            # Then XMODIFIERS est préservé
            self.assertEqual(os.environ["XMODIFIERS"], "@im=ibus")


if __name__ == "__main__":
    unittest.main()
