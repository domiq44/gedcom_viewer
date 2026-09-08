from controllers.entity_controller import EntityController
from gedcom.parser import GedcomParser


class GedcomService:
    """Service dédié pour charger et exposer les données GEDCOM."""

    def __init__(self):
        self.parser = None

    def load_file(self, filename: str, strict=False):
        parser = GedcomParser()
        parser.load(filename, strict=strict)
        self.parser = parser

    def create_entity_controller(self):
        if not self.is_loaded():
            return None
        return EntityController(self.parser)

    def is_loaded(self):
        return self.parser is not None

    @property
    def entities(self):
        if not self.is_loaded():
            return {}
        return self.parser.entities

    def get_entity(self, pointer: str):
        if not self.is_loaded() or not pointer:
            return None
        return self.parser.get_entity(pointer)

    def get_entities_by_type(self, entity_type: str):
        if not self.is_loaded() or not entity_type:
            return []
        return self.parser.entities.get(entity_type, [])

    def get_entity_types(self):
        if not self.is_loaded():
            return []
        return list(self.parser.entities.keys())

    def extract_head(self):
        if not self.is_loaded():
            return ""
        return self.parser.extract_head()

    def extract_trailer(self):
        if not self.is_loaded():
            return ""
        return self.parser.extract_trailer()
