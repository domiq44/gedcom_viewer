"""Vue de détail des soumetteurs."""

from ui.views.structured_property_view import StructuredPropertyView

CONTACT_ATTRIBUTES = (
    ("phones", "phone", "view.phone"),
    ("emails", "email", "view.email"),
    ("faxes", "fax", "view.fax"),
    ("websites", "website", "view.website"),
    ("languages", "language", "view.language"),
)


class SubmitterPropertyView(StructuredPropertyView):
    """Vue structurée des coordonnées d’un soumetteur GEDCOM."""

    def __init__(
        self,
        parent,
        on_pointer_click,
        translator=None,
        entity_type="SUBM",
        tooltip_factory=None,
    ):
        """Initialise la vue des soumetteurs."""
        super().__init__(
            parent,
            on_pointer_click,
            translator,
            entity_type,
            title_key="view.submitter",
            tooltip_factory=tooltip_factory,
        )

    def display(self, submitter):
        """Affiche un soumetteur."""
        self._clear()
        self.title_label.configure(text=self.translator.get("view.submitter"))
        if submitter is None:
            return

        self._display_title(submitter)
        self._display_identity(submitter)
        self._display_labelled_section(
            "view.submitter_details", self._detail_fields(submitter)
        )
        self._display_contact_rows(submitter, CONTACT_ATTRIBUTES)
        self._display_additional_fields(submitter)

    def _display_title(self, submitter):
        """Affiche le nom du soumetteur dans le titre."""
        name = getattr(submitter, "name", None)
        self.title_label.configure(text=name or self.translator.get("view.submitter"))

    def _detail_fields(self, submitter):
        """Retourne les champs de détail du soumetteur."""
        return (
            ("view.name", getattr(submitter, "name", None)),
            ("view.address", getattr(submitter, "address", None)),
            ("view.address_line", getattr(submitter, "address_line_1", None)),
            ("view.additional_address_2", getattr(submitter, "address_line_2", None)),
            ("view.city", getattr(submitter, "city", None)),
            ("view.state_country", getattr(submitter, "state", None)),
            ("view.postal_code", getattr(submitter, "postal_code", None)),
            ("view.country", getattr(submitter, "country", None)),
            ("view.registered_number", getattr(submitter, "registered_number", None)),
            ("view.internal_id", getattr(submitter, "record_id", None)),
            ("view.restriction", getattr(submitter, "restriction", None)),
            ("view.change_date", getattr(submitter, "change_date", None)),
            ("view.change_time", getattr(submitter, "change_time", None)),
        )
