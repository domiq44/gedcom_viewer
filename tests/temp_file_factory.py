"""Fabrique des fichiers temporaires refermés pour les tests multiplateformes."""

import os
import tempfile


def write_temp_text(test_case, content):
    """Écrit un fichier texte temporaire fermé et planifie sa suppression."""
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
    test_case.addCleanup(os.unlink, handle.name)
    handle.write(content)
    handle.close()
    return handle.name


def write_temp_bytes(test_case, content):
    """Écrit un fichier binaire temporaire fermé et planifie sa suppression."""
    handle = tempfile.NamedTemporaryFile("wb", delete=False)
    test_case.addCleanup(os.unlink, handle.name)
    handle.write(content)
    handle.close()
    return handle.name
