from controllers.entity_controller import EntityController


class PresentationController:
    """Transforme les entités en contexte d'affichage pour l'UI."""

    def __init__(self, gedcom_service, entity_controller: EntityController):
        self.gedcom_service = gedcom_service
        self.entity_controller = entity_controller

    def is_loaded(self):
        return (
            self.gedcom_service is not None
            and self.entity_controller is not None
            and self.gedcom_service.is_loaded()
        )

    def get_entity(self, pointer: str):
        if not self.is_loaded():
            return None
        return self.gedcom_service.get_entity(pointer)

    def get_individual(self, pointer: str):
        if not self.is_loaded():
            return None
        return self.entity_controller.get_individual(pointer)

    def get_family(self, pointer: str):
        if not self.is_loaded():
            return None
        return self.entity_controller.get_family(pointer)

    def get_source(self, pointer: str):
        if not self.is_loaded():
            return None
        return self.entity_controller.get_source(pointer)

    def get_repository(self, pointer: str):
        if not self.is_loaded():
            return None
        return self.entity_controller.get_repository(pointer)

    def get_note(self, pointer: str):
        if not self.is_loaded():
            return None
        return self.entity_controller.get_note(pointer)

    def get_object(self, pointer: str):
        if not self.is_loaded():
            return None
        return self.entity_controller.get_object(pointer)

    def get_submitter(self, pointer: str):
        if not self.is_loaded():
            return None
        return self.entity_controller.get_submitter(pointer)

    def resolve_pointer(self, pointer: str):
        if not self.is_loaded() or not pointer:
            return None

        note = self.get_note(pointer)
        if note:
            return note

        obj = self.get_object(pointer)
        if obj:
            return obj

        submitter = self.get_submitter(pointer)
        if submitter:
            return submitter

        source = self.get_source(pointer)
        if source:
            return source

        repository = self.get_repository(pointer)
        if repository:
            return repository

        individual = self.get_individual(pointer)
        if individual:
            return individual

        family = self.get_family(pointer)
        if family:
            return family

        return self.get_entity(pointer)

    def get_raw_block(self, entity):
        if not self.is_loaded() or entity is None:
            return ""

        if hasattr(entity, "entity") and entity.entity is not None:
            return entity.entity.raw_block()

        if hasattr(entity, "raw_block"):
            return entity.raw_block()

        if hasattr(entity, "entity"):
            inner = getattr(entity, "entity")
            if inner and hasattr(inner, "raw_block"):
                return inner.raw_block()

        return ""

    def get_entity_view_context(self, entity):
        if not self.is_loaded() or entity is None:
            return {"type": "raw", "entity": None, "raw_entity": None}

        if hasattr(entity, "entity") and entity.entity is not None:
            if entity.entity.tag == "INDI":
                return {
                    "type": "individual",
                    "entity": entity,
                    "raw_entity": entity.entity,
                }
            if entity.entity.tag == "FAM":
                return {"type": "family", "entity": entity, "raw_entity": entity.entity}
            if entity.entity.tag == "SOUR":
                return {"type": "source", "entity": entity, "raw_entity": entity.entity}
            if entity.entity.tag == "REPO":
                return {
                    "type": "repository",
                    "entity": entity,
                    "raw_entity": entity.entity,
                }
            if entity.entity.tag == "NOTE":
                return {"type": "note", "entity": entity, "raw_entity": entity.entity}
            if entity.entity.tag == "OBJE":
                return {"type": "object", "entity": entity, "raw_entity": entity.entity}
            if entity.entity.tag == "SUBM":
                return {
                    "type": "submitter",
                    "entity": entity,
                    "raw_entity": entity.entity,
                }
            return {"type": "raw", "entity": entity, "raw_entity": entity.entity}

        if getattr(entity, "tag", None) == "FAM":
            family = self.get_family(getattr(entity, "pointer", None))
            if family:
                return {"type": "family", "entity": family, "raw_entity": family.entity}

        return {"type": "raw", "entity": entity, "raw_entity": entity}

    def get_entity_display_info(self, entity):
        if not self.is_loaded() or entity is None:
            return {"type": "raw", "entity": None, "raw_entity": None, "raw_block": ""}

        context = self.get_entity_view_context(entity)
        raw_entity = context.get("raw_entity")
        context["raw_block"] = self.get_raw_block(raw_entity) if raw_entity else ""
        return context

    def extract_head(self):
        if not self.is_loaded():
            return ""
        return self.gedcom_service.extract_head()

    def extract_trailer(self):
        if not self.is_loaded():
            return ""
        return self.gedcom_service.extract_trailer()
