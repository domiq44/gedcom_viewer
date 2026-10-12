PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
APP_NAME ?= gedcom_viewer

.PHONY: help install run test format lint dist clean check_pip check_tk venv

help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  venv        Create the virtual environment (.venv)"
	@echo "  install     Install pip, Tkinter (system check), Pillow, PyInstaller and Black"
	@echo "  run         Create the venv if needed and launch the application locally"
	@echo "  test        Run the Python unit tests"
	@echo "  format      Format Python sources with Black"
	@echo "  lint        Check Python syntax for all source files"
	@echo "  dist        Build a standalone executable with PyInstaller"
	@echo "  clean       Remove build artifacts and venv"

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

check_tk:
	@echo "Checking Tkinter..."
	@if ! $(PYTHON_ACTUAL) -c "import tkinter" >/dev/null 2>&1; then \
		echo "Tkinter is not installed."; \
		echo "Install it with your system package manager:"; \
		echo "  Debian/Ubuntu: sudo apt install python3-tk"; \
		echo "  Fedora: sudo dnf install python3-tkinter"; \
		echo "  Arch: sudo pacman -S tk"; \
		echo "  macOS: Tkinter is included with python.org installers"; \
	else \
		echo "Tkinter is installed."; \
	fi

# --- Installation ---

install: venv check_pip check_tk
	@echo "Installing project dependencies..."
	$(PYTHON_ACTUAL) -m pip install -r requirements-dev.txt

# --- Exécution et Test ---

run: venv install
	echo "--- Running application ---"
	$(PYTHON_ACTUAL) main.py

test: venv install
	echo "--- Running tests ---"
	$(PYTHON_ACTUAL) -m unittest discover -s tests

# --- Formatage et Linting ---

format: install
	@echo "--- Formatting sources with Black ---"
	$(PYTHON_ACTUAL) -m black .

lint:
	@echo "--- Linting sources ---"
	find . -name "*.py" \
		-not -path "./build/*" \
		-not -path "./dist/*" \
		-not -path "./.venv/*" \
		-print0 | xargs -0 $(PYTHON_ACTUAL) -m py_compile

# --- Distribution ---

dist: venv install
	@echo "--- Building executable with PyInstaller ---"
	$(PYTHON_ACTUAL) -m PyInstaller $(APP_NAME).spec

# --- Nettoyage ---

clean:
	@echo "--- Cleaning build artifacts, venv, and __pycache__ ---"
	# Nettoie les répertoires de build et de distribution
	rm -rf build dist .venv
	# Nettoie tous les dossiers __pycache__ dans tout le projet
	find . -name "__pycache__" -type d -exec rm -rf {} +
