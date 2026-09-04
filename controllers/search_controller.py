from controllers.entity_controller import EntityController
import re


class SearchController:
    """Gère les types d'entités, les listes et la recherche côté application."""

    def __init__(
        self, gedcom_service, entity_controller: EntityController, entity_labels=None
    ):
        self.gedcom_service = gedcom_service
        self.entity_controller = entity_controller
        self.entity_labels = entity_labels or {}

    @staticmethod
    def _extract_numeric_id(entity):
        """Extrait le nombre du pointeur GEDCOM d'une entité (e.g., @I123@ → 123)."""
        pointer = getattr(entity, "pointer", None)
        if not pointer:
            pointer = getattr(getattr(entity, "entity", None), "pointer", None)

        if not pointer:
            return (float("inf"), "")  # Mettre à la fin si pas de pointeur valide

        # Trouver le nombre au sein du pointeur (e.g., @I123@ → 123)
        match = re.search(r"(\d+)", pointer)
        if match:
            return (int(match.group(1)), pointer)
        return (float("inf"), pointer)

    @staticmethod
    def _sort_entities(entities):
        """Trie les entités par la partie numérique de leur pointeur."""
        return sorted(entities, key=SearchController._extract_numeric_id)

    def is_loaded(self):
        return (
            self.gedcom_service is not None
            and self.entity_controller is not None
            and self.gedcom_service.is_loaded()
        )

    def get_entity_types(self):
        if not self.is_loaded():
            return []

        return [
            entity_type
            for entity_type in self.entity_labels
            if entity_type in self.gedcom_service.entities
        ]

    def get_entity_type_label(self, entity_type: str):
        return self.entity_labels.get(entity_type, "Type inconnu")

    def get_entity_type_menu_items(self):
        return [
            (entity_type, self.get_entity_type_label(entity_type))
            for entity_type in self.get_entity_types()
        ]

    def get_entity_type_menu_display_items(self):
        return [
            (self.get_entity_type_label(entity_type), entity_type)
            for entity_type in self.get_entity_types()
        ]

    def get_all_entity_type_menu_display_items(self):
        return [
            (self.get_entity_type_label(entity_type), entity_type)
            for entity_type in self.entity_labels
        ]

    def list_entities(self, entity_type: str):
        if not self.is_loaded():
            return []

        if entity_type == "INDI":
            return self.entity_controller.list_individuals()
        if entity_type == "FAM":
            return self.entity_controller.list_families()
        if entity_type == "SOUR":
            return self.entity_controller.list_sources()
        if entity_type == "REPO":
            return self.entity_controller.list_repositories()
        if entity_type == "NOTE":
            return self.entity_controller.list_notes()
        if entity_type == "OBJE":
            return self.entity_controller.list_objects()
        if entity_type == "SUBM":
            return self.entity_controller.list_submitters()

        return self.gedcom_service.entities.get(entity_type, [])

    def search_entities(self, entity_type: str, query: str):
        if not self.is_loaded():
            return []

        if entity_type == "INDI":
            return self.entity_controller.search_individuals(query)
        if entity_type == "SOUR":
            return self.entity_controller.search_sources(query)
        if entity_type == "REPO":
            return self.entity_controller.search_repositories(query)
        if entity_type == "NOTE":
            return self.entity_controller.search_notes(query)
        if entity_type == "OBJE":
            return self.entity_controller.search_objects(query)
        if entity_type == "SUBM":
            return self.entity_controller.search_submitters(query)

        normalized = (query or "").lower()
        if not normalized:
            return self.list_entities(entity_type)

        return [
            entity
            for entity in self.list_entities(entity_type)
            if getattr(entity, "pointer", "") and normalized in entity.pointer.lower()
        ]

    def get_entity_list(self, entity_type: str, query: str = ""):
        if not self.is_loaded():
            return []

        if query:
            entities = self.search_entities(entity_type, query)
        else:
            entities = self.list_entities(entity_type)

        # Trier les entités par la partie numérique du pointeur
        return self._sort_entities(entities)

    def get_entity_list_items(self, entity_type: str, query: str = ""):
        return [
            (entity, self.format_entity_label(entity, entity_type))
            for entity in self.get_entity_list(entity_type, query)
        ]

    @staticmethod
    def _clean_gedcom_name(name):
        if not isinstance(name, str):
            return ""

        cleaned = re.sub(r"\s*/([^/]*)/\s*", r" \1 ", name)
        return " ".join(cleaned.split())

    def format_entity_display_name(self, entity, entity_type: str = None):
        if entity is None:
            return ""

        if entity_type == "INDI":
            name = self._clean_gedcom_name(getattr(entity, "name", ""))
            return name or "Individu sans nom"

        if entity_type == "FAM":
            names = []
            for pointer in (
                getattr(entity, "husband", None),
                getattr(entity, "wife", None),
            ):
                individual = self.entity_controller.get_individual(pointer)
                name = self._clean_gedcom_name(getattr(individual, "name", ""))
                if name:
                    names.append(name)
            if names:
                return " & ".join(names)
            return "Famille sans membres"

        for attribute in ("title", "name", "file"):
            value = getattr(entity, attribute, None)
            if isinstance(value, str) and value.strip():
                return self._clean_gedcom_name(value)

        if entity_type == "NOTE":
            text = getattr(entity, "text", "")
            if isinstance(text, str) and text.strip():
                return " ".join(text.split())[:80]

        return entity_type or "Entité"

    def get_entity_sort_key(self, entity, entity_type: str, column: str):
        if column == "pointer":
            pointer = getattr(entity, "pointer", "") or ""
            numeric_id = self._extract_numeric_id(entity)
            return (numeric_id[0] == float("inf"), numeric_id[0], pointer.casefold())

        if entity_type == "INDI":
            raw_name = getattr(entity, "name", "") or ""
            surname_match = re.search(r"/([^/]*)/", raw_name)
            if surname_match and surname_match.group(1).strip():
                return surname_match.group(1).strip().casefold()
            return self._clean_gedcom_name(raw_name).casefold()

        return self.format_entity_display_name(entity, entity_type).casefold()

    def format_entity_label(self, entity, entity_type: str = None):
        if entity is None:
            return ""

        pointer = getattr(entity, "pointer", None)
        if not pointer and hasattr(entity, "entity"):
            pointer = getattr(entity.entity, "pointer", None)

        if not pointer:
            tag = getattr(entity, "tag", None)
            if tag:
                return f"{tag} (sans pointeur)"
            return "(sans pointeur)"

        # Ajouter des informations spécifiques par type d'entité
        label = pointer

        # INDI : Ajouter le nom et prénom
        if entity_type == "INDI" or (hasattr(entity, "name") and entity_type is None):
            name = getattr(entity, "name", None)
            if name:
                label = f"{pointer} – {name}"

        # FAM : Ajouter les noms du mari et de la femme
        elif entity_type == "FAM" or (
            hasattr(entity, "husband") and entity_type is None
        ):
            husband_name = None
            wife_name = None

            if hasattr(entity, "husband") and entity.husband:
                husband = self.entity_controller.get_individual(entity.husband)
                if husband and hasattr(husband, "name"):
                    husband_name = husband.name

            if hasattr(entity, "wife") and entity.wife:
                wife = self.entity_controller.get_individual(entity.wife)
                if wife and hasattr(wife, "name"):
                    wife_name = wife.name

            if husband_name and wife_name:
                label = f"{pointer} – {husband_name} ∞ {wife_name}"
            elif husband_name:
                label = f"{pointer} – {husband_name}"
            elif wife_name:
                label = f"{pointer} – {wife_name}"

        # SOUR : Ajouter le titre
        elif entity_type == "SOUR" or (
            hasattr(entity, "title") and entity_type is None
        ):
            title = getattr(entity, "title", None)
            if title:
                label = f"{pointer} – {title}"

        # REPO : Ajouter le nom du dépôt
        elif entity_type == "REPO" or (
            hasattr(entity, "name")
            and hasattr(entity, "address")
            and entity_type is None
        ):
            name = getattr(entity, "name", None)
            if name:
                label = f"{pointer} – {name}"

        # SUBM : Ajouter le nom du soumissionnaire
        elif entity_type == "SUBM" or (
            hasattr(entity, "name")
            and hasattr(entity, "address")
            and entity_type is None
        ):
            name = getattr(entity, "name", None)
            if name:
                label = f"{pointer} – {name}"

        # OBJE : Ajouter le titre s'il existe
        elif entity_type == "OBJE" or (hasattr(entity, "file") and entity_type is None):
            file_ref = getattr(entity, "file", None)
            if file_ref:
                label = f"{pointer} – {file_ref}"

        return label
