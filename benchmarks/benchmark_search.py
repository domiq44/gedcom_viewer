"""Benchmark du chargement et de la recherche GEDCOM."""

import argparse
import gc
import statistics
import sys
import tempfile
import time
import tracemalloc
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import IO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def percentile(values, pct):
    """Retourne le percentile demandé (interpolation linéaire) d'une liste."""
    ordered = sorted(values)
    if not ordered:
        return 0.0
    rank = (len(ordered) - 1) * (pct / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def peak_rss_bytes():
    """Retourne la mémoire résidente maximale du processus en octets (0 si indispo).

    Lit VmHWM depuis /proc/self/status (high water mark, équivalent au peak RSS).
    """
    try:
        with open("/proc/self/status") as handle:
            for line in handle:
                if line.startswith("VmHWM:"):
                    value_kb = int(line.split()[1])
                    return value_kb * 1024
    except (OSError, ValueError, IndexError):
        pass
    return 0


def threshold_failures(label, load_seconds, search_median_ms, rss_bytes, arguments):
    """Retourne les messages de dépassement de seuils pour un jeu de mesures."""
    failures = []
    if (
        arguments.max_load_seconds is not None
        and load_seconds > arguments.max_load_seconds
    ):
        failures.append(
            f"{label}: chargement {load_seconds:.3f} s > "
            f"{arguments.max_load_seconds:.3f} s"
        )
    if (
        arguments.max_search_median_ms is not None
        and search_median_ms > arguments.max_search_median_ms
    ):
        failures.append(
            f"{label}: recherche médiane {search_median_ms:.2f} ms > "
            f"{arguments.max_search_median_ms:.2f} ms"
        )
    if arguments.max_rss_mib is not None:
        rss_mib = rss_bytes / 1024 / 1024
        if rss_mib > arguments.max_rss_mib:
            failures.append(
                f"{label}: RSS {rss_mib:.1f} MiB > {arguments.max_rss_mib:.1f} MiB"
            )
    return failures


def report_threshold_failures(failures):
    """Affiche les dépassements de seuils et retourne le code de sortie."""
    if not failures:
        return 0
    for failure in failures:
        print(f"Seuil dépassé: {failure}", file=sys.stderr)
    return 1


def normalize_search_text_baseline(value):
    """Normalise une chaîne de recherche avec la méthode de référence."""
    if not isinstance(value, str):
        return ""

    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return without_accents.casefold()


def search_with_normalizer(controller, query, normalize):
    """Recherche les individus avec le normaliseur fourni."""
    normalized_query = normalize(query)
    if not normalized_query:
        return controller.list_individuals()

    return [
        individual
        for individual in controller.individuals.values()
        if (individual.name and normalized_query in normalize(individual.name))
        or (individual.pointer and normalized_query in normalize(individual.pointer))
    ]


def materialize_optional_data(controller):
    """Matérialise les champs optionnels des entités pour mesurer leur coût."""
    for individual in controller.list_individuals():
        individual.notes
        individual.texts
        individual.occupations
        individual.properties
        individual.fams
        individual.obje
        individual.events

    for family in controller.list_families():
        family.marriages
        family.divorces
        family.events

    for source in controller.list_sources():
        source.notes
        source.sources
        source.references
        source.data_events


def benchmark_file(filename, query, repeats):
    """Mesure chargement, mémoire et recherche sur un fichier GEDCOM donné."""
    from controllers.entity_controller import EntityController
    from controllers.gedcom_service import GedcomService
    from controllers.search_controller import SearchController
    from gedcom.parser import GedcomParser

    gc.collect()
    tracemalloc.start()
    load_started_at = time.perf_counter()
    parser = GedcomParser()
    parser.load(filename)
    parser_bytes, _ = tracemalloc.get_traced_memory()
    controller = EntityController(parser)
    service = GedcomService()
    service.parser = parser
    search_controller = SearchController(service, controller)
    load_seconds = time.perf_counter() - load_started_at
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    model_bytes = current_bytes - parser_bytes
    line_count = len(parser.lines)
    record_count = sum(len(entities) for entities in parser.entities.values())

    materialize_optional_data(controller)
    materialized_bytes, _ = tracemalloc.get_traced_memory()
    optional_data_bytes = materialized_bytes - current_bytes
    tracemalloc.stop()

    baseline_times = []
    for _ in range(repeats):
        started_at = time.perf_counter()
        baseline_results = search_with_normalizer(
            controller, query, normalize_search_text_baseline
        )
        baseline_times.append(time.perf_counter() - started_at)

    fast_path_times = []
    for _ in range(repeats):
        started_at = time.perf_counter()
        fast_path_results = search_controller.search_entities("INDI", query)
        fast_path_times.append(time.perf_counter() - started_at)

    baseline_median = statistics.median(baseline_times)
    fast_path_median = statistics.median(fast_path_times)
    baseline_p95 = percentile(baseline_times, 95)
    fast_path_p95 = percentile(fast_path_times, 95)
    rss_bytes = peak_rss_bytes()

    return (
        load_seconds,
        baseline_median,
        fast_path_median,
        parser_bytes,
        model_bytes,
        current_bytes,
        peak_bytes,
        optional_data_bytes,
        len(baseline_results),
        len(fast_path_results),
        line_count,
        record_count,
        len(controller.individuals),
        len(controller.families),
        len(controller.sources),
        baseline_p95,
        fast_path_p95,
        rss_bytes,
    )


@dataclass
class SyntheticGedcom:
    """Paramètres de génération du fichier GEDCOM synthétique."""

    individual_count: int
    texts_per_individual: int
    notes_per_individual: int
    occupations_per_individual: int
    properties_per_individual: int
    fams_per_individual: int
    obje_per_individual: int
    family_count: int
    other_entity_count: int
    events_per_family: int
    events_per_source: int
    metadata_per_source: int


def _write_individual_extras(handle: IO[str], index: int, scenario: SyntheticGedcom):
    """Écrit les lignes optionnelles d'un enregistrement INDI."""
    for text_index in range(scenario.texts_per_individual):
        handle.write(
            f"1 TEXT Synthetic text {text_index} for individual {index}\n"
            f"2 CONT Continued text for individual {index}\n"
        )
    for note_index in range(scenario.notes_per_individual):
        handle.write(
            f"1 NOTE Synthetic note {note_index} for individual {index}\n"
            f"2 CONT Continued note for individual {index}\n"
        )
    for occupation_index in range(scenario.occupations_per_individual):
        handle.write(
            f"1 OCCU Synthetic occupation {occupation_index}\n" "2 DATE 1 JAN 1900\n"
        )
    for property_index in range(scenario.properties_per_individual):
        handle.write(f"1 PROP Synthetic property {property_index}\n")
    for family_reference in range(scenario.fams_per_individual):
        family_index = family_reference % scenario.family_count
        handle.write(f"1 FAMS @F{family_index}@\n")
    for object_reference in range(scenario.obje_per_individual):
        object_index = object_reference % scenario.other_entity_count
        handle.write(f"1 OBJE @O{object_index}@\n")


def _write_individual_records(handle: IO[str], scenario: SyntheticGedcom):
    """Écrit les enregistrements INDI du fichier synthétique."""
    for index in range(scenario.individual_count):
        handle.write(
            f"0 @I{index}@ INDI\n1 NAME Person{index} /Surname{index % 1000}/\n"
        )
        _write_individual_extras(handle, index, scenario)


def _write_family_records(handle: IO[str], scenario: SyntheticGedcom):
    """Écrit les enregistrements FAM du fichier synthétique."""
    for family_index in range(scenario.family_count):
        husband_index = (family_index * 2) % scenario.individual_count
        wife_index = (husband_index + 1) % scenario.individual_count
        handle.write(
            f"0 @F{family_index}@ FAM\n"
            f"1 HUSB @I{husband_index}@\n"
            f"1 WIFE @I{wife_index}@\n"
        )
        handle.write("1 MARR\n" * scenario.events_per_family)


def _write_source_metadata(handle: IO[str], index: int, scenario: SyntheticGedcom):
    """Écrit les métadonnées d'un enregistrement SOUR."""
    for event_index in range(scenario.events_per_source):
        handle.write(
            "1 DATA\n" f"2 EVEN Source event {event_index}\n" "3 DATE 1 JAN 1900\n"
        )
    for metadata_index in range(scenario.metadata_per_source):
        linked_source_index = (index + metadata_index + 1) % scenario.other_entity_count
        handle.write(
            f"1 NOTE Synthetic source note {metadata_index}\n"
            "2 CONT Continued source note\n"
            f"1 SOUR @S{linked_source_index}@\n"
            f"1 REFN Shelf {metadata_index}\n"
        )


def _write_other_records(handle: IO[str], scenario: SyntheticGedcom):
    """Écrit les enregistrements NOTE, SOUR, REPO, SUBM et OBJE."""
    for index in range(scenario.other_entity_count):
        handle.write(f"0 @N{index}@ NOTE Synthetic note {index}\n")
        handle.write(f"0 @S{index}@ SOUR\n1 TITL Synthetic source {index}\n")
        _write_source_metadata(handle, index, scenario)
        handle.write(f"0 @R{index}@ REPO\n1 NAME Archive {index}\n")
        handle.write(f"0 @U{index}@ SUBM\n1 NAME Submitter {index}\n")
        handle.write(
            f"0 @O{index}@ OBJE\n"
            f"1 FILE image-{index}.jpg\n"
            f"1 TITL Family image {index}\n"
        )


def _write_synthetic_gedcom(handle: IO[str], scenario: SyntheticGedcom):
    """Écrit l'intégralité du fichier GEDCOM synthétique."""
    handle.write("0 HEAD\n1 SOUR BENCHMARK\n")
    _write_individual_records(handle, scenario)
    _write_family_records(handle, scenario)
    _write_other_records(handle, scenario)
    handle.write("0 TRLR\n")


def benchmark(
    individual_count,
    texts_per_individual,
    notes_per_individual,
    occupations_per_individual,
    properties_per_individual,
    fams_per_individual,
    obje_per_individual,
    family_count,
    other_entity_count,
    events_per_family,
    events_per_source,
    metadata_per_source,
    query,
    repeats,
):
    """Génère un fichier synthétique et mesure chargement et recherche."""
    scenario = SyntheticGedcom(
        individual_count=individual_count,
        texts_per_individual=texts_per_individual,
        notes_per_individual=notes_per_individual,
        occupations_per_individual=occupations_per_individual,
        properties_per_individual=properties_per_individual,
        fams_per_individual=fams_per_individual,
        obje_per_individual=obje_per_individual,
        family_count=family_count,
        other_entity_count=other_entity_count,
        events_per_family=events_per_family,
        events_per_source=events_per_source,
        metadata_per_source=metadata_per_source,
    )
    with tempfile.NamedTemporaryFile("w", encoding="utf-8") as gedcom_file:
        _write_synthetic_gedcom(gedcom_file, scenario)
        gedcom_file.flush()
        return benchmark_file(gedcom_file.name, query, repeats)


def main():
    """Analyse les arguments et exécute le benchmark demandé."""
    argument_parser = argparse.ArgumentParser(
        description=("Benchmark GEDCOM loading, memory use, and search normalization.")
    )
    argument_parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=(10_000, 50_000, 100_000),
        help="Number of synthetic individuals per run.",
    )
    argument_parser.add_argument(
        "--file",
        help="Measure an existing GEDCOM file; its path and record values are not printed.",
    )
    argument_parser.add_argument(
        "--query",
        default="term-that-does-not-exist",
        help="Search query; the default forces a full scan with no matches.",
    )
    argument_parser.add_argument(
        "--texts-per-individual",
        type=int,
        default=0,
        help="Number of TEXT tags with continuations to add to each individual.",
    )
    argument_parser.add_argument(
        "--occupations-per-individual",
        type=int,
        default=0,
        help="Number of dated OCCU tags to add to each individual.",
    )
    argument_parser.add_argument(
        "--notes-per-individual",
        type=int,
        default=0,
        help="Number of NOTE tags with continuations to add to each individual.",
    )
    argument_parser.add_argument(
        "--properties-per-individual",
        type=int,
        default=0,
        help="Number of PROP tags to add to each individual.",
    )
    argument_parser.add_argument(
        "--fams-per-individual",
        type=int,
        default=0,
        help="Number of FAMS references to add to each individual.",
    )
    argument_parser.add_argument(
        "--obje-per-individual",
        type=int,
        default=0,
        help="Number of OBJE references to add to each individual.",
    )
    argument_parser.add_argument(
        "--families",
        type=int,
        default=0,
        help="Number of synthetic families to include per dataset.",
    )
    argument_parser.add_argument(
        "--events-per-family",
        type=int,
        default=0,
        help="Number of empty MARR events to add to each synthetic family.",
    )
    argument_parser.add_argument(
        "--events-per-source",
        type=int,
        default=0,
        help="Number of DATA/EVEN events to add to each synthetic source.",
    )
    argument_parser.add_argument(
        "--metadata-per-source",
        type=int,
        default=0,
        help="Number of NOTE, SOUR, and REFN entries to add to each source.",
    )
    argument_parser.add_argument(
        "--other-entities",
        type=int,
        default=0,
        help="Number of each NOTE, SOUR, REPO, SUBM, and OBJE record to include.",
    )
    argument_parser.add_argument(
        "--repeats", type=int, default=5, help="Search repetitions per dataset."
    )
    argument_parser.add_argument(
        "--max-load-seconds",
        type=float,
        default=None,
        help="Exit non-zero when the load time exceeds this threshold.",
    )
    argument_parser.add_argument(
        "--max-search-median-ms",
        type=float,
        default=None,
        help="Exit non-zero when the baseline search median exceeds this threshold.",
    )
    argument_parser.add_argument(
        "--max-rss-mib",
        type=float,
        default=None,
        help="Exit non-zero when the peak RSS exceeds this threshold.",
    )
    arguments = argument_parser.parse_args()

    if (
        arguments.repeats < 1
        or arguments.texts_per_individual < 0
        or arguments.notes_per_individual < 0
        or arguments.occupations_per_individual < 0
        or arguments.properties_per_individual < 0
        or arguments.fams_per_individual < 0
        or arguments.obje_per_individual < 0
        or arguments.families < 0
        or arguments.events_per_family < 0
        or arguments.events_per_source < 0
        or arguments.metadata_per_source < 0
        or arguments.other_entities < 0
        or any(size < 1 for size in arguments.sizes)
    ):
        argument_parser.error(
            "sizes and repeats must be positive; optional record counts non-negative"
        )
    if arguments.fams_per_individual and not arguments.families:
        argument_parser.error("--families is required with --fams-per-individual")
    if arguments.obje_per_individual and not arguments.other_entities:
        argument_parser.error("--other-entities is required with --obje-per-individual")
    if arguments.metadata_per_source and not arguments.other_entities:
        argument_parser.error("--other-entities is required with --metadata-per-source")

    thresholds = (
        arguments.max_load_seconds,
        arguments.max_search_median_ms,
        arguments.max_rss_mib,
    )
    if any(value is not None and value < 0 for value in thresholds):
        argument_parser.error("thresholds must be non-negative")

    if arguments.file:
        synthetic_counts = (
            arguments.texts_per_individual,
            arguments.notes_per_individual,
            arguments.occupations_per_individual,
            arguments.properties_per_individual,
            arguments.fams_per_individual,
            arguments.obje_per_individual,
            arguments.families,
            arguments.events_per_family,
            arguments.events_per_source,
            arguments.metadata_per_source,
            arguments.other_entities,
        )
        if any(synthetic_counts):
            argument_parser.error(
                "--file cannot be combined with synthetic data options"
            )
        if not Path(arguments.file).is_file():
            argument_parser.error("--file must refer to an existing GEDCOM file")

        (
            load_seconds,
            baseline_median,
            fast_path_median,
            parser_bytes,
            model_bytes,
            current_bytes,
            peak_bytes,
            optional_data_bytes,
            baseline_matches,
            fast_path_matches,
            line_count,
            record_count,
            individual_count,
            family_count,
            source_count,
            baseline_p95,
            fast_path_p95,
            rss_bytes,
        ) = benchmark_file(arguments.file, arguments.query, arguments.repeats)
        print(
            "Lines | Records | INDI | FAM | SOUR | Load (s) | "
            "Baseline median (ms) | p95 (ms) | ASCII fast median (ms) | p95 (ms) | "
            "Parser (MiB) | Models (+MiB) | Retained (MiB) | Peak (MiB) | "
            "Accessed optional data (MiB) | RSS (MiB) | Matches"
        )
        print(
            f"{line_count:>7} | {record_count:>7} | {individual_count:>4} | "
            f"{family_count:>3} | {source_count:>4} | {load_seconds:>8.3f} | "
            f"{baseline_median * 1000:>17.2f} | "
            f"{baseline_p95 * 1000:>7.2f} | "
            f"{fast_path_median * 1000:>20.2f} | "
            f"{fast_path_p95 * 1000:>7.2f} | "
            f"{parser_bytes / 1024 / 1024:>11.1f} | "
            f"{model_bytes / 1024 / 1024:>13.1f} | "
            f"{current_bytes / 1024 / 1024:>14.1f} | "
            f"{peak_bytes / 1024 / 1024:>10.1f} | "
            f"{optional_data_bytes / 1024 / 1024:>24.1f} | "
            f"{rss_bytes / 1024 / 1024:>10.1f} | "
            f"{baseline_matches}/{fast_path_matches}"
        )
        failures = threshold_failures(
            "fichier",
            load_seconds,
            baseline_median * 1000,
            rss_bytes,
            arguments,
        )
        sys.exit(report_threshold_failures(failures))

    print(
        "Individuals | Texts/individual | Notes/individual | Occu/individual | "
        "Props/individual | FAMS/individual | OBJE/individual | "
        "Families | Events/family | Other each | "
        "Events/source | Metadata/source | Load (s) | "
        "Baseline median (ms) | p95 (ms) | ASCII fast median (ms) | p95 (ms) | "
        "Parser (MiB) | Models (+MiB) | Retained (MiB) | Peak (MiB) | "
        "Accessed optional data (MiB) | RSS (MiB) | Matches"
    )
    failures = []
    for individual_count in arguments.sizes:
        (
            load_seconds,
            baseline_median,
            fast_path_median,
            parser_bytes,
            model_bytes,
            current_bytes,
            peak_bytes,
            optional_data_bytes,
            baseline_matches,
            fast_path_matches,
            _line_count,
            _record_count,
            _individual_count,
            _family_count,
            _source_count,
            baseline_p95,
            fast_path_p95,
            rss_bytes,
        ) = benchmark(
            individual_count,
            arguments.texts_per_individual,
            arguments.notes_per_individual,
            arguments.occupations_per_individual,
            arguments.properties_per_individual,
            arguments.fams_per_individual,
            arguments.obje_per_individual,
            arguments.families,
            arguments.other_entities,
            arguments.events_per_family,
            arguments.events_per_source,
            arguments.metadata_per_source,
            arguments.query,
            arguments.repeats,
        )
        print(
            f"{individual_count:>11} | {arguments.texts_per_individual:>16} | "
            f"{arguments.notes_per_individual:>15} | "
            f"{arguments.occupations_per_individual:>16} | "
            f"{arguments.properties_per_individual:>16} | "
            f"{arguments.fams_per_individual:>15} | "
            f"{arguments.obje_per_individual:>15} | "
            f"{arguments.families:>8} | "
            f"{arguments.events_per_family:>13} | "
            f"{arguments.other_entities:>11} | {arguments.events_per_source:>13} | "
            f"{arguments.metadata_per_source:>15} | "
            f"{load_seconds:>8.3f} | "
            f"{baseline_median * 1000:>17.2f} | "
            f"{baseline_p95 * 1000:>7.2f} | "
            f"{fast_path_median * 1000:>20.2f} | "
            f"{fast_path_p95 * 1000:>7.2f} | "
            f"{parser_bytes / 1024 / 1024:>11.1f} | "
            f"{model_bytes / 1024 / 1024:>13.1f} | "
            f"{current_bytes / 1024 / 1024:>14.1f} | "
            f"{peak_bytes / 1024 / 1024:>10.1f} | "
            f"{optional_data_bytes / 1024 / 1024:>24.1f} | "
            f"{rss_bytes / 1024 / 1024:>10.1f} | "
            f"{baseline_matches}/{fast_path_matches}"
        )
        failures.extend(
            threshold_failures(
                f"{individual_count} individus",
                load_seconds,
                baseline_median * 1000,
                rss_bytes,
                arguments,
            )
        )

    sys.exit(report_threshold_failures(failures))


if __name__ == "__main__":
    main()
