import os


class FileManager:
    """Gestion des fichiers récents et des options d’ouverture de GEDCOM."""

    def __init__(self, root, translator, last_directory=None, recent_files=None):
        self.root = root
        self.translator = translator
        self.last_directory = last_directory or os.path.expanduser("~")
        self.recent_files = list(recent_files or [])

    def file_dialog_options(self):
        initialdir = self.last_directory
        if not initialdir or not os.path.isdir(initialdir):
            initialdir = os.path.expanduser("~")
        return {"initialdir": initialdir}

    def remember_recent_file(self, filename):
        normalized = os.path.abspath(filename)
        if not normalized:
            return

        self.last_directory = os.path.dirname(normalized)
        self.recent_files = [
            path for path in self.recent_files if os.path.abspath(path) != normalized
        ]
        self.recent_files.insert(0, normalized)
        self.recent_files = self.recent_files[:10]
