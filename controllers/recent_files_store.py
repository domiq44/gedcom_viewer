import json
import logging
import os

logger = logging.getLogger(__name__)


class RecentFilesStore:
    def __init__(self, settings_path, file_opener=open, log=logger):
        self.settings_path = os.path.expanduser(settings_path)
        self.file_opener = file_opener
        self.logger = log
        self.window_size = None

    @staticmethod
    def _parse_window_size(value):
        if isinstance(value, dict):
            width = value.get("width")
            height = value.get("height")
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            width, height = value
        else:
            return None

        if type(width) is int and type(height) is int and width > 0 and height > 0:
            return width, height
        return None

    def load(self, default_directory):
        self.window_size = None
        if not os.path.isfile(self.settings_path):
            return [], default_directory, None

        try:
            with self.file_opener(self.settings_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)

            language = None
            last_directory = default_directory
            if isinstance(data, dict):
                language = data.get("language")
                last_directory = data.get("last_directory", default_directory)
                self.window_size = self._parse_window_size(data.get("window_size"))
                data = data.get("recent_files", [])

            if not isinstance(last_directory, str) or not os.path.isdir(last_directory):
                last_directory = default_directory
            if not isinstance(data, list):
                return [], last_directory, language

            recent_files = [path for path in data if isinstance(path, str)]
            if last_directory == default_directory:
                for path in recent_files:
                    directory = os.path.dirname(os.path.abspath(path))
                    if os.path.isdir(directory):
                        last_directory = directory
                        break
            return recent_files, last_directory, language
        except Exception as exc:
            self.logger.warning(
                "Impossible de lire la liste des fichiers récents (%s)",
                type(exc).__name__,
            )
            return [], default_directory, None

    def save(self, recent_files, last_directory, language, window_size=None):
        try:
            settings = {
                "recent_files": recent_files[:10],
                "last_directory": last_directory,
                "language": language,
            }
            parsed_window_size = self._parse_window_size(window_size)
            if parsed_window_size is not None:
                settings["window_size"] = {
                    "width": parsed_window_size[0],
                    "height": parsed_window_size[1],
                }

            with self.file_opener(self.settings_path, "w", encoding="utf-8") as handle:
                json.dump(settings, handle)
        except Exception as exc:
            self.logger.warning(
                "Impossible d'enregistrer la liste des fichiers récents (%s)",
                type(exc).__name__,
            )
