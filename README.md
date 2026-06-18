# GEDCOM Viewer 5.5.1

Un visualiseur GEDCOM moderne écrit en **Python + Tkinter**, permettant d’explorer facilement les fichiers généalogiques au format **GEDCOM 5.5.1**.

Ce projet propose :

- une interface simple et claire  
- une liste des entités GEDCOM (INDI, FAM, OBJE, etc.)  
- un affichage du bloc GEDCOM brut  
- une **coloration syntaxique** pour une meilleure lisibilité  
- une **barre de séparation déplaçable** entre les zones gauche/droite  
- un **redimensionnement dynamique** de l’interface  
- un lanceur Linux (`run.sh`) robuste  
- une fonctionnalité dédiée : **affichage de l’en‑tête GEDCOM (0 HEAD)**  

---

## 📦 Fonctionnalités principales

### ✔ Chargement de fichiers GEDCOM
Le menu *Fichier → Ouvrir* permet de charger un fichier `.ged`.

Le programme extrait automatiquement les types d’entités présents dans le fichier.

### ✔ Liste des entités par type
Les types d’entités sont affichés dans l’ordre suivant :

1. INDI — Individu  
2. FAM — Famille  
3. OBJE — Multimédia  
4. NOTE — Note  
5. SOUR — Source  
6. SUBM — Fournisseur d'information  
7. REPO — Dépôt  

Le changement de type met automatiquement à jour la liste.

### ✔ Recherche instantanée
Une barre de recherche permet de filtrer les identifiants d’entités en temps réel.

### ✔ Affichage du bloc GEDCOM
Un clic sur une entité affiche son bloc GEDCOM brut dans la zone de droite.

### ✔ Coloration syntaxique
Le code GEDCOM est mis en couleur :

- niveaux (0, 1, 2…)  
- tags GEDCOM (NAME, BIRT, DEAT…)  
- identifiants (@I123@)  
- dates (12 JAN 1900)  

### ✔ Affichage de l’en‑tête GEDCOM (0 HEAD)
Le menu *Fichier → Afficher l’en‑tête GEDCOM* permet d’afficher :

- la version GEDCOM  
- la source du fichier  
- la date de création  
- le charset  
- les informations du logiciel ayant généré le fichier  
- les métadonnées diverses  

L’extraction est **robuste**, même si :

- le fichier contient un **BOM UTF‑8** (`\ufeff`)  
- HEAD n’est pas stocké comme entité dans le parser  
- HEAD est suivi immédiatement d’une autre entité (`0 @X@ TAG`)  

### ✔ Interface redimensionnable
- La zone de droite s’adapte automatiquement à la taille de la fenêtre  
- Une **barre de séparation déplaçable** permet d’ajuster la largeur de la zone de gauche  

---

## 🛠 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/gedcom-viewer.git
cd gedcom-viewer
```

### 2. Installer les dépendances

Le projet utilise uniquement Tkinter (inclus dans Python) et un parser GEDCOM interne.

Aucune installation supplémentaire n’est requise.

---

## ▶️ Lancer l’application

### Sous Linux / macOS

```bash
./run.sh
```

ou :

```bash
bash run.sh
```

### Sous Windows

```bash
python main.py
```

---

## 📁 Structure du projet

Arborescence actuelle :

```
.
├── assets
│   └── icons
├── cretel_ancestris.ged
├── gedcom
│   ├── __init__.py
│   ├── parser.py
│   ├── search.py
│   └── __pycache__/
├── main.py
├── README.md
├── run.sh
└── ui
    ├── __init__.py
    ├── main_window.py
    ├── menus.py
    ├── syntax_highlighter.py
    ├── themes.py
    └── __pycache__/
```

---

## 🧩 Modules importants

### `main.py`
Point d’entrée de l’application.

### `gedcom/parser.py`
Parser GEDCOM minimaliste utilisé pour extraire les blocs d’entités.  
Il gère :

- la lecture du fichier  
- la normalisation des lignes  
- l’extraction des entités par pointeur  
- l’accès aux lignes brutes pour HEAD  

### `gedcom/search.py`
Fonctions utilitaires pour la recherche dans les données GEDCOM.

### `ui/main_window.py`
Interface principale :  
- liste des entités  
- zone d’affichage  
- gestion des événements  
- barre de séparation déplaçable  
- extraction robuste de l’en‑tête HEAD  

### `ui/syntax_highlighter.py`
Coloration syntaxique du contenu GEDCOM.

### `ui/menus.py`
Gestion des menus (Fichier, Aide…).

### `ui/themes.py`
Gestion des thèmes graphiques (si activés).

### `assets/icons/`
Icônes de l’application.

---

## 🧪 Fichier GEDCOM d’exemple

Le dépôt contient un fichier :

```
cretel_ancestris.ged
```

Il peut être utilisé pour tester l’application.

---

## 🛡️ Script de lancement (`run.sh`)

Le script `run.sh` :

- détecte automatiquement `python3` ou `python`  
- vérifie la présence de `main.py`  
- exécute l’application depuis le bon répertoire  
- utilise `set -euo pipefail` pour plus de robustesse  

---

## 📜 Licence

Projet libre d’utilisation et de modification.

---

## 🤝 Contributions

Les contributions sont les bienvenues :  
corrections, améliorations, nouvelles fonctionnalités…

---

## 📧 Contact

Pour toute question ou suggestion, n’hésitez pas à ouvrir une issue ou à me contacter.
