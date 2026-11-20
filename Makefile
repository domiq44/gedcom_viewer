PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
APP_NAME ?= gedcom_viewer
CRITICAL_COVERAGE_MODULES ?= gedcom/parser.py,gedcom/validator.py,gedcom/continuations.py,controllers/entity_controller.py,controllers/citation_controller.py,controllers/search_controller.py,controllers/presentation_controller.py,controllers/app_controller.py,ui/load_coordinator.py

.PHONY: help install run test format lint typecheck sanitize coverage smoke dist clean check_python check_pip check_tk venv

help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  venv        Create the virtual environment (.venv)"
	@echo "  install     Install pip, Tkinter (system check), Pillow, PDFium, PyInstaller, Black, ruff, coverage and mypy"
	@echo "  run         Create the venv if needed and launch the application locally"
	@echo "  test        Run the Python unit tests"
	@echo "  format      Format Python sources with Black"
	@echo "  lint        Check sources with ruff, black --check, syntax compilation and conformance (locales, docstrings, comments)"
	@echo "  typecheck   Run mypy on gedcom, controllers and ui"
	@echo "  sanitize    Run all checks: lint + typecheck + tests"
	@echo "  coverage    Run tests under coverage and report"
	@echo "  smoke       Smoke-test the PyInstaller artefact (after make dist)"
	@echo "  dist        Build a standalone executable with PyInstaller"
	@echo "  clean       Remove build artifacts, venv, caches and coverage"

# --- Gestion de l'environnement ---

venv:
	@if [ ! -d .venv ]; then \
		echo "Creating virtual environment (.venv)..."; \
		python3 -m venv .venv; \
	else \
		echo ".venv already exists."; \
	fi

# Assurez-vous que PYTHON pointe vers le bon exécutable après venv
# On réévalue PYTHON pour s'assurer qu'il pointe vers .venv/bin/python
PYTHON_ACTUAL = $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

# --- Vérifications ---

check_pip:
	@echo "Checking pip..."
	@if ! $(PYTHON_ACTUAL) -m pip >/dev/null 2>&1; then \
		echo "pip not found. Attempting installation..."; \
		$(PYTHON_ACTUAL) -m ensurepip --upgrade || echo "Failed to install pip. Install it manually."; \
	else \
		echo "pip is installed."; \
	fi

check_python:
	@echo "Checking Python version..."
	@$(PYTHON_ACTUAL) -c "import sys; sys.exit('Python 3.11 or newer is required') if sys.version_info < (3, 11) else None"

check_tk:
	@echo "Checking Tkinter..."
	@if ! $(PYTHON_ACTUAL) -c "import tkinter" >/dev/null 2>&1; then \
		echo "Tkinter is not installed."; \
		echo "Install it with your system package manager:"; \
		echo "  Debian/Ubuntu: sudo apt install python3-tk"; \
		echo "  Fedora: sudo dnf install python3-tkinter"; \
		echo "  Arch: sudo pacman -S tk"; \
		echo "  macOS: Tkinter is included with python.org installers"; \
		exit 1; \
	else \
		echo "Tkinter is installed."; \
	fi

# --- Installation ---

install: venv check_pip check_python check_tk
	@echo "Installing project dependencies..."
	$(PYTHON_ACTUAL) -m pip install -r requirements-dev.txt

# --- Exécution et Test ---

run: venv install
	@echo "--- Running application ---"
	./run.sh

test: venv install
	@echo "--- Running tests ---"
	@if [ "$${XMODIFIERS:-}" = "@im=ibus" ] && [ "$${GEDCOM_VIEWER_KEEP_XIM:-0}" != "1" ]; then \
		env -u XMODIFIERS $(PYTHON_ACTUAL) -m unittest discover -s tests -t .; \
	else \
		$(PYTHON_ACTUAL) -m unittest discover -s tests -t .; \
	fi

# --- Formatage et Linting ---

format: install
	@echo "--- Formatting sources with Black ---"
	$(PYTHON_ACTUAL) -m black .

lint:
	@echo "--- Linting sources with ruff ---"
	$(PYTHON_ACTUAL) -m ruff check .
	@echo "--- Checking formatting with Black ---"
	$(PYTHON_ACTUAL) -m black --check main.py controllers gedcom ui tests benchmarks scripts
	@echo "--- Checking syntax ---"
	$(PYTHON_ACTUAL) -m compileall -q gedcom controllers ui tests benchmarks scripts main.py
	@echo "--- Checking locale completeness ---"
	$(PYTHON_ACTUAL) -m unittest tests.test_locale_keys
	@echo "--- Checking docstrings and test comments ---"
	$(PYTHON_ACTUAL) -m unittest tests.test_docstrings tests.test_test_comments

# --- Validation complète ---

sanitize: lint typecheck test

# --- Typage ---

typecheck:
	@echo "--- Type-checking production, entry point, benchmarks and scripts with mypy ---"
	$(PYTHON_ACTUAL) -m mypy

# --- Couverture ---

coverage:
	@echo "--- Running tests under coverage ---"
	@if [ "$${XMODIFIERS:-}" = "@im=ibus" ] && [ "$${GEDCOM_VIEWER_KEEP_XIM:-0}" != "1" ]; then \
		env -u XMODIFIERS $(PYTHON_ACTUAL) -m coverage run -m unittest discover -s tests -t .; \
	else \
		$(PYTHON_ACTUAL) -m coverage run -m unittest discover -s tests -t .; \
	fi
	@echo ""
	@echo "=== Rapport de couverture (modules les moins couverts en premier) ==="
	@$(PYTHON_ACTUAL) -m coverage report -m --sort=cover | sed -n '1,12p;/^TOTAL/p'
	@echo ""
	@echo "=== Rapport complet ==="
	@$(PYTHON_ACTUAL) -m coverage report -m --fail-under=93
	@echo ""
	@echo "=== Garde-fou des modules critiques ==="
	@$(PYTHON_ACTUAL) -m coverage report -m --include="$(CRITICAL_COVERAGE_MODULES)" --fail-under=93
	@$(PYTHON_ACTUAL) -m coverage html -q
	@echo ""
	@echo "Rapport HTML navigable : htmlcov/index.html"
	@echo "(tapez: xdg-open htmlcov/index.html)"

# --- Smoke test de l'artefact ---

smoke:
	@echo "--- Smoke-testing the PyInstaller artefact ---"
	$(PYTHON_ACTUAL) scripts/smoke_test_dist.py

# --- Distribution ---

dist: venv install
	@echo "--- Building executable with PyInstaller ---"
	$(PYTHON_ACTUAL) -m PyInstaller $(APP_NAME).spec

# --- Nettoyage ---

clean:
	@echo "--- Cleaning build artifacts, venv, caches, and coverage ---"
	# Nettoie les répertoires de build et de distribution
	rm -rf build dist .venv
	# Nettoie tous les dossiers __pycache__ dans tout le projet
	find . -name "__pycache__" -type d -exec rm -rf {} +
	# Nettoie les caches d'outils, les rapports de couverture et les métadonnées d'installation
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov .coverage .coverage.* *.egg-info
