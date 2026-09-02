PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
APP_NAME ?= gedcom_viewer

.PHONY: help install run test format lint dist clean check_pip check_tk

help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  install     Install pip (if missing), Tkinter (if missing), PyInstaller and Black"
	@echo "  run         Launch the application locally"
	@echo "  test        Run the Python unit tests"
	@echo "  format      Format Python sources with Black"
	@echo "  lint        Check Python syntax for all source files"
	@echo "  dist        Build a standalone executable with PyInstaller"
	@echo "  clean       Remove build artifacts"

# Vérifie si pip est installé
check_pip:
	@echo "Checking pip..."
	@if ! command -v pip >/dev/null 2>&1; then \
		echo "pip not found. Attempting installation..."; \
		$(PYTHON) -m ensurepip --upgrade || echo "Failed to install pip. Install it manually."; \
	else \
		echo "pip is installed."; \
	fi

# Vérifie si Tkinter est disponible
check_tk:
	@echo "Checking Tkinter..."
	@if ! $(PYTHON) -c "import tkinter" >/dev/null 2>&1; then \
		echo "Tkinter is not installed."; \
		echo "Install it with your system package manager:"; \
		echo "  Debian/Ubuntu: sudo apt install python3-tk"; \
		echo "  Fedora: sudo dnf install python3-tkinter"; \
		echo "  Arch: sudo pacman -S tk"; \
		echo "  macOS: Tkinter is included with python.org installers"; \
	else \
		echo "Tkinter is installed."; \
	fi

install: check_pip check_tk
	@if [ -n "$$VIRTUAL_ENV" ] || [ -d .venv ]; then \
		$(PYTHON) -m pip install pyinstaller black; \
	else \
		$(PYTHON) -m pip install --user pyinstaller black; \
	fi

run:
	$(PYTHON) main.py

test:
	$(PYTHON) -m unittest discover -s tests

format:
	$(PYTHON) -m black .

lint:
	find . -name "*.py" \
		-not -path "./build/*" \
		-not -path "./dist/*" \
		-not -path "./.venv/*" \
		-print0 | xargs -0 $(PYTHON) -m py_compile

dist: install
	$(PYTHON) -m PyInstaller $(APP_NAME).spec

clean:
	rm -rf build dist
