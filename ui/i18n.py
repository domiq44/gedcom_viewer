"""Gestion centralisee des textes de l'interface."""

SUPPORTED_LANGUAGES = {
    "fr": "Francais",
}
DEFAULT_LANGUAGE = "fr"

TRANSLATIONS = {
    "fr": {
        "app.title": "GEDCOM Viewer",
        "app.subtitle": "Explorateur de fichiers GEDCOM",
        "ui.search": "Recherche :",
        "ui.entities": "Entités :",
        "ui.name": "Nom",
        "ui.identifier": "Identifiant",
        "ui.history": "Historique : {current}/{total}",
        "ui.log_status": "Dernière erreur log",
        "ui.gedcom": "GEDCOM",
        "ui.raw_content": "Contenu brut du fichier :",
        "ui.entity_view": "Vue de l’entité",
        "ui.ready": "Prêt",
        "ui.loading_last_file": "Chargement du dernier fichier GEDCOM…",
        "ui.no_entity_type": "Aucune entité de ce type",
        "menu.file": "Fichier",
        "menu.help": "Aide",
        "menu.about": "À propos",
        "menu.open": "Ouvrir un fichier GEDCOM",
        "menu.open_validate": "Ouvrir et valider un fichier GEDCOM",
        "menu.recent": "Récents",
        "menu.no_recent": "Aucun fichier récent",
        "menu.clear_recent": "Effacer la liste des fichiers récents",
        "menu.inspect": "Inspecter",
        "menu.header": "Afficher l'en-tête GEDCOM",
        "menu.trailer": "Afficher le bloc TRLR",
        "menu.navigation": "Navigation",
        "menu.previous": "Précédent",
        "menu.next": "Suivant",
        "menu.quit": "Quitter",
        "menu.about_text": "GEDCOM Viewer 5.5.1\nDéveloppé avec Python et Tkinter\n© 2026",
    }
}


class Translator:
    def __init__(self, language=DEFAULT_LANGUAGE):
        self.language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    def set_language(self, language):
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Langue non supportee: {language}")
        self.language = language

    def get(self, key, **values):
        text = TRANSLATIONS.get(self.language, {}).get(key, key)
        return text.format(**values) if values else text
