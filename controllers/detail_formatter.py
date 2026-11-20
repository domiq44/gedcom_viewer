"""Formatage des détails d'affichage : fusion des continuations CONT/CONC.

Le module expose aussi :func:`field_parts`, réexporté depuis le domaine, afin
que les vues n'importent jamais `gedcom` directement.
"""

from gedcom.continuations import CONTINUATION_TAGS, append_continuation
from gedcom.models.details import field_parts as field_parts

TEXT_CONTINUATION_TAGS = frozenset({"TEXT", "EVENTEXT", "NOTE"})


def merge_text_continuations(items):
    """Regroupe les continuations CONT/CONC dans le texte TEXT/EVENTEXT/NOTE parent.

    `items` est un itérable de dictionnaires ``{"tag": chemin, "value": valeur}``.
    Les items CONT/CONC sont fusionnés dans le dernier texte parent (repéré par son
    chemin, ou par sa position pour les tags plats). Retourne une nouvelle liste.
    """
    merged: list[dict] = []
    for item in items:
        tag_path = item.get("tag", "")
        tag_parts = tag_path.split("/")
        tag = tag_parts[-1] if tag_parts else ""
        if tag in CONTINUATION_TAGS:
            parent_path = "/".join(tag_parts[:-1])
            parent = None
            if parent_path:
                parent_tag = parent_path.split("/")[-1]
                if parent_tag in TEXT_CONTINUATION_TAGS:
                    parent = next(
                        (
                            candidate
                            for candidate in reversed(merged)
                            if candidate.get("tag") == parent_path
                        ),
                        None,
                    )
            elif merged:
                candidate = merged[-1]
                if candidate.get("tag", "").split("/")[-1] in TEXT_CONTINUATION_TAGS:
                    parent = candidate
            if parent is not None:
                parent["value"] = append_continuation(
                    parent.get("value"), tag, item.get("value")
                )
                continue
        merged.append(dict(item))
    return merged
