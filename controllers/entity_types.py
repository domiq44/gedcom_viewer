"""Correspondances entre tags GEDCOM et types de contexte d’affichage."""

ENTITY_CONTEXT_BY_TYPE = {
    "INDI": "individual",
    "FAM": "family",
    "SOUR": "source",
    "REPO": "repository",
    "NOTE": "note",
    "OBJE": "object",
    "SUBM": "submitter",
    "CITE": "citation",
    "ANCESTOR_TREE": "ANCESTOR_TREE",
}
ENTITY_TYPE_BY_CONTEXT = {
    context_type: entity_type
    for entity_type, context_type in ENTITY_CONTEXT_BY_TYPE.items()
}
