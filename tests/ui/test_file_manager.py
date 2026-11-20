"""Tests du gestionnaire de fichiers récents."""

import os
import tempfile
import unittest

from ui.file_manager import FileManager
from ui.i18n import Translator


class TestFileManager(unittest.TestCase):
    """Vérifie les options de dialogue et la mémorisation des fichiers."""

    # Vérifie file dialog options uses last directory.
    def test_file_dialog_options_uses_last_directory(self):
        # Given un gestionnaire avec un répertoire existant
        manager = FileManager(None, Translator("fr"), last_directory=os.getcwd())

        # When on demande les options du dialogue
        options = manager.file_dialog_options()

        # Then le répertoire courant est proposé
        self.assertEqual(options, {"initialdir": os.getcwd()})

    # Vérifie file dialog options falls back to home.
    def test_file_dialog_options_falls_back_to_home(self):
        # Given un gestionnaire avec un répertoire inexistant
        manager = FileManager(
            None, Translator("fr"), last_directory="/dossier/inexistant"
        )

        # When on demande les options du dialogue
        options = manager.file_dialog_options()

        # Then le répertoire personnel est proposé
        self.assertEqual(options, {"initialdir": os.path.expanduser("~")})

    # Vérifie remember recent file moves to front and caps ten.
    def test_remember_recent_file_moves_to_front_and_caps_ten(self):
        # Given un gestionnaire sans fichier récent
        manager = FileManager(None, Translator("fr"))
        temp_dir = tempfile.gettempdir()

        # When on mémorise onze fichiers
        for index in range(11):
            manager.remember_recent_file(os.path.join(temp_dir, f"fichier-{index}.ged"))

        # Then seuls dix fichiers restent, le plus récent en tête
        self.assertEqual(len(manager.recent_files), 10)
        self.assertEqual(
            manager.recent_files[0],
            os.path.abspath(os.path.join(temp_dir, "fichier-10.ged")),
        )
        self.assertEqual(manager.last_directory, os.path.abspath(temp_dir))

    # Vérifie remember recent file removes duplicates.
    def test_remember_recent_file_removes_duplicates(self):
        # Given un gestionnaire avec un fichier déjà mémorisé
        manager = FileManager(None, Translator("fr"))
        temp_dir = tempfile.gettempdir()
        path = os.path.join(temp_dir, "fichier.ged")
        manager.remember_recent_file(path)

        # When on mémorise à nouveau le même fichier
        manager.remember_recent_file(path)

        # Then il n'apparaît qu'une fois, en tête
        self.assertEqual(manager.recent_files, [os.path.abspath(path)])


if __name__ == "__main__":
    unittest.main()
