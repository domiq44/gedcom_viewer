import argparse
import gc
import sys
import tempfile
import time
import tracemalloc
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllers.entity_controller import EntityController
from gedcom.parser import GedcomParser


def normalize_search_text_baseline(value):
    if not isinstance(value, str):
        return ""

    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return without_accents.casefold()


def search_with_normalizer(controller, query, normalize):
    normalized_query = normalize(query)
    if not normalized_query:
        return controller.list_individuals()

    return [
        individual
        for individual in controller.individuals.values()
        if (individual.name and normalized_query in normalize(individual.name))
        or (individual.pointer and normalized_query in normalize(individual.pointer))
    ]


def benchmark(
    individual_count,
    texts_per_individual,
    family_count,
    other_entity_count,
    events_per_family,
    events_per_source,
    query,
    repeats,
):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8") as gedcom_file:
        gedcom_file.write("0 HEAD\n1 SOUR BENCHMARK\n")
        for index in range(individual_count):
            gedcom_file.write(
                f"0 @I{index}@ INDI\n1 NAME Person{index} /Surname{index % 1000}/\n"
            )
            for text_index in range(texts_per_individual):
                gedcom_file.write(
                    f"1 TEXT Synthetic text {text_index} for individual {index}\n"
                    f"2 CONT Continued text for individual {index}\n"
                )
        for family_index in range(family_count):
            husband_index = (family_index * 2) % individual_count
            wife_index = (husband_index + 1) % individual_count
            gedcom_file.write(
                f"0 @F{family_index}@ FAM\n"
                f"1 HUSB @I{husband_index}@\n"
                f"1 WIFE @I{wife_index}@\n"
            )
            gedcom_file.write("1 MARR\n" * events_per_family)

        for index in range(other_entity_count):
            gedcom_file.write(f"0 @N{index}@ NOTE Synthetic note {index}\n")
            gedcom_file.write(f"0 @S{index}@ SOUR\n1 TITL Synthetic source {index}\n")
            for event_index in range(events_per_source):
                gedcom_file.write(
                    "1 DATA\n"
                    f"2 EVEN Source event {event_index}\n"
                    "3 DATE 1 JAN 1900\n"
                )
            gedcom_file.write(f"0 @R{index}@ REPO\n1 NAME Archive {index}\n")
            gedcom_file.write(f"0 @U{index}@ SUBM\n1 NAME Submitter {index}\n")
            gedcom_file.write(
                f"0 @O{index}@ OBJE\n"
                f"1 FILE image-{index}.jpg\n"
                f"1 TITL Family image {index}\n"
            )
        gedcom_file.write("0 TRLR\n")
        gedcom_file.flush()

        gc.collect()
        tracemalloc.start()
        load_started_at = time.perf_counter()
        parser = GedcomParser()
        parser.load(gedcom_file.name)
        controller = EntityController(parser)
        load_seconds = time.perf_counter() - load_started_at
        current_bytes, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        search_started_at = time.perf_counter()
        for _ in range(repeats):
            baseline_results = search_with_normalizer(
                controller, query, normalize_search_text_baseline
            )
        baseline_search_seconds = (time.perf_counter() - search_started_at) / repeats

        search_started_at = time.perf_counter()
        for _ in range(repeats):
            fast_path_results = controller.search_individuals(query)
        fast_path_search_seconds = (time.perf_counter() - search_started_at) / repeats

    return (
        load_seconds,
        baseline_search_seconds,
        fast_path_search_seconds,
        current_bytes,
        peak_bytes,
        len(baseline_results),
        len(fast_path_results),
    )


def main():
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
        "--other-entities",
        type=int,
        default=0,
        help="Number of each NOTE, SOUR, REPO, SUBM, and OBJE record to include.",
    )
    argument_parser.add_argument(
        "--repeats", type=int, default=5, help="Search repetitions per dataset."
    )
    arguments = argument_parser.parse_args()

    if (
        arguments.repeats < 1
        or arguments.texts_per_individual < 0
        or arguments.families < 0
        or arguments.events_per_family < 0
        or arguments.events_per_source < 0
        or arguments.other_entities < 0
        or any(size < 1 for size in arguments.sizes)
    ):
        argument_parser.error(
            "sizes and repeats must be positive; optional record counts non-negative"
        )

    print(
        "Individuals | Texts/individual | Families | Events/family | Other each | "
        "Events/source | Load (s) | "
        "Baseline (ms) | ASCII fast path (ms) | "
        "Retained (MiB) | Peak (MiB) | Matches"
    )
    for individual_count in arguments.sizes:
        (
            load_seconds,
            baseline_search_seconds,
            fast_path_search_seconds,
            current_bytes,
            peak_bytes,
            baseline_matches,
            fast_path_matches,
        ) = benchmark(
            individual_count,
            arguments.texts_per_individual,
            arguments.families,
            arguments.other_entities,
            arguments.events_per_family,
            arguments.events_per_source,
            arguments.query,
            arguments.repeats,
        )
        print(
            f"{individual_count:>11} | {arguments.texts_per_individual:>16} | "
            f"{arguments.families:>8} | "
            f"{arguments.events_per_family:>13} | "
            f"{arguments.other_entities:>11} | {arguments.events_per_source:>13} | "
            f"{load_seconds:>8.3f} | "
            f"{baseline_search_seconds * 1000:>12.2f} | "
            f"{fast_path_search_seconds * 1000:>19.2f} | "
            f"{current_bytes / 1024 / 1024:>14.1f} | "
            f"{peak_bytes / 1024 / 1024:>10.1f} | "
            f"{baseline_matches}/{fast_path_matches}"
        )


if __name__ == "__main__":
    main()
