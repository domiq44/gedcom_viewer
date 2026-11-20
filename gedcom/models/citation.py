"""Modèle d'une citation (CITE)."""

from dataclasses import dataclass, field

from gedcom.continuations import CONTINUATION_TAGS, append_continuation
from gedcom.line_parser import parse_line


@dataclass(slots=True)
class Citation:
    """Citation d'une source attachée à une entité."""

    source_pointer: str
    owner_pointer: str
    owner_type: str
    level: int
    context_tag: str = ""
    page: str = ""
    gedcom_lines: list[str] = field(default_factory=list, repr=False)
    _details: list[dict[str, object]] | None = field(
        default=None, init=False, repr=False, compare=False
    )

    @property
    def pointer(self):
        """Retourne le pointeur de la source citée."""
        return self.source_pointer

    @property
    def raw_block(self):
        """Retourne le bloc GEDCOM brut de la citation."""
        return "".join(self.gedcom_lines)

    @property
    def details(self):
        """Retourne les champs de détail de la citation."""
        if self._details is None:
            self._details = self._build_details()
        return self._details

    def _build_details(self):
        """Construit les champs de détail de la citation."""
        fields: list[dict[str, object]] = []
        path_by_level: dict[int, str] = {}

        for raw in self.gedcom_lines:
            level, _pointer, tag, value = parse_line(raw)
            if level is None or level <= self.level:
                continue

            relative_level = level - self.level
            path_by_level = {
                depth: path_tag
                for depth, path_tag in path_by_level.items()
                if depth < relative_level
            }

            if tag in CONTINUATION_TAGS:
                parent_path = "/".join(
                    path_by_level[depth]
                    for depth in sorted(path_by_level)
                    if depth < relative_level
                )
                parent = next(
                    (
                        field
                        for field in reversed(fields)
                        if field["tag"] == parent_path
                    ),
                    None,
                )
                if parent is not None:
                    parent["value"] = append_continuation(
                        parent["value"], tag, value or ""
                    )
                    continue

            path_by_level[relative_level] = tag
            tag_path = "/".join(
                path_by_level[depth]
                for depth in sorted(path_by_level)
                if depth <= relative_level
            )
            fields.append(
                {
                    "tag": tag_path,
                    "value": value or "",
                    "level": relative_level,
                }
            )

        return fields
