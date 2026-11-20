"""Formatage des résumés d'entités pour l'affichage."""

from controllers.text_formatting import TextFormatter


class SummaryFormatter:
    """Construit les résumés (titre, sous-titre, faits) pour chaque type d'entité."""

    def __init__(self, text_formatter: TextFormatter):
        """Initialise le formateur de résumés."""
        self.text_formatter = text_formatter

    def format_entity_summary(self, entity_type, entity):
        """Retourne le titre, le sous-titre et les faits d'une entité."""
        if entity is None:
            return {"title": "", "subtitle": "", "facts": []}
        builders = {
            "INDI": self._summary_individual,
            "FAM": self._summary_family,
            "SOUR": self._summary_source,
            "REPO": self._summary_repository,
            "NOTE": self._summary_note,
            "OBJE": self._summary_multimedia,
            "SUBM": self._summary_submitter,
        }
        builder = builders.get(entity_type, self._summary_generic)
        return builder(entity)

    def _summary_individual(self, entity):
        """Retourne le résumé d'un individu."""
        tf = self.text_formatter
        facts = tf._facts(
            (
                ("view.birth_date", entity.birth_date),
                ("view.birth_place", entity.birth_place),
                ("view.death_date", entity.death_date),
                (
                    "view.occupations",
                    [item.get("occupation") for item in entity.occupations],
                ),
            )
        )
        return {
            "title": tf._clean_name(entity.name) or tf._text("entity.unnamed"),
            "subtitle": tf._life_span(entity),
            "facts": facts,
        }

    def _summary_family(self, entity):
        """Retourne le résumé d'une famille."""
        tf = self.text_formatter
        facts = tf._facts(
            (
                ("view.marriage_date", entity.marriage_date),
                ("view.marriage_place", entity.marriage_place),
                ("view.divorce_date", entity.divorce_date),
                ("view.children_count", len(entity.children) or None),
            )
        )
        return {
            "title": tf._text("view.family"),
            "subtitle": tf._pointer(entity),
            "facts": facts,
        }

    def _summary_source(self, entity):
        """Retourne le résumé d'une source."""
        tf = self.text_formatter
        facts = tf._facts(
            (
                ("view.author", entity.author),
                ("view.publication", entity.publication),
                ("view.repository", entity.repository),
                ("view.call_number", entity.call_number),
            )
        )
        return {
            "title": entity.title or tf._text("view.source"),
            "subtitle": entity.abbreviation or tf._pointer(entity),
            "facts": facts,
        }

    def _summary_repository(self, entity):
        """Retourne le résumé d'un dépôt d'archives."""
        tf = self.text_formatter
        facts = tf._facts(
            (
                ("view.address", entity.address),
                ("view.city", entity.city),
                ("view.country", entity.country),
                ("view.website", entity.website),
            )
        )
        return {
            "title": entity.name or tf._text("view.repository"),
            "subtitle": tf._pointer(entity),
            "facts": facts,
        }

    def _summary_note(self, entity):
        """Retourne le résumé d'une note."""
        tf = self.text_formatter
        return {
            "title": tf._text("view.note"),
            "subtitle": tf._pointer(entity),
            "facts": tf._facts((("view.text", tf._first_line(entity.text)),)),
        }

    def _summary_multimedia(self, entity):
        """Retourne le résumé d'un objet multimédia."""
        tf = self.text_formatter
        facts = tf._facts(
            (
                ("view.file", entity.file),
                ("view.format", entity.format),
            )
        )
        return {
            "title": entity.title or tf._text("view.multimedia"),
            "subtitle": tf._pointer(entity),
            "facts": facts,
        }

    def _summary_submitter(self, entity):
        """Retourne le résumé d'un soumissionnaire."""
        tf = self.text_formatter
        facts = tf._facts(
            (
                ("view.email", entity.email),
                ("view.website", entity.website),
                ("view.address", entity.address),
            )
        )
        return {
            "title": entity.name or tf._text("view.submitter"),
            "subtitle": tf._pointer(entity),
            "facts": facts,
        }

    def _summary_generic(self, entity):
        """Retourne un résumé minimal pour un type d'entité non détaillé."""
        tf = self.text_formatter
        return {"title": tf._pointer(entity), "subtitle": "", "facts": []}
