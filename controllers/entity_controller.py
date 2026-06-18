# controllers/entity_controller.py

from gedcom.models.individual import Individual
from gedcom.models.family import Family


class EntityController:
    """
    Transforme les GedcomEntity brutes en objets métier (Individual, Family, etc.)
    et fournit une API propre pour l'interface utilisateur.
    """

    def __init__(self, parser):
        """
        parser : instance de GedcomParser déjà chargée
        """
        self.parser = parser

        # Dictionnaires d'accès rapide
        self.individuals = {}   # pointer → Individual
        self.families = {}      # pointer → Family (plus tard)

        # Construction des modèles
        self._build_individuals()
        self._build_families()

    # ---------------------------------------------------------
    # INDIVIDUS
    # ---------------------------------------------------------
    def _build_individuals(self):
        """
        Parcourt toutes les entités INDI et instancie des Individual.
        """
        indi_entities = self.parser.entities.get("INDI", [])

        for entity in indi_entities:
            if not entity.pointer:
                continue  # sécurité : un INDI sans pointeur est inutilisable

            person = Individual(entity)
            self.individuals[entity.pointer] = person

    def list_individuals(self):
        """
        Retourne la liste des objets Individual.
        """
        return list(self.individuals.values())

    def get_individual(self, pointer):
        """
        Retourne un individu par son pointeur (@I1@).
        """
        return self.individuals.get(pointer)

    def search_individuals(self, query):
        """
        Recherche simple : filtre sur le nom ou le pointeur.
        """
        query = query.lower()

        return [
            indi for indi in self.individuals.values()
            if (indi.name and query in indi.name.lower())
            or (indi.pointer and query in indi.pointer.lower())
        ]

    # ---------------------------------------------------------
    # FAMILLES (à implémenter plus tard)
    # ---------------------------------------------------------
    def _build_families(self):
        fam_entities = self.parser.entities.get("FAM", [])

        for entity in fam_entities:
            if not entity.pointer:
                continue

            fam = Family(entity)
            self.families[entity.pointer] = fam

        print("==== FAM ENTITY ====")
        print(entity.tag, entity.pointer)
        print(entity.__dict__)


    def list_families(self):
        return list(self.families.values())
