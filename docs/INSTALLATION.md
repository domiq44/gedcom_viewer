# Installation et lancement

## Prérequis

- Python 3.11, 3.12 ou 3.13 et Tkinter.
- `make` pour utiliser les commandes du projet.

## Dépendances par usage

| Usage | Dépendance | Source / rôle |
| --- | --- | --- |
| Application | `Pillow==13.0.0`, `pypdfium2==5.15.2` | `requirements.txt` ; prévisualisation des images et des PDF (PDFium optionnel à l'exécution) |
| Interface | Tkinter | Module Python avec dépendance système possible ; non installé par `pip` |
| Tests | `unittest` | Bibliothèque standard Python ; aucun paquet `pytest` requis |
| Tests sans affichage | Xvfb (`xvfb-run`) | Paquet système facultatif pour exécuter les tests Tkinter en mode headless |
| Développement | `black==26.10.1`, `ruff==0.17.5`, `coverage==7.17.3`, `mypy==2.4.1`, `pip-audit==2.10.1`, `setuptools==84.2.1` | Formatage, lint, couverture, typage et audit, dans `requirements-dev.txt` |
| Développement verrouillé | versions exactes résolues | Environnement reproductible de la CI, dans `requirements-lock.txt` |
| Génération | `pyinstaller==6.22.3` | Création de l'exécutable, dans `requirements-dev.txt` |

`requirements-dev.txt` inclut `requirements.txt`, Black et PyInstaller.
`requirements-lock.txt` contient les versions exactes installées par la CI.

Pour installer uniquement la dépendance Python de l'application :

```bash
python3 -m pip install -r requirements.txt
```

Pour installer l'environnement de développement :

```bash
make install
```

Le projet expose également des métadonnées PEP 621 : `pip install -e .` installe
la commande `gedcom-viewer`.

## Prérequis système

Sous Fedora Linux, installe les prérequis de base avec :

```bash
sudo dnf install python3 python3-pip python3-tkinter make
```

Pour lancer les tests Tkinter sans session graphique, installe Xvfb, qui fournit
la commande `xvfb-run` :

```bash
sudo dnf install xorg-x11-server-Xvfb
```

Sous Debian ou Ubuntu, le paquet Tkinter s'installe avec :

```bash
sudo apt install python3-tk
```

`ripgrep` (`rg`) est facultatif ; il permet de rechercher rapidement dans le
code, mais n'est requis ni par l'application ni par les tests :

```bash
sudo dnf install ripgrep
```

## Démarrage rapide

La commande suivante crée `.venv` si nécessaire, installe les dépendances de
`requirements-dev.txt`, puis lance l'application :

```bash
make run
```

Le script `run.sh` lance l'application avec `.venv/bin/python` si cet
environnement existe, sinon avec `python3` ou `python`. Il ne procède pas à
l'installation des dépendances. Après installation, l'application peut aussi
être lancée directement :

```bash
.venv/bin/python main.py
```

Au démarrage, le dernier fichier récent est rouvert s'il existe toujours.

## XIM et IBus

Sur Fedora avec `XMODIFIERS=@im=ibus`, les lanceurs retirent cette variable pour
éviter le ralentissement XIM de Tk. Ce réglage s'applique aussi au binaire
PyInstaller exécuté directement. Pour conserver IBus/XIM, définis
`GEDCOM_VIEWER_KEEP_XIM=1` avant de lancer `make run`, `make test`, `./run.sh`,
`python main.py` ou `./dist/gedcom_viewer`.
