import json
import os
import tempfile
import unittest

from controllers.recent_files_store import RecentFilesStore


class TestRecentFilesStore(unittest.TestCase):
    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            store = RecentFilesStore(settings_path)

            store.save(["/tmp/example.ged"], "/tmp", "fr")
            recent_files, last_directory, language = store.load(directory)

            self.assertEqual(recent_files, ["/tmp/example.ged"])
            self.assertEqual(last_directory, "/tmp")
            self.assertEqual(language, "fr")

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

    def test_load_missing_settings_returns_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "missing.json")

            result = RecentFilesStore(settings_path).load(directory)

            self.assertEqual(result, ([], directory, None))

    def test_save_limits_recent_files_to_ten(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            recent_files = [f"/tmp/file-{index}.ged" for index in range(12)]

            RecentFilesStore(settings_path).save(recent_files, directory, "en")

            with open(settings_path, encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data["recent_files"], recent_files[:10])


if __name__ == "__main__":
    unittest.main()
