"""Tests du magasin de fichiers récents : sauvegarde, chargement et validation."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from controllers.recent_files_store import RecentFilesStore


class TestRecentFilesStore(unittest.TestCase):
    """Vérifie la sauvegarde, le chargement et la validation des fichiers récents."""

    # Vérifie save and load round trip.
    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            store = RecentFilesStore(settings_path)

            store.save(
                ["/tmp/example.ged"],
                "/tmp",
                "fr",
                window_size=(1280, 800),
                view_preferences={
                    "indent": False,
                    "show_gedcom_view": False,
                    "show_entity_view": True,
                },
            )
            recent_files, last_directory, language = store.load(directory)

            self.assertEqual(recent_files, ["/tmp/example.ged"])
            self.assertEqual(
                store.view_preferences,
                {
                    "indent": False,
                    "show_gedcom_view": False,
                    "show_entity_view": True,
                },
            )
            self.assertEqual(last_directory, "/tmp")
            self.assertEqual(language, "fr")
            self.assertEqual(store.window_size, (1280, 800))

    # Vérifie load ignores invalid window size.
    def test_load_ignores_invalid_window_size(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                json.dump({"window_size": {"width": "1280", "height": 800}}, handle)

            store = RecentFilesStore(settings_path)
            store.load(directory)

            self.assertIsNone(store.window_size)

    # Vérifie load filters invalid view preferences.
    def test_load_filters_invalid_view_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "view_preferences": {
                            "indent": "false",
                            "show_entity_view": True,
                            "show_gedcom_view": "false",
                            "unknown": True,
                        }
                    },
                    handle,
                )

            store = RecentFilesStore(settings_path)
            store.load(directory)

            self.assertEqual(store.view_preferences, {"show_entity_view": True})

    # Vérifie load filters invalid recent files.
    def test_load_filters_invalid_recent_files(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "recent_files": ["/tmp/example.ged", 42, None],
                        "last_directory": directory,
                    },
                    handle,
                )

            recent_files, last_directory, language = RecentFilesStore(
                settings_path
            ).load("/tmp")

            self.assertEqual(recent_files, ["/tmp/example.ged"])
            self.assertEqual(last_directory, directory)
            self.assertIsNone(language)

    # Vérifie load missing settings returns defaults.
    def test_load_missing_settings_returns_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "missing.json")

            result = RecentFilesStore(settings_path).load(directory)

            self.assertEqual(result, ([], directory, None))

    # Vérifie storage errors do not log paths or error text.
    def test_storage_errors_do_not_log_paths_or_error_text(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                handle.write("{}")

            def failing_opener(*args, **kwargs):
                raise OSError(f"cannot access {settings_path}")

            store = RecentFilesStore(settings_path, file_opener=failing_opener)
            with self.assertLogs(
                "controllers.recent_files_store", level="WARNING"
            ) as logs:
                store.load(directory)
            self.assertNotIn(settings_path, logs.output[0])
            self.assertNotIn("cannot access", logs.output[0])

            with self.assertLogs(
                "controllers.recent_files_store", level="WARNING"
            ) as logs:
                store.save([], directory, "en")
            self.assertNotIn(settings_path, logs.output[0])
            self.assertNotIn("cannot access", logs.output[0])

    # Vérifie save limits recent files to ten.
    def test_save_limits_recent_files_to_ten(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            recent_files = [f"/tmp/file-{index}.ged" for index in range(12)]

            RecentFilesStore(settings_path).save(recent_files, directory, "en")

            with open(settings_path, encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data["recent_files"], recent_files[:10])

    # Vérifie save replaces atomically without leftover files.
    def test_save_replaces_atomically_without_leftover_files(self):
        # Given un fichier de configuration existant
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                handle.write('{"recent_files": ["old"]}')

            # When on enregistre une nouvelle configuration
            RecentFilesStore(settings_path).save(["/tmp/new.ged"], directory, "fr")

            # Then le fichier est remplacé sans laisser de fichier temporaire
            with open(settings_path, encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data["recent_files"], ["/tmp/new.ged"])
            self.assertEqual(os.listdir(directory), ["settings.json"])

    # Vérifie save failure keeps previous file.
    def test_save_failure_keeps_previous_file(self):
        # Given un fichier de configuration existant et un écrivain défaillant
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                handle.write('{"recent_files": ["old"]}')

            def failing_opener(*args, **kwargs):
                raise OSError("boom")

            store = RecentFilesStore(settings_path, file_opener=failing_opener)

            # When on tente d'enregistrer
            with self.assertLogs("controllers.recent_files_store", level="WARNING"):
                store.save(["/tmp/new.ged"], directory, "fr")

            # Then l'ancien fichier est intact et aucun temporaire ne subsiste
            with open(settings_path, encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data["recent_files"], ["old"])
            self.assertEqual(os.listdir(directory), ["settings.json"])

    # Vérifie load reads theme.
    def test_load_reads_theme(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                json.dump({"theme": "dark"}, handle)

            store = RecentFilesStore(settings_path)
            store.load(directory)

            self.assertEqual(store.theme, "dark")

    # Vérifie load falls back when last directory is invalid.
    def test_load_falls_back_when_last_directory_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                json.dump({"last_directory": 42, "recent_files": []}, handle)

            _recent_files, last_directory, _language = RecentFilesStore(
                settings_path
            ).load(directory)

            self.assertEqual(last_directory, directory)

    # Vérifie load ignores non list recent files.
    def test_load_ignores_non_list_recent_files(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {"recent_files": "not-a-list", "last_directory": directory},
                    handle,
                )

            recent_files, last_directory, language = RecentFilesStore(
                settings_path
            ).load(directory)

            self.assertEqual(recent_files, [])
            self.assertEqual(last_directory, directory)
            self.assertIsNone(language)

    # Vérifie load infers last directory from recent file.
    def test_load_infers_last_directory_from_recent_file(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                json.dump({"recent_files": ["/tmp/example.ged"]}, handle)

            _recent_files, last_directory, _language = RecentFilesStore(
                settings_path
            ).load(directory)

            self.assertEqual(last_directory, "/tmp")

    # Vérifie save handles unlink failure.
    def test_save_handles_unlink_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")

            def failing_opener(*args, **kwargs):
                raise OSError("boom")

            store = RecentFilesStore(settings_path, file_opener=failing_opener)
            with patch(
                "controllers.recent_files_store.os.unlink",
                side_effect=OSError("unlink failed"),
            ):
                with self.assertLogs("controllers.recent_files_store", level="WARNING"):
                    store.save(["/tmp/new.ged"], directory, "fr")

    # Vérifie save and load round trip des dernières sélections.
    def test_save_and_load_last_selected_entities(self):
        # Given des sélections d'entité par type
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            store = RecentFilesStore(settings_path)

            store.save(
                ["/tmp/example.ged"],
                "/tmp",
                "fr",
                last_selected_entities={"INDI": "@I1@", "FAM": "@F2@"},
            )
            recent_files, last_directory, language = store.load(directory)

            # Then les sélections sont restaurées
            self.assertEqual(
                store.last_selected_entities, {"INDI": "@I1@", "FAM": "@F2@"}
            )

    # Vérifie load ignore les sélections invalides.
    def test_load_ignores_invalid_last_selected_entities(self):
        # Given un fichier avec des sélections invalides
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with open(settings_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {"last_selected_entities": {"INDI": "@I1@", "FAM": 42, "NOTE": ""}},
                    handle,
                )

            store = RecentFilesStore(settings_path)
            store.load(directory)

            # Then seules les sélections valides sont conservées
            self.assertEqual(store.last_selected_entities, {"INDI": "@I1@"})


if __name__ == "__main__":
    unittest.main()
