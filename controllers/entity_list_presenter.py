"""Présentation des listes d'entités pour l'interface."""

import re


class EntityListPresenter:
    """Formate les entités pour la liste et fournit leurs clés de tri."""

    def __init__(self, entity_controller, translator=None):
        """Initialise le présentateur avec son contrôleur et son traducteur."""
        self.entity_controller = entity_controller
        self.translator = translator

    def _translate(self, key, fallback):
        """Retourne la traduction d'une clé ou le libellé de repli."""
        if self.translator is not None:
            return self.translator.get(key)
        return fallback

    @staticmethod
    def extract_numeric_id(entity):
        """Extrait l'identifiant numérique et le pointeur d'une entité."""
        pointer = getattr(entity, "pointer", None)
        if not pointer:
            pointer = getattr(getattr(entity, "entity", None), "pointer", None)

        if not pointer:
            return float("inf"), ""

        match = re.search(r"(\d+)", pointer)
        if match:
            return int(match.group(1)), pointer
        return float("inf"), pointer

    @classmethod
    def sort_entities(cls, entities):
        """Trie les entités par identifiant numérique."""
        return sorted(entities, key=cls.extract_numeric_id)

    @staticmethod
    def clean_gedcom_name(name):
        """Nettoie un nom GEDCOM (séparateurs /)."""
        if not isinstance(name, str):
            return ""
        cleaned = re.sub(r"\s*/([^/]*)/\s*", r" \1 ", name)
        return " ".join(cleaned.split())

    @classmethod
    def format_individual_name(cls, name):
        """Formate un nom d'individu en « Nom, Prénom »."""
        if not isinstance(name, str):
            return ""

        surname_match = re.search(r"/([^/]*)/", name)
        if not surname_match:
            surname = ""
            given_name = cls.clean_gedcom_name(name)
        else:
            surname = surname_match.group(1).strip()
            given_name = cls.clean_gedcom_name(
                name[: surname_match.start()] + name[surname_match.end() :]
            )

        if surname and given_name:
            return f"{surname}, {given_name}"
        if surname:
            return f"{surname},"
        return given_name

    def format_display_name(self, entity, entity_type=None):
        """Retourne le nom d'affichage d'une entité selon son type."""
        if entity is None:
            return ""

        if entity_type == "CITE":
            return self._citation_label(entity)

        if entity_type == "INDI":
            name = self.format_individual_name(getattr(entity, "name", ""))
            return name or ","

        if entity_type == "FAM":
            return self._family_label(entity)

        return self._generic_label(entity, entity_type)

    def _citation_label(self, citation):
        """Retourne le libellé d'une citation."""
        source = (
            self.entity_controller.get_source(citation.source_pointer)
            if self.entity_controller is not None
            else None
        )
        source_title = (
            getattr(source, "title", None) or citation.source_pointer
            if source is not None
            else citation.source_pointer
        )
        owner = self._citation_owner(citation)
        owner_name = self.format_display_name(owner, citation.owner_type)
        owner_name = owner_name or citation.owner_pointer
        details = [owner_name]
        if citation.context_tag:
            details.append(citation.context_tag)
        if citation.page:
            details.append(f"p. {citation.page}")
        return f"{source_title} — {' · '.join(details)}"

    def _family_label(self, family):
        """Retourne le libellé d'une famille."""
        names = []
        for pointer in (
            getattr(family, "husband", None),
            getattr(family, "wife", None),
        ):
            individual = (
                self.entity_controller.get_individual(pointer)
                if self.entity_controller is not None
                else None
            )
            name = self.format_individual_name(getattr(individual, "name", ""))
            if name:
                names.append(name)
        if names:
            return " & ".join(names)
        return self._translate(
            "entity.family_without_members", "Family without members"
        )

    def _generic_label(self, entity, entity_type):
        """Retourne le libellé générique d'une entité."""
        for attribute in ("title", "name", "file"):
            value = getattr(entity, attribute, None)
            if isinstance(value, str) and value.strip():
                return value.strip()

        if entity_type == "NOTE":
            text = getattr(entity, "text", "")
            if isinstance(text, str) and text.strip():
                return " ".join(text.split())[:80]

        return entity_type or self._translate("entity.unnamed", "Entity")

    LABEL_FIELDS = {"NAMED": "name", "SOUR": "title", "OBJE": "file"}

    def format_label(self, entity, entity_type=None):
        """Retourne le libellé d'une entité pour la liste."""
        if entity is None:
            return ""

        pointer = self._pointer(entity)
        if not pointer:
            return self._label_without_pointer(entity)

        if entity_type == "CITE":
            return self.format_display_name(entity, entity_type)

        suffix = self._label_suffix(entity, entity_type)
        return f"{pointer} – {suffix}" if suffix else pointer

    def _label_suffix(self, entity, entity_type):
        """Retourne le suffixe du libellé selon la catégorie de l'entité."""
        kind = self._label_kind(entity, entity_type)
        if kind == "INDI":
            return self.format_individual_name(getattr(entity, "name", None))
        if kind == "FAM":
            return self.format_display_name(entity, "FAM")

        field = self.LABEL_FIELDS.get(kind)
        if field is None:
            return ""
        value = getattr(entity, field, None)
        return value if isinstance(value, str) and value.strip() else ""

    @staticmethod
    def _label_kind(entity, entity_type):
        """Déduit la catégorie d'étiquetage d'une entité."""
        if entity_type == "INDI" or (
            getattr(getattr(entity, "entity", None), "tag", None) == "INDI"
        ):
            return "INDI"
        if entity_type == "FAM" or (entity_type is None and hasattr(entity, "husband")):
            return "FAM"
        if entity_type == "SOUR" or (entity_type is None and hasattr(entity, "title")):
            return "SOUR"
        if entity_type in {"REPO", "SUBM"} or (
            entity_type is None
            and hasattr(entity, "name")
            and hasattr(entity, "address")
        ):
            return "NAMED"
        if entity_type == "OBJE" or (entity_type is None and hasattr(entity, "file")):
            return "OBJE"
        if entity_type is None and hasattr(entity, "name"):
            return "NAMED"
        return None

    @staticmethod
    def _pointer(entity):
        """Retourne le pointeur d'une entité, y compris encapsulée."""
        pointer = getattr(entity, "pointer", None)
        if not pointer and hasattr(entity, "entity"):
            pointer = getattr(entity.entity, "pointer", None)
        return pointer

    def _label_without_pointer(self, entity):
        """Retourne le libellé d'une entité sans pointeur."""
        tag = getattr(entity, "tag", None)
        label = self._translate("entity.without_pointer", "(no pointer)")
        return f"{tag} {label}" if tag else label

    def sort_key(self, entity, entity_type, column):
        """Retourne la clé de tri d'une entité pour une colonne."""
        if column == "pointer":
            pointer = getattr(entity, "pointer", "") or ""
            numeric_id = self.extract_numeric_id(entity)
            return numeric_id[0] == float("inf"), numeric_id[0], pointer.casefold()

        if entity_type == "INDI":
            raw_name = getattr(entity, "name", "") or ""
            surname_match = re.search(r"/([^/]*)/", raw_name)
            if surname_match and surname_match.group(1).strip():
                return surname_match.group(1).strip().casefold()
            return self.clean_gedcom_name(raw_name).casefold()

        return self.format_display_name(entity, entity_type).casefold()

    def _citation_owner(self, citation):
        """Retourne l'entité propriétaire d'une citation."""
        if self.entity_controller is None:
            return None
        resolvers = {
            "INDI": self.entity_controller.get_individual,
            "FAM": self.entity_controller.get_family,
            "SOUR": self.entity_controller.get_source,
            "REPO": self.entity_controller.get_repository,
            "NOTE": self.entity_controller.get_note,
            "OBJE": self.entity_controller.get_object,
            "SUBM": self.entity_controller.get_submitter,
        }
        resolver = resolvers.get(citation.owner_type)
        return resolver(citation.owner_pointer) if resolver else None
