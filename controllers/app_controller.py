from controllers.entity_controller import EntityController
from controllers.entity_labels import get_default_entity_labels
from controllers.search_controller import SearchController
from controllers.presentation_controller import PresentationController
from controllers.gedcom_service import GedcomService


class AppController:
    ENTITY_LABELS = get_default_entity_labels()
    """
    Contrôleur principal de l'application.
    """

    def __init__(self, gedcom_service=None):
        self.gedcom_service = gedcom_service or GedcomService()
        self.entity_controller = None
        self.search_controller = None
        self.presentation_controller = None

    def load_file(self, filename: str):
        self.gedcom_service.load_file(filename)
        self._initialize_controllers()

    def _initialize_controllers(self):
        self.entity_controller = self.gedcom_service.create_entity_controller()
        self.search_controller = SearchController(
            self.gedcom_service,
            self.entity_controller,
            entity_labels=self.ENTITY_LABELS,
        )
        self.presentation_controller = PresentationController(
            self.gedcom_service,
            self.entity_controller,
        )

    def is_loaded(self):
        return (
            self.gedcom_service.is_loaded()
            and self.entity_controller is not None
            and self.search_controller is not None
            and self.presentation_controller is not None
        )

    def get_entity_types(self):
        if not self.is_loaded():
            return []
        return self.search_controller.get_entity_types()

    def get_entity_type_label(self, entity_type: str):
        return self.search_controller.get_entity_type_label(entity_type)

    def get_entity_type_menu_items(self):
        return self.search_controller.get_entity_type_menu_items()

    def get_entity_type_menu_display_items(self):
        return self.search_controller.get_entity_type_menu_display_items()

    def list_entities(self, entity_type: str):
        return self.search_controller.list_entities(entity_type)

    def search_entities(self, entity_type: str, query: str):
        return self.search_controller.search_entities(entity_type, query)

    def get_entity_list(self, entity_type: str, query: str = ""):
        return self.search_controller.get_entity_list(entity_type, query)

    def get_entity_list_items(self, entity_type: str, query: str = ""):
        return self.search_controller.get_entity_list_items(entity_type, query)

    def get_entity_display_info(self, entity):
        return self.presentation_controller.get_entity_display_info(entity)

    def get_entity(self, pointer: str):
        if not self.is_loaded():
            return None
        return self.gedcom_service.get_entity(pointer)

    def get_individual(self, pointer: str):
        if not self.is_loaded():
            return None
        return self.entity_controller.get_individual(pointer)

    def format_entity_label(self, entity, entity_type: str = None):
        return self.search_controller.format_entity_label(entity, entity_type)

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

    def get_raw_block(self, entity):
        return self.presentation_controller.get_raw_block(entity)

    def resolve_pointer(self, pointer: str):
        return self.presentation_controller.resolve_pointer(pointer)

    def get_entity_view_context(self, entity):
        return self.presentation_controller.get_entity_view_context(entity)

    def extract_head(self):
        return self.presentation_controller.extract_head()

    def extract_trailer(self):
        return self.presentation_controller.extract_trailer()
