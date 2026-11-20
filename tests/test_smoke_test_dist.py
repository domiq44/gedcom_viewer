"""Tests du smoke-test de l'artefact PyInstaller."""

import io
import subprocess
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from scripts.smoke_test_dist import main


class TestSmokeTestDist(unittest.TestCase):
    """Vérifie les retours du smoke-test de l'artefact."""

    # Vérifie missing artifact is skipped without require artifact.
    def test_missing_artifact_is_skipped_without_require_artifact(self):
        # Given (Arrange) un artefact absent
        with patch("scripts.smoke_test_dist.os.path.exists", return_value=False):
            # When (Act) on exécute le smoke-test
            with redirect_stdout(io.StringIO()):
                status = main([])

        # Then (Assert) le test est ignoré
        self.assertEqual(status, 0)

    # Vérifie missing artifact fails when required.
    def test_missing_artifact_fails_when_required(self):
        # Given (Arrange) un artefact absent mais requis
        with patch("scripts.smoke_test_dist.os.path.exists", return_value=False):
            # When (Act) on exécute le smoke-test
            with redirect_stdout(io.StringIO()):
                status = main(["--require-artifact"])

        # Then (Assert) le test échoue
        self.assertEqual(status, 1)

    # Vérifie non executable artifact fails.
    def test_non_executable_artifact_fails(self):
        # Given (Arrange) un artefact non exécutable
        with patch("scripts.smoke_test_dist.os.path.exists", return_value=True):
            with patch("scripts.smoke_test_dist.os.path.isfile", return_value=True):
                with patch("scripts.smoke_test_dist.os.access", return_value=False):
                    # When (Act) on exécute le smoke-test
                    with redirect_stdout(io.StringIO()):
                        status = main([])

        # Then (Assert) le test échoue
        self.assertEqual(status, 1)

    # Vérifie timeout is treated as successful startup.
    def test_timeout_is_treated_as_successful_startup(self):
        # Given (Arrange) un binaire qui reste vivant jusqu'au timeout
        error = subprocess.TimeoutExpired(cmd="app", timeout=1)
        error.output = "started"
        with patch("scripts.smoke_test_dist.os.path.exists", return_value=True):
            with patch("scripts.smoke_test_dist.os.path.isfile", return_value=True):
                with patch("scripts.smoke_test_dist.os.access", return_value=True):
                    with patch(
                        "scripts.smoke_test_dist.shutil.which", return_value=None
                    ):
                        with patch(
                            "scripts.smoke_test_dist.subprocess.run", side_effect=error
                        ):
                            # When (Act) on exécute le smoke-test
                            with redirect_stdout(io.StringIO()):
                                status = main([])

        # Then (Assert) le démarrage est validé
        self.assertEqual(status, 0)

    # Vérifie early exit fails.
    def test_early_exit_fails(self):
        # Given (Arrange) un binaire qui s'arrête avant le timeout
        completed = Mock(stdout="stopped", returncode=1)
        with patch("scripts.smoke_test_dist.os.path.exists", return_value=True):
            with patch("scripts.smoke_test_dist.os.path.isfile", return_value=True):
                with patch("scripts.smoke_test_dist.os.access", return_value=True):
                    with patch(
                        "scripts.smoke_test_dist.shutil.which", return_value=None
                    ):
                        with patch(
                            "scripts.smoke_test_dist.subprocess.run",
                            return_value=completed,
                        ):
                            # When (Act) on exécute le smoke-test
                            with redirect_stdout(io.StringIO()):
                                status = main([])

        # Then (Assert) le test échoue
        self.assertEqual(status, 1)


if __name__ == "__main__":
    unittest.main()
