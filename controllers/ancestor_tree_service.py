"""Service de construction de l'arbre d'ascendance d'un individu."""

from __future__ import annotations

import os
import re
from typing import Any


class AncestorNode:
    """Un nœud de l'arbre d'ascendance avec ses deux parents."""

    def __init__(
        self,
        pointer: str | None,
        name: str,
        birth_date: str = "",
        death_date: str = "",
        marriage_date: str = "",
        sex: str | None = None,
        generation: int = 0,
        photo_path: str = "",
    ):
        """Initialise un nœud d'ancêtre."""
        self.pointer = pointer
        self.name = name or ""
        self.birth_date = birth_date or ""
        self.death_date = death_date or ""
        self.marriage_date = marriage_date or ""
        self.sex = sex
        self.generation = generation
        self.photo_path = photo_path or ""
        self.father: AncestorNode | None = None
        self.mother: AncestorNode | None = None

    @property
    def label(self) -> str:
        """Retourne le libellé affichable (nom + dates)."""
        parts = [AncestorTreeService._clean_name(self.name)]
        if self.birth_date:
            parts.append(f"* {AncestorTreeService._format_date(self.birth_date)}")
        if self.death_date:
            parts.append(f"✝ {AncestorTreeService._format_date(self.death_date)}")
        return " \u2013 ".join(parts)


