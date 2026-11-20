"""Tests de la désactivation conditionnelle de l'XIM IBus."""

import os
import unittest
from unittest.mock import Mock, patch

from main import _disable_slow_ibus_xim


class TestDisableSlowIbusXim(unittest.TestCase):
    """Vérifie la désactivation conditionnelle de l'XIM IBus."""

    # Vérifie removes xmodifiers for ibus.
    def test_removes_xmodifiers_for_ibus(self):
        # Given un environnement XIM IBus sans conservation explicite
        logger = Mock()
        environment = {"XMODIFIERS": "@im=ibus"}
        # When on désactive l'XIM IBus
        with patch.dict(os.environ, environment, clear=True):
            _disable_slow_ibus_xim(logger)
            # Then la variable est retirée et l'action est journalisée
            self.assertNotIn("XMODIFIERS", os.environ)
        logger.info.assert_called_once()

    # Vérifie keeps xmodifiers when keep flag is set.
    def test_keeps_xmodifiers_when_keep_flag_is_set(self):
        # Given un environnement XIM IBus avec conservation explicite
        logger = Mock()
        environment = {"XMODIFIERS": "@im=ibus", "GEDCOM_VIEWER_KEEP_XIM": "1"}
        # When on désactive l'XIM IBus
        with patch.dict(os.environ, environment, clear=True):
            _disable_slow_ibus_xim(logger)
            # Then la variable est conservée
            self.assertEqual(os.environ["XMODIFIERS"], "@im=ibus")
        logger.info.assert_not_called()

    # Vérifie keeps xmodifiers for other input method.
    def test_keeps_xmodifiers_for_other_input_method(self):
        # Given un environnement XIM différent d'IBus
        logger = Mock()
        environment = {"XMODIFIERS": "@im=fcitx"}
        # When on désactive l'XIM IBus
        with patch.dict(os.environ, environment, clear=True):
            _disable_slow_ibus_xim(logger)
            # Then la variable est conservée
            self.assertEqual(os.environ["XMODIFIERS"], "@im=fcitx")
        logger.info.assert_not_called()

    # Vérifie does nothing without xmodifiers.
    def test_does_nothing_without_xmodifiers(self):
        # Given un environnement sans variable XMODIFIERS
        logger = Mock()
        # When on désactive l'XIM IBus
        with patch.dict(os.environ, {}, clear=True):
            _disable_slow_ibus_xim(logger)
            # Then aucune variable n'est ajoutée
            self.assertNotIn("XMODIFIERS", os.environ)
        logger.info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
