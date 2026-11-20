"""Contrôleur d'accès aux entités GEDCOM et à leurs données."""

import logging
import threading

from gedcom.models.family import Family
from gedcom.models.individual import Individual
from gedcom.models.multimedia import MultimediaObject
from gedcom.models.note import Note
from gedcom.models.repository import Repository
from gedcom.models.source import Source
from gedcom.models.submitter import Submitter

logger = logging.getLogger(__name__)


class EntityController:
    """
    Transforme les GedcomEntity brutes en objets métier (Individual, Family, Source, Repository, Note, MultimediaObject, Submitter)
    et fournit une API propre pour l’interface utilisateur.
    """

    INDEX_SPECS = {
        "individuals": ("INDI", Individual),
        "families": ("FAM", Family),
        "sources": ("SOUR", Source),
        "repositories": ("REPO", Repository),
        "notes": ("NOTE", Note),
        "objects": ("OBJE", MultimediaObject),
        "submitters": ("SUBM", Submitter),
    }

    def __init__(self, parser):
        """Initialise le contrôleur avec des index construits à la demande."""
        self.parser = parser
        self.individuals = {}
        self.families = {}
        self.sources = {}
        self.repositories = {}
        self.notes = {}
        self.objects = {}
        self.submitters = {}
        self._built_indexes = set()
        self._index_lock = threading.Lock()

    def _build_index(self, name):
        """Construit l'index des entités d'un type donné."""
        tag, model = self.INDEX_SPECS[name]
        collection = getattr(self, name)
        for entity in self.parser.entities.get(tag, []):
            if not entity.pointer:
                continue
            try:
                instance = model(entity)
            except Exception:
                logger.exception(
                    "Modèle %s impossible pour l'entité %s",
                    model.__name__,
                    entity.pointer,
                )
                continue
            self._store_first(collection, entity.pointer, instance)

    def _ensure_index(self, name):
        """Construit l'index d'un type d'entité au premier accès."""
        if name in self._built_indexes:
            return
        with self._index_lock:
            if name in self._built_indexes:
                return
            self._build_index(name)
            self._built_indexes.add(name)

    @staticmethod
    def _store_first(collection, pointer, value):
        """Stocke la première valeur pour un pointeur donné."""
        if pointer not in collection:
            collection[pointer] = value

    def list_individuals(self):
        """Retourne la liste des individus."""
        self._ensure_index("individuals")
        return list(self.individuals.values())

    def list_families(self):
        """Retourne la liste des familles."""
        self._ensure_index("families")
        return list(self.families.values())

    def get_individual(self, pointer):
        """Retourne l'individu correspondant au pointeur."""
        self._ensure_index("individuals")
        return self.individuals.get(pointer)

    def get_family(self, pointer):
        """Retourne la famille correspondant au pointeur."""
        self._ensure_index("families")
        return self.families.get(pointer)

    def get_source(self, pointer):
        """Retourne la source correspondant au pointeur."""
        self._ensure_index("sources")
        return self.sources.get(pointer)

    def get_repository(self, pointer):
        """Retourne le dépôt correspondant au pointeur."""
        self._ensure_index("repositories")
        return self.repositories.get(pointer)

    def get_note(self, pointer):
        """Retourne la note correspondant au pointeur."""
        self._ensure_index("notes")
        return self.notes.get(pointer)

    def get_object(self, pointer):
        """Retourne l'objet multimédia correspondant au pointeur."""
        self._ensure_index("objects")
        return self.objects.get(pointer)

    def get_submitter(self, pointer):
        """Retourne le soumetteur correspondant au pointeur."""
        self._ensure_index("submitters")
        return self.submitters.get(pointer)

    def list_sources(self):
        """Retourne la liste des sources."""
        self._ensure_index("sources")
        return list(self.sources.values())

    def list_repositories(self):
        """Retourne la liste des dépôts."""
        self._ensure_index("repositories")
        return list(self.repositories.values())

    def list_notes(self):
        """Retourne la liste des notes."""
        self._ensure_index("notes")
        return list(self.notes.values())

    def list_objects(self):
        """Retourne la liste des objets multimédia."""
        self._ensure_index("objects")
        return list(self.objects.values())

    def list_submitters(self):
        """Retourne la liste des soumetteurs."""
        self._ensure_index("submitters")
        return list(self.submitters.values())
