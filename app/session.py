# app/session.py
from gedcom.parser import GedcomParser
from gedcom.models.individual import Individual
from gedcom.models.family import Family

class GedcomSession:
    def __init__(self):
        self.parser = GedcomParser()
        self.individuals = {}
        self.families = {}

    def load(self, filename: str):
        self.parser.load(filename)
        self._build_indexes()

    def _build_indexes(self):
        self.individuals = {}
        self.families = {}

        for e in self.parser.entities.get("INDI", []):
            if getattr(e, "pointer", None):
                self.individuals[e.pointer] = Individual(e)

        for e in self.parser.entities.get("FAM", []):
            if getattr(e, "pointer", None):
                self.families[e.pointer] = Family(e)

    # API utilisée par l'UI
    def list_individuals(self):
        return list(self.individuals.values())

    def search_individuals(self, query: str):
        q = (query or "").lower()
        if not q:
            return self.list_individuals()
        return [
            indi for indi in self.individuals.values()
            if (indi.name and q in indi.name.lower())
            or (indi.pointer and q in indi.pointer.lower())
        ]

    def get_family(self, pointer: str):
        return self.families.get(pointer)

    def extract_head(self):
        return self.parser.extract_head()
