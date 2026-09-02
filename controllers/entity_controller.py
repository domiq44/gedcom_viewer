from gedcom.models.individual import Individual
from gedcom.models.family import Family
from gedcom.models.source import Source
from gedcom.models.repository import Repository
from gedcom.models.note import Note
from gedcom.models.object import MultimediaObject
from gedcom.models.submitter import Submitter


class EntityController:
    """
    Transforme les GedcomEntity brutes en objets métier (Individual, Family, Source, Repository, Note, MultimediaObject, Submitter)
    et fournit une API propre pour l’interface utilisateur.
    """

    def __init__(self, parser):
        self.parser = parser
        self.individuals = {}
        self.families = {}
        self.sources = {}
        self.repositories = {}
        self.notes = {}
        self.objects = {}
        self.submitters = {}

        self._build_individuals()
        self._build_families()
        self._build_sources()
        self._build_repositories()
        self._build_notes()
        self._build_objects()
        self._build_submitters()

    def _build_individuals(self):
        indi_entities = self.parser.entities.get("INDI", [])
        for entity in indi_entities:
            if not entity.pointer:
                continue
            self.individuals[entity.pointer] = Individual(entity)

    def _build_families(self):
        fam_entities = self.parser.entities.get("FAM", [])
        for entity in fam_entities:
            if not entity.pointer:
                continue
            self.families[entity.pointer] = Family(entity)

    def _build_sources(self):
        source_entities = self.parser.entities.get("SOUR", [])
        for entity in source_entities:
            if not entity.pointer:
                continue
            self.sources[entity.pointer] = Source(entity)

    def _build_repositories(self):
        repo_entities = self.parser.entities.get("REPO", [])
        for entity in repo_entities:
            if not entity.pointer:
                continue
            self.repositories[entity.pointer] = Repository(entity)

    def _build_notes(self):
        note_entities = self.parser.entities.get("NOTE", [])
        for entity in note_entities:
            if not entity.pointer:
                continue
            self.notes[entity.pointer] = Note(entity)

    def _build_objects(self):
        object_entities = self.parser.entities.get("OBJE", [])
        for entity in object_entities:
            if not entity.pointer:
                continue
            self.objects[entity.pointer] = MultimediaObject(entity)

    def _build_submitters(self):
        submitter_entities = self.parser.entities.get("SUBM", [])
        for entity in submitter_entities:
            if not entity.pointer:
                continue
            self.submitters[entity.pointer] = Submitter(entity)

    def list_individuals(self):
        return list(self.individuals.values())

    def list_families(self):
        return list(self.families.values())

    def get_individual(self, pointer):
        return self.individuals.get(pointer)

    def get_family(self, pointer):
        return self.families.get(pointer)

    def get_source(self, pointer):
        return self.sources.get(pointer)

    def get_repository(self, pointer):
        return self.repositories.get(pointer)

    def get_note(self, pointer):
        return self.notes.get(pointer)

    def get_object(self, pointer):
        return self.objects.get(pointer)

    def get_submitter(self, pointer):
        return self.submitters.get(pointer)

    def search_individuals(self, query):
        normalized = (query or "").lower()
        if not normalized:
            return self.list_individuals()

        return [
            indi
            for indi in self.individuals.values()
            if (indi.name and normalized in indi.name.lower())
            or (indi.pointer and normalized in indi.pointer.lower())
        ]

    def list_sources(self):
        return list(self.sources.values())

    def list_repositories(self):
        return list(self.repositories.values())

    def search_sources(self, query):
        normalized = (query or "").lower()
        if not normalized:
            return self.list_sources()

        return [
            source
            for source in self.sources.values()
            if (source.pointer and normalized in source.pointer.lower())
            or (getattr(source, "title", "") and normalized in source.title.lower())
        ]

    def search_repositories(self, query):
        normalized = (query or "").lower()
        if not normalized:
            return self.list_repositories()

        return [
            repo
            for repo in self.repositories.values()
            if (repo.pointer and normalized in repo.pointer.lower())
            or (getattr(repo, "name", "") and normalized in repo.name.lower())
        ]

    def list_notes(self):
        return list(self.notes.values())

    def list_objects(self):
        return list(self.objects.values())

    def list_submitters(self):
        return list(self.submitters.values())

    def search_notes(self, query):
        normalized = (query or "").lower()
        if not normalized:
            return self.list_notes()

        return [
            note
            for note in self.notes.values()
            if (note.pointer and normalized in note.pointer.lower())
            or (getattr(note, "text", "") and normalized in note.text.lower())
        ]

    def search_objects(self, query):
        normalized = (query or "").lower()
        if not normalized:
            return self.list_objects()

        return [
            obj
            for obj in self.objects.values()
            if (obj.pointer and normalized in obj.pointer.lower())
            or (getattr(obj, "title", "") and normalized in obj.title.lower())
            or (getattr(obj, "file", "") and normalized in obj.file.lower())
        ]

    def search_submitters(self, query):
        normalized = (query or "").lower()
        if not normalized:
            return self.list_submitters()

        return [
            submitter
            for submitter in self.submitters.values()
            if (submitter.pointer and normalized in submitter.pointer.lower())
            or (getattr(submitter, "name", "") and normalized in submitter.name.lower())
            or (
                getattr(submitter, "email", "")
                and normalized in submitter.email.lower()
            )
        ]
