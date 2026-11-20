"""Extraction centralisée des valeurs de tags GEDCOM."""

from gedcom.continuations import CONTINUATION_TAGS, append_continuation


def append_tag_value(values, line_tag, value):
    """Ajoute une continuation CONT/CONC à la dernière valeur collectée."""
    suffix = value or ""
    if not values:
        values.append(suffix)
        return
    values[-1] = append_continuation(values[-1], line_tag, suffix)


def get_tag_values(entity, tag, level=None):
    """Retourne les valeurs d'un tag avec les continuations fusionnées."""
    values = []
    collecting = False
    current_level = None
    last_tag = None

    for line_level, _, line_tag, value in entity.parsed_lines():
        if line_tag is None:
            continue

        if line_tag == tag:
            if level is None or line_level == level:
                collecting = True
                current_level = line_level
                last_tag = tag
                values.append(value or "")
                continue
            if collecting and line_level > current_level:
                last_tag = None
            continue

        if not collecting or current_level is None:
            continue

        if line_tag in CONTINUATION_TAGS:
            if line_level >= current_level and last_tag == tag:
                append_tag_value(values, line_tag, value)
                last_tag = tag
            continue

        if line_level <= current_level:
            collecting = False
            last_tag = None
            continue

        last_tag = line_tag

    return [item for item in values if item is not None]


def get_subtag_values(entity, parent_tag, child_tag):
    """Retourne les valeurs d'un sous-tag avec les continuations fusionnées."""
    values = []
    collecting = False
    parent_level = None
    child_level = None
    last_tag = None

    for level, _, line_tag, value in entity.parsed_lines():
        if line_tag is None:
            continue

        if line_tag == parent_tag and level == 1:
            collecting = True
            parent_level = level
            child_level = None
            last_tag = None
            continue

        if not collecting:
            continue

        if line_tag in CONTINUATION_TAGS:
            if (
                child_level is not None
                and level >= child_level
                and last_tag == child_tag
            ):
                append_tag_value(values, line_tag, value)
                last_tag = child_tag
            continue

        if level <= parent_level:
            collecting = False
            child_level = None
            last_tag = None
            continue

        if (
            line_tag == child_tag
            and parent_level is not None
            and level == parent_level + 1
        ):
            values.append(value or "")
            child_level = level
            last_tag = child_tag
            continue

        last_tag = line_tag

    return [item for item in values if item is not None]


def last_subtag_value(entity, parent_tag, child_tag):
    """Retourne la dernière valeur fusionnée d'un sous-tag, ou None."""
    values = get_subtag_values(entity, parent_tag, child_tag)
    return values[-1] if values else None


class _TagQuery:
    """État de collecte des valeurs d'un tag, aligné sur get_tag_values."""

    __slots__ = ("tag", "level", "values", "collecting", "current_level", "last_tag")

    def __init__(self, tag, level):
        """Initialise la requête pour un tag et un niveau optionnel."""
        self.tag = tag
        self.level = level
        self.values = []
        self.collecting = False
        self.current_level = None
        self.last_tag = None

    def feed(self, line_level, line_tag, value):
        """Met à jour l'état de collecte avec une ligne analysée."""
        tag = self.tag
        if line_tag == tag:
            if self.level is None or line_level == self.level:
                self.collecting = True
                self.current_level = line_level
                self.last_tag = tag
                self.values.append(value or "")
                return
            if self.collecting and line_level > self.current_level:
                self.last_tag = None
            return

        if not self.collecting or self.current_level is None:
            return

        if line_tag in CONTINUATION_TAGS:
            if line_level >= self.current_level and self.last_tag == tag:
                append_tag_value(self.values, line_tag, value)
                self.last_tag = tag
            return

        if line_level <= self.current_level:
            self.collecting = False
            self.last_tag = None
            return

        self.last_tag = line_tag


class _SubtagQuery:
    """État de collecte des sous-tags, aligné sur get_subtag_values."""

    __slots__ = (
        "parent_tag",
        "child_tag",
        "collecting",
        "parent_level",
        "child_level",
        "values",
        "last_tag",
    )

    def __init__(self, parent_tag, child_tag):
        """Initialise la requête pour un couple parent/enfant."""
        self.parent_tag = parent_tag
        self.child_tag = child_tag
        self.collecting = False
        self.parent_level = None
        self.child_level = None
        self.values = []
        self.last_tag = None

    def feed(self, line_level, line_tag, value):
        """Met à jour l'état de collecte avec une ligne analysée."""
        if line_tag == self.parent_tag and line_level == 1:
            self.collecting = True
            self.parent_level = line_level
            self.child_level = None
            self.last_tag = None
            return

        if not self.collecting:
            return

        if line_tag in CONTINUATION_TAGS:
            if (
                self.child_level is not None
                and line_level >= self.child_level
                and self.last_tag == self.child_tag
            ):
                append_tag_value(self.values, line_tag, value)
                self.last_tag = self.child_tag
            return

        if line_level <= self.parent_level:
            self.collecting = False
            self.child_level = None
            self.last_tag = None
            return

        if (
            line_tag == self.child_tag
            and self.parent_level is not None
            and line_level == self.parent_level + 1
        ):
            self.values.append(value or "")
            self.child_level = line_level
            self.last_tag = self.child_tag
            return

        self.last_tag = line_tag


class TagValueCollector:
    """Répond à plusieurs requêtes de valeurs en une seule passe.

    Les requêtes reproduisent exactement la sémantique de :func:`get_tag_values`
    et :func:`get_subtag_values` ; elles évitent de reparcourir les lignes d'une
    entité pour chaque tag.
    """

    def __init__(self, parsed_lines, tags=(), subtags=()):
        """Analyse les lignes et alimente toutes les requêtes demandées."""
        self._tags = {(tag, level): _TagQuery(tag, level) for tag, level in tags}
        self._subtags = {
            (parent, child): _SubtagQuery(parent, child) for parent, child in subtags
        }
        queries: tuple[_TagQuery | _SubtagQuery, ...] = (
            *self._tags.values(),
            *self._subtags.values(),
        )
        for line_level, _, line_tag, value in parsed_lines:
            if line_tag is None:
                continue
            for query in queries:
                query.feed(line_level, line_tag, value)

    def values(self, tag, level=None):
        """Retourne les valeurs collectées pour un tag et un niveau."""
        query = self._tags.get((tag, level))
        return [item for item in query.values if item is not None] if query else []

    def last(self, tag, level=None):
        """Retourne la dernière valeur collectée pour un tag et un niveau."""
        values = self.values(tag, level)
        return values[-1] if values else None

    def subtag_values(self, parent_tag, child_tag):
        """Retourne les valeurs collectées pour un sous-tag."""
        query = self._subtags.get((parent_tag, child_tag))
        return [item for item in query.values if item is not None] if query else []

    def subtag(self, parent_tag, child_tag):
        """Retourne la dernière valeur collectée pour un sous-tag."""
        values = self.subtag_values(parent_tag, child_tag)
        return values[-1] if values else None
