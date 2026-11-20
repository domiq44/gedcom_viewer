"""Service de chargement et d'exposition des données GEDCOM."""

from controllers.entity_controller import EntityController
from gedcom.parser import GedcomParser


class GedcomService:
    """Service dédié pour charger et exposer les données GEDCOM."""

    def __init__(self):
        """Initialise le service sans fichier chargé."""
        self.parser: GedcomParser | None = None

    def load_file(self, filename: str, strict=False, cancel_event=None):
        """Charge et analyse un fichier GEDCOM."""
        parser = GedcomParser()
        parser.load(filename, strict=strict, cancel_event=cancel_event)
        self.parser = parser

    def reset(self):
        """Décharge le fichier courant."""
        self.parser = None

    def create_entity_controller(self):
        """Crée le contrôleur d'entités si un fichier est chargé."""
        if self.parser is None:
            return None
        return EntityController(self.parser)

    def is_loaded(self):
        """Indique si un fichier est chargé."""
        return self.parser is not None

    @property
    def entities(self):
        """Retourne l'index des entités du fichier."""
        if self.parser is None:
            return {}
        return self.parser.entities

    def get_entity(self, pointer: str):
        """Retourne l'entité correspondant au pointeur."""
        if self.parser is None or not pointer:
            return None
        return self.parser.get_entity(pointer)

    def get_entity_types(self):
        """Retourne les types d'entités présents."""
        if self.parser is None:
            return []
        return list(self.parser.entities.keys())

    def extract_head(self):
        """Retourne le bloc HEAD du fichier."""
        if self.parser is None:
            return ""
        return self.parser.extract_head()

    def extract_trailer(self):
        """Retourne le bloc TRLR du fichier."""
        if self.parser is None:
            return ""
        return self.parser.extract_trailer()
