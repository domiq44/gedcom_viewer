"""Configuration des labels des types d'entités GEDCOM."""

ENTITY_LABELS = {
    "INDI": "Individu",
    "FAM": "Famille",
    "OBJE": "Multimédia",
    "NOTE": "Note",
    "SOUR": "Source",
    "SUBM": "Fournisseur d'information",
    "REPO": "Dépôt",
}


def get_default_entity_labels():
    return ENTITY_LABELS.copy()
