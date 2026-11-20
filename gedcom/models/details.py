"""Représentation canonique des champs GEDCOM et de leurs détails."""

FIELD_KEYS = ("tag", "value", "details")


def new_field(tag, value, details=()):
    """Crée un champ canonique {tag, value, details}."""
    return {"tag": tag, "value": value, "details": list(details)}


def field_parts(field):
    """Retourne le tag, la valeur et les détails d'un champ (dict ou tuple)."""
    if isinstance(field, dict):
        return field.get("tag", ""), field.get("value", ""), field.get("details") or []

    values = list(field)
    tag = values[0] if values else ""
    value = values[1] if len(values) > 1 else ""
    details = values[2] if len(values) > 2 else []
    return tag, value, details or []


def field_tag(field):
    """Retourne le tag d'un champ."""
    return field_parts(field)[0]


def field_value(field):
    """Retourne la valeur d'un champ."""
    return field_parts(field)[1]


def field_details(field):
    """Retourne les détails d'un champ."""
    return field_parts(field)[2]
