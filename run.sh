#!/usr/bin/env bash
set -euo pipefail

# Déterminer le répertoire du script (sécurisé)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Vérifier que main.py existe
if [[ ! -f "main.py" ]]; then
    echo "Erreur : main.py introuvable dans $SCRIPT_DIR"
    exit 1
fi

# Trouver la meilleure commande Python disponible
if [[ -x ".venv/bin/python" ]]; then
    PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "Erreur : Python n'est pas installé."
    exit 1
fi

# Tk startup can stall with Fedora's IBus XIM; preserve an explicit opt-in.
if [[ "${XMODIFIERS:-}" == "@im=ibus" && "${GEDCOM_VIEWER_KEEP_XIM:-0}" != "1" ]]; then
    unset XMODIFIERS
fi

# Lancer l'application
exec "$PYTHON" main.py