class AncestorTreeService:
    """Construit l'arbre d'ascendance d'un individu jusqu'à N générations."""

    MAX_GENERATIONS = 50

    def __init__(self, controller: Any, base_path: str | None = None):
        """Initialise le service avec le contrôleur d'application."""
        self.controller = controller
        self.base_path = base_path

    def build_tree(
        self, individual_pointer: str | None, generations: int = MAX_GENERATIONS
    ) -> AncestorNode | None:
        """Construit l'arbre d'ascendance à partir d'un pointeur d'individu."""
        if individual_pointer is None:
            return None
        if generations < 1:
            generations = 1
        if generations > self.MAX_GENERATIONS:
            generations = self.MAX_GENERATIONS
        return self._build_node(individual_pointer, 0, generations)

    @staticmethod
    def _clean_date(value: str | None) -> str:
        """Nettoie une date en retirant les continuations de sous-tags (ex: NOTE).

        Les continuations CONT/CONC de tags imbriqués (comme NOTE sous DATE)
        peuvent fusionner des sauts de ligne dans la valeur collectée. On ne
        garde que la première ligne, qui correspond à la date proprement dite.
        """
        if not value:
            return ""
        return value.split("\n")[0]

    @staticmethod
    def _format_date(value: str | None) -> str:
        """Convertit une date GEDCOM au format YYYY-MM-DD (ou YYYY-MM / YYYY).

        Les dates GEDCOM peuvent être ``15 APR 1950``, ``1950``, ``APR 1950``,
        ``ABT 1950``, ``FROM ... TO ...`` ou ``BET ... AND ...``. Seule la
        première composante date est conservée.
        """
        if not value:
            return ""
        date = value.split("\n")[0].strip()
        if not date:
            return ""

        months = {
            "JAN": "01",
            "FEB": "02",
            "MAR": "03",
            "APR": "04",
            "MAY": "05",
            "JUN": "06",
            "JUL": "07",
            "AUG": "08",
            "SEP": "09",
            "OCT": "10",
            "NOV": "11",
            "DEC": "12",
        }

        return AncestorTreeService._format_date_parts(date.split(), months)

    @staticmethod
    def _format_date_parts(parts: list[str], months: dict[str, str]) -> str:
        """Convertit les parties d'une date en YYYY-MM-DD."""
        start = 0
        while start < len(parts):
            upper = parts[start].upper()
            if upper in ("ABT", "CAL", "EST", "BEF", "AFT", "INT"):
                start += 1
            else:
                break
        if start >= len(parts):
            return ""

        date_tokens = parts[start:]
        date_str = " ".join(date_tokens).split(" TO ")[0].split(" AND ")[0].strip()
        tokens = date_str.split()

        if len(tokens) == 3 and tokens[1].upper() in months:
            year = tokens[2]
            month = months[tokens[1].upper()]
            day = tokens[0].zfill(2)
            return f"{year}-{month}-{day}" if year.isdigit() else ""

        if len(tokens) == 2 and tokens[0].upper() in months:
            year = tokens[1]
            month = months[tokens[0].upper()]
            return f"{year}-{month}" if year.isdigit() else ""

        if len(tokens) == 1:
            token = tokens[0]
            if "-" in token:
                return token
            return token if token.isdigit() else ""

        return ""

    @staticmethod
    def _clean_name(value: str | None) -> str:
        """Nettoie un nom GEDCOM pour l'affichage dans l'arbre.

        Retire les ``/`` autour du nom de famille et les virgules. Si un nom de
        famille est détecté entre ``/``, il est placé en premier suivi d'une
        virgule (ex: ``John /Doe/`` ou ``/Doe/, John`` devient ``Doe, John``).
        """
        if not value:
            return ""
        cleaned = value.replace(",", "")
        parts = re.split(r"/", cleaned)
        if len(parts) >= 3:
            surname = parts[1].strip()
            given = " ".join(p.strip() for p in (parts[0], parts[2]) if p.strip())
            if given:
                return f"{surname}, {given}"
            return f"{surname},"
        return cleaned.strip()

    def _build_node(
        self, pointer: str | None, generation: int, max_generations: int
    ) -> AncestorNode | None:
        """Construit récursivement un nœud et ses ancêtres."""
        if pointer is None or generation >= max_generations:
            return None

        individual = self.controller.get_individual(pointer)
        if individual is None:
            return None

        # À partir de la 5e génération, on n'affiche plus la date
        # de naissance. La date de décès est conservée pour toutes les
        # générations afin d'afficher le témoin de décès le cas échéant.
        show_birth_date = generation < 4

        node = AncestorNode(
            pointer=individual.pointer,
            name=self._clean_name(getattr(individual, "name", None)),
            birth_date=(
                self._format_date(getattr(individual, "birth_date", None))
                if show_birth_date
                else ""
            ),
            death_date=self._format_date(getattr(individual, "death_date", None)),
            marriage_date=self._format_date(getattr(individual, "marriage_date", None)),
            sex=getattr(individual, "sex", None),
            generation=generation,
            photo_path=self._find_photo_path(individual),
        )

        famc_pointer = getattr(individual, "famc", None)
        if famc_pointer:
            family = self.controller.get_family(famc_pointer)
            if family is not None:
                node.marriage_date = self._format_date(
                    getattr(family, "marriage_date", None)
                )
                father_pointer = getattr(family, "husband", None)
                mother_pointer = getattr(family, "wife", None)
                if father_pointer:
                    node.father = self._build_node(
                        father_pointer, generation + 1, max_generations
                    )
                if mother_pointer:
                    node.mother = self._build_node(
                        mother_pointer, generation + 1, max_generations
                    )

        return node

    def _find_photo_path(self, individual: Any) -> str:
        """Retourne le premier chemin de fichier photo trouvé dans les OBJE.

        Les OBJE peuvent être des pointeurs vers des enregistrements OBJE ou des
        chemins de fichier inline. On tente chaque valeur et on retourne la
        première qui ressemble à un fichier image.
        """
        for ref in getattr(individual, "obje", []) or []:
            if not ref or not isinstance(ref, str):
                continue
            candidate = ref.strip()
            if not candidate or candidate == "*":
                continue

            # Si c'est un pointeur OBJE, résoudre l'enregistrement associé
            if candidate.startswith("@") and candidate.endswith("@"):
                multimedia = self.controller.get_object(candidate)
                if multimedia is not None:
                    candidate = getattr(multimedia, "file", None) or ""
                    if not candidate:
                        continue

            candidate = candidate.strip()
            ext = os.path.splitext(candidate)[1].lower()
            if ext in {
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".tif",
                ".tiff",
                ".webp",
            }:
                return candidate
        return ""
