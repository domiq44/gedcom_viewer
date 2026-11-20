"""Vue de détail des dépôts d'archives."""

from ui.views.structured_property_view import StructuredPropertyView

CONTACT_ATTRIBUTES = (
    ("phones", "phone", "view.phone"),
    ("emails", "email", "view.email"),
    ("faxes", "fax", "view.fax"),
    ("websites", "website", "view.website"),
)


class RepositoryPropertyView(StructuredPropertyView):
    """Vue de lecture structurée pour un dépôt GEDCOM."""

    def __init__(
        self,
        parent,
        on_pointer_click,
        translator=None,
        entity_type="REPO",
        tooltip_factory=None,
    ):
        """Initialise la vue des dépôts."""
        super().__init__(
            parent,
            on_pointer_click,
            translator,
            entity_type,
            title_key="view.repository",
            tooltip_factory=tooltip_factory,
        )

    def display(self, repository):
        """Affiche un dépôt."""
        self._clear()
        self.title_label.configure(text=self.translator.get("view.repository"))
        if repository is None:
            return

        self._display_title(repository)
        self._display_identity(repository)
        self._display_labelled_section(
            "view.repository_details", self._detail_fields(repository)
        )
        self._display_labelled_section(
            "view.repository_address", self._address_fields(repository)
        )
        self._display_contact_rows(repository, CONTACT_ATTRIBUTES)
        self._display_pointer_lists(
            repository, (("notes", "view.notes"), ("references", "view.references"))
        )
        self._display_additional_fields(repository)

    def _display_title(self, repository):
        """Affiche le nom du dépôt dans le titre."""
        name = getattr(repository, "name", None)
        self.title_label.configure(text=name or self.translator.get("view.repository"))

    def _detail_fields(self, repository):
        """Retourne les champs de détail du dépôt."""
        return (
            ("view.name", getattr(repository, "name", None)),
            ("view.internal_id", getattr(repository, "record_id", None)),
            ("view.change_date", getattr(repository, "change_date", None)),
            ("view.change_time", getattr(repository, "change_time", None)),
        )

    def _address_fields(self, repository):
        """Retourne les champs d'adresse du dépôt."""
        return (
            ("view.address", getattr(repository, "address", None)),
            ("view.address_line", getattr(repository, "address_line_1", None)),
            ("view.additional_address_2", getattr(repository, "address_line_2", None)),
            ("view.city", getattr(repository, "city", None)),
            ("view.state_country", getattr(repository, "state", None)),
            ("view.postal_code", getattr(repository, "postal_code", None)),
            ("view.country", getattr(repository, "country", None)),
        )
