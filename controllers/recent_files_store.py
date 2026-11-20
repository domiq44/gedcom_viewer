"""Persistance des fichiers récents et des préférences."""

import json
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


class RecentFilesStore:
    """Magasin persistant des fichiers récents et des préférences."""

    def __init__(self, settings_path, file_opener=open, log=logger):
        """Initialise le magasin avec son chemin de configuration."""
        self.settings_path = os.path.expanduser(settings_path)
        self.file_opener = file_opener
        self.logger = log
        self.window_size = None
        self.view_preferences = {}
        self.last_selected_entities = {}
        self.theme = None

    @staticmethod
    def _parse_window_size(value):
        """Valide et normalise une taille de fenêtre."""
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

    @staticmethod
    def _parse_view_preferences(value):
        """Filtre les préférences de vue valides."""
        if not isinstance(value, dict):
            return {}
        prefs = {}
        for key in ("indent", "show_gedcom_view", "show_entity_view"):
            if type(value.get(key)) is bool:
                prefs[key] = value[key]
        if type(value.get("max_age_for_deceased")) is int:
            prefs["max_age_for_deceased"] = value["max_age_for_deceased"]
        return prefs

    @staticmethod
    def _parse_last_selected_entities(value):
        """Filtre les sélections d'entité valides (type -> pointeur)."""
        if not isinstance(value, dict):
            return {}
        return {
            str(key): str(val)
            for key, val in value.items()
            if isinstance(key, str) and isinstance(val, str) and val
        }

    def load(self, default_directory: str) -> tuple[list[str], str, str | None]:
        """Charge les fichiers récents et les préférences."""
        self.window_size = None
        self.view_preferences = {}
        self.last_selected_entities = {}
        self.theme = None
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
                self.view_preferences = self._parse_view_preferences(
                    data.get("view_preferences")
                )
                self.last_selected_entities = self._parse_last_selected_entities(
                    data.get("last_selected_entities")
                )
                theme = data.get("theme")
                if theme in ("light", "dark"):
                    self.theme = theme
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

    def save(
        self,
        recent_files,
        last_directory,
        language,
        window_size=None,
        view_preferences=None,
        last_selected_entities=None,
        theme=None,
    ):
        """Enregistre les fichiers récents et les préférences de manière atomique."""
        temp_path = None
        try:
            settings = {
                "recent_files": recent_files[:10],
                "last_directory": last_directory,
                "language": language,
            }
            parsed_last_selected = self._parse_last_selected_entities(
                last_selected_entities
            )
            if parsed_last_selected:
                settings["last_selected_entities"] = parsed_last_selected
            if theme in ("light", "dark"):
                settings["theme"] = theme
            parsed_window_size = self._parse_window_size(window_size)
            if parsed_window_size is not None:
                settings["window_size"] = {
                    "width": parsed_window_size[0],
                    "height": parsed_window_size[1],
                }
            parsed_view_preferences = self._parse_view_preferences(view_preferences)
            if parsed_view_preferences:
                settings["view_preferences"] = parsed_view_preferences

            directory = os.path.dirname(os.path.abspath(self.settings_path)) or "."
            file_descriptor, temp_path = tempfile.mkstemp(
                prefix=".gedcom_viewer.", suffix=".tmp", dir=directory
            )
            os.close(file_descriptor)
            with self.file_opener(temp_path, "w", encoding="utf-8") as handle:
                json.dump(settings, handle)
            os.replace(temp_path, self.settings_path)
            temp_path = None
        except Exception as exc:
            self.logger.warning(
                "Impossible d'enregistrer la liste des fichiers récents (%s)",
                type(exc).__name__,
            )
        finally:
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
