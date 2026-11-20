"""Génère un fichier GEDCOM synthétique pour les benchmarks."""

import argparse
from pathlib import Path


def build_gedcom(individuals=2000):
    """Construit un GEDCOM contenant des individus et quelques familles."""
    lines = [
        "0 HEAD",
        "1 SOUR BENCHMARK",
        "1 GEDC",
        "2 VERS 5.5.1",
        "2 FORM LINEAGE-LINKED",
        "1 CHAR UTF-8",
        "1 SUBM @U1@",
        "0 @U1@ SUBM",
        "1 NAME Benchmark /Generator/",
    ]
    for index in range(individuals):
        pointer = index + 1
        lines.extend(
            [
                f"0 @I{pointer}@ INDI",
                f"1 NAME John{index} /Doe{index}/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 1 JAN 1900",
                "2 PLAC Paris",
            ]
        )
        if index % 10 == 0:
            family_pointer = index // 10 + 1
            lines.extend(
                [
                    f"0 @F{family_pointer}@ FAM",
                    f"1 HUSB @I{pointer}@",
                ]
            )
    lines.append("0 TRLR")
    return "\n".join(lines) + "\n"


def main(argv=None):
    """Écrit le fichier GEDCOM de benchmark demandé."""
    parser = argparse.ArgumentParser(
        description="Génère un fichier GEDCOM synthétique pour les benchmarks."
    )
    parser.add_argument("--output", required=True, help="Chemin du fichier GEDCOM.")
    parser.add_argument(
        "--individuals",
        type=int,
        default=2000,
        help="Nombre d'individus à générer.",
    )
    args = parser.parse_args(argv)
    Path(args.output).write_text(build_gedcom(args.individuals), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
