"""Configuration des labels des types d'entités GEDCOM."""

ENTITY_LABELS = {
    "INDI": "Individu",
    "FAM": "Famille",
    "OBJE": "Multimédia",
    "NOTE": "Note",
    "SOUR": "Source",
    "CITE": "Citation",
    "SUBM": "Fournisseur d'information",
    "REPO": "Dépôt",
    "ANCESTOR_TREE": "Arbre d'ascendance",
}


def get_default_entity_labels():
    """Retourne une copie des libellés par défaut des types d'entité."""
    return ENTITY_LABELS.copy()
