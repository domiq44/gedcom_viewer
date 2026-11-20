"""Tests du mixin de prévisualisation d'images ImagePreviewMixin."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock

from ui.views.image_preview import ImagePreviewMixin


class _PreviewTestImagePreviewMixin(ImagePreviewMixin):
    """Mixin testable avec un label d'aperçu."""

    def __init__(self, translator):
        """Initialise le mixin avec un traducteur et un label mock."""
        self.translator = translator
        self.preview_label = MagicMock()
        self._preview_photo = None
        self.base_path = None


class TestImagePreviewMixin(unittest.TestCase):
    """Vérifie le comportement de prévisualisation ImagePreviewMixin."""

    def setUp(self):
        """Crée un mixin avec un traducteur basique."""
        self.translator = MagicMock()
        self.translator.get.side_effect = lambda key: key
        self.mixin = _PreviewTestImagePreviewMixin(self.translator)

    # Vérifie qu'aucun fichier affiche l'aperçu indisponible.
    def test_show_preview_without_file_shows_placeholder(self):
        """Vérifie qu'aucun fichier affiche l'aperçu indisponible."""
        self.mixin._show_preview(None)
        self.mixin.preview_label.configure.assert_called()
        self.assertIsNone(self.mixin._preview_photo)

    # Vérifie qu'un fichier relatif sans base_path affiche l'aperçu indisponible.
    def test_show_preview_without_base_path_shows_placeholder(self):
        """Vérifie qu'un fichier relatif sans base_path affiche l'aperçu indisponible."""
        self.mixin._show_preview("photo.jpg")
        self.mixin.preview_label.configure.assert_called()
        self.assertIsNone(self.mixin._preview_photo)

    # Vérifie qu'un chemin absolu valide est accepté sans base_path.
    def test_show_preview_with_absolute_path_without_base_path(self):
        """Vérifie qu'un chemin absolu valide est affiché sans base_path."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"\xff\xd8\xff\xe0")  # en-tête JPEG factice
            tmp_path = tmp.name
        try:
            self.mixin.base_path = None
            self.mixin.translator.get.side_effect = lambda key: key
            result = self.mixin._resolve_preview_path(tmp_path)
            self.assertEqual(result, os.path.realpath(tmp_path))
        finally:
            os.unlink(tmp_path)

    # Vérifie qu'une extension non supportée affiche l'aperçu indisponible.
    def test_show_preview_with_unknown_extension_shows_placeholder(self):
        """Vérifie qu'une extension non supportée affiche l'aperçu indisponible."""
        self.mixin.base_path = "/tmp"
        self.mixin._show_preview("photo.xyz")
        self.mixin.preview_label.configure.assert_called()
        self.assertIsNone(self.mixin._preview_photo)

    # Vérifie qu'un chemin absolu valide hors du répertoire de base est accepté.
    def test_resolve_preview_path_absolute_outside_base_is_accepted(self):
        """Vérifie qu'un chemin absolu valide hors de base_path est accepté."""
        with tempfile.TemporaryDirectory() as other_dir:
            img_path = os.path.join(other_dir, "photo.png")
            with open(img_path, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n")  # en-tête PNG factice
            self.mixin.base_path = "/tmp"
            self.mixin.translator.get.side_effect = lambda key: key
            result = self.mixin._resolve_preview_path(img_path)
            self.assertEqual(result, os.path.realpath(img_path))

    # Vérifie qu'un chemin hors du répertoire de base est rejeté s'il est inexistant.
    def test_resolve_preview_path_outside_base_nonexistent_is_none(self):
        """Vérifie qu'un chemin absolu inexistant est rejeté."""
        self.mixin.base_path = "/tmp"
        self.mixin.translator.get.side_effect = lambda key: key
        result = self.mixin._resolve_preview_path("/etc/passwd")
        self.assertIsNone(result)

    # Vérifie qu'un chemin inexistant est rejeté.
    def test_resolve_preview_path_nonexistent_is_none(self):
        """Vérifie qu'un chemin inexistant est rejeté."""
        self.mixin.base_path = "/tmp"
        self.mixin.translator.get.side_effect = lambda key: key
        result = self.mixin._resolve_preview_path("nonexistent.jpg")
        self.assertIsNone(result)

    # Vérifie set_base_path accepte un répertoire existant.
    def test_set_base_path_accepts_existing_directory(self):
        """Vérifie que set_base_path stocke un répertoire valide."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.mixin.set_base_path(tmpdir)
            self.assertEqual(self.mixin.base_path, tmpdir)

    # Vérifie set_base_path ignore un répertoire inexistant.
    def test_set_base_path_ignores_nonexistent_directory(self):
        """Vérifie que set_base_path met base_path à None pour un répertoire absent."""
        self.mixin.set_base_path("/chemin/inexistant/xyz")
        self.assertIsNone(self.mixin.base_path)

    # Vérifie set_base_path ignore une chaîne vide.
    def test_set_base_path_ignores_empty_string(self):
        """Vérifie que set_base_path met base_path à None pour une chaîne vide."""
        self.mixin.set_base_path("")
        self.assertIsNone(self.mixin.base_path)

    # Vérifie set_base_path ignore None.
    def test_set_base_path_ignores_none(self):
        """Vérifie que set_base_path met base_path à None pour None."""
        self.mixin.set_base_path(None)
        self.assertIsNone(self.mixin.base_path)

    # Vérifie _is_within_base retourne False sur ValueError (disques différents).
    def test_is_within_base_false_on_valueerror(self):
        """Vérifie que _is_within_base retourne False en cas de ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.mixin.base_path = tmpdir
            # Monkeypatch os.path.commonpath pour forcer ValueError
            original_commonpath = os.path.commonpath
            try:
                os.path.commonpath = lambda *args, **kwargs: (_ for _ in ()).throw(
                    ValueError("no common path")
                )
                result = self.mixin._is_within_base("/tmp/foo.jpg", tmpdir)
                self.assertFalse(result)
            finally:
                os.path.commonpath = original_commonpath

    # Vérifie _is_acceptable_file retourne False sur OSError (taille inaccessible).
    def test_is_acceptable_file_false_on_oserror(self):
        """Vérifie que _is_acceptable_file retourne False si getsize lève OSError."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            original_getsize = os.path.getsize
            try:
                os.path.getsize = lambda path: (_ for _ in ()).throw(
                    OSError("permission denied")
                )
                result = self.mixin._is_acceptable_file(tmp_path)
                self.assertFalse(result)
            finally:
                os.path.getsize = original_getsize
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
