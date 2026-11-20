#!/usr/bin/env python3
"""Smoke-test du binaire PyInstaller produit par `make dist`.

Vérifie que l'artefact existe, est exécutable, puis tente de le lancer
brièvement (sous un affichage virtuel si `xvfb-run` est disponible) et
considère un code de sortie 124 (timeout) comme un succès : cela signifie
que l'application a démarré et tenu la boucle d'événements sans planter.

Code de sortie :
    0  artefact absent et `--require-artifact` absent -> skip
    0  l'application démarre et reste vivante (timeout)
    1  artefact requis absent, non exécutable, ou arrêt anormal
"""

import argparse
import os
import shutil
import subprocess
import sys

DIST_BINARY = os.path.join(
    "dist", "gedcom_viewer.exe" if os.name == "nt" else "gedcom_viewer"
)
STARTUP_TIMEOUT_SECONDS = 8


def parse_args(argv=None):
    """Analyse les arguments du smoke-test."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-artifact",
        action="store_true",
        help="Échoue si l'artefact est absent au lieu de l'ignorer.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=STARTUP_TIMEOUT_SECONDS,
        help="Délai maximal de démarrage en secondes.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Vérifie que l'artefact PyInstaller démarre et tient la boucle d'événements."""
    args = parse_args(argv)

    if not os.path.exists(DIST_BINARY):
        if args.require_artifact:
            print(f"[smoke] {DIST_BINARY} est absent.")
            return 1
        print(f"[smoke] {DIST_BINARY} absent, smoke-test ignoré.")
        return 0

    if not os.path.isfile(DIST_BINARY):
        print(f"[smoke] {DIST_BINARY} n'est pas un fichier.")
        return 1

    if not os.access(DIST_BINARY, os.X_OK):
        print(f"[smoke] {DIST_BINARY} n'est pas exécutable.")
        return 1

    command = [os.path.abspath(DIST_BINARY)]
    if shutil.which("xvfb-run"):
        command = ["xvfb-run", "--auto-servernum", *command]

    env = dict(os.environ)
    env.pop("XMODIFIERS", None)

    print(f"[smoke] Lancement de {' '.join(command)}")
    try:
        completed = subprocess.run(
            command,
            timeout=args.timeout,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.TimeoutExpired as expired:
        output = expired.output or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", "replace")
        print("[smoke] L'application a démarré et tenu la boucle d'événements.")
        if output:
            print(output)
        return 0

    print("[smoke] L'application s'est arrêtée avant le timeout.")
    print(completed.stdout)
    return 1


if __name__ == "__main__":
    sys.exit(main())
