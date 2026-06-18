# GEDCOM Viewer 5.5.1

Un visualiseur GEDCOM moderne écrit en **Python + Tkinter**, permettant d’explorer facilement les fichiers généalogiques au format **GEDCOM 5.5.1**.

Ce projet propose :

- une interface simple et claire  
- une liste des entités GEDCOM (INDI, FAM, OBJE, NOTE, SOUR…)  
- un affichage du bloc GEDCOM brut  
- une **coloration syntaxique** pour une meilleure lisibilité  
- une **fiche Individu** interactive  
- une **fiche Famille** interactive  
- une **navigation par clic** entre individus et familles  
- une **barre de séparation déplaçable**  
- un **redimensionnement dynamique**  
- un lanceur Linux (`run.sh`) robuste  
- une fonctionnalité dédiée : **affichage de l’en‑tête GEDCOM (0 HEAD)**  

---

## 📦 Fonctionnalités principales

### ✔ Chargement de fichiers GEDCOM
Le menu *Fichier → Ouvrir* permet de charger un fichier `.ged`.

Le programme extrait automatiquement les entités présentes dans le fichier.

---

## ✔ Liste des entités par type
Les types d’entités sont affichés dans l’ordre suivant :

1. INDI — Individu  
2. FAM — Famille  
3. OBJE — Multimédia  
4. NOTE — Note  
5. SOUR — Source  
6. SUBM — Fournisseur d'information  
7. REPO — Dépôt  

---

## ✔ Recherche instantanée
Une barre de recherche permet de filtrer les identifiants d’entités en temps réel.

---

## ✔ Affichage du bloc GEDCOM
Un clic sur une entité affiche son bloc GEDCOM brut dans la zone de droite.

---

## ✔ Coloration syntaxique
Le code GEDCOM est mis en couleur :

- niveaux (0, 1, 2…)  
- tags GEDCOM (NAME, BIRT, DEAT…)  
- identifiants (@I123@)  
- dates (12 JAN 1900)  

---

## ✔ Fiche Individu (INDI)
L’onglet **Individu** affiche :

- nom  
- sexe  
- dates et lieux de naissance / décès  
- **Famille (enfant)** — lien cliquable vers la famille FAMC  
- **Familles (parent)** — liens cliquables vers les familles FAMS  

### 🔗 Navigation par clic
Les pointeurs GEDCOM (`@I123@`, `@F456@`) sont **cliquables** :

- cliquer sur une famille → ouvre l’onglet Famille  
- cliquer sur un individu → ouvre l’onglet Individu  

---

## ✔ Fiche Famille (FAM)
L’onglet **Famille** affiche :

- mari  
- femme  
- enfants  
- dates et lieux de mariage / divorce  

Tous les individus sont **cliquables**.

---

## ✔ Navigation bidirectionnelle
La navigation est fluide :

- Individu → Famille (FAMC / FAMS)  
- Famille → Individu (HUSB / WIFE / CHIL)  

---

## ✔ Affichage de l’en‑tête GEDCOM (0 HEAD)
Le menu *Fichier → Afficher l’en‑tête GEDCOM* permet d’afficher :

- la version GEDCOM  
- la source du fichier  
- la date de création  
- le charset  
- les informations du logiciel ayant généré le fichier  

L’extraction est **robuste**, même si :

- le fichier contient un **BOM UTF‑8**  
- HEAD n’est pas stocké comme entité  
- HEAD est suivi immédiatement d’une autre entité  

---

## ✔ Interface redimensionnable
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

Le projet utilise uniquement Tkinter (inclus dans Python).  
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

Arborescence complète :

```
.
├── assets
│   ├── icons
│   └── themes
├── controllers
│   ├── app_controller.py
│   ├── entity_controller.py
│   ├── search_controller.py
│   └── __pycache__
├── gedcom
│   ├── entity.py
│   ├── models
│   │   ├── event.py
│   │   ├── family.py
│   │   ├── individual.py
│   │   └── source.py
│   ├── parser.py
│   ├── search.py
│   └── utils.py
├── ui
│   ├── main_window.py
│   ├── menus.py
│   ├── syntax_highlighter.py
│   ├── themes.py
│   ├── views
│   │   ├── family_view.py
│   │   ├── header_view.py
│   │   └── individual_view.py
│   └── widgets
│       ├── entity_listbox.py
│       ├── entity_type_selector.py
│       ├── gedcom_text_view.py
│       └── search_bar.py
├── main.py
├── run.sh
└── README.md
```

---

## 🧩 Modules importants

### `main.py`
Point d’entrée de l’application.

---

### 📂 `controllers/`
Couche contrôleur (architecture MVC) :

- `app_controller.py` — coordination générale  
- `entity_controller.py` — gestion des entités INDI/FAM  
- `search_controller.py` — logique de recherche  

---

### 📂 `gedcom/`
Contient le parser et les modèles :

- `parser.py` — extraction des entités  
- `entity.py` — représentation brute d’une entité  
- `models/individual.py` — modèle Individu  
- `models/family.py` — modèle Famille  
- `models/source.py` — modèle Source  
- `utils.py` — fonctions utilitaires  

---

### 📂 `ui/`
Interface graphique Tkinter :

- `main_window.py` — fenêtre principale  
- `menus.py` — menus Fichier / Aide  
- `syntax_highlighter.py` — coloration GEDCOM  
- `themes.py` — gestion des thèmes  

#### `ui/views/`
- `individual_view.py` — fiche individu + navigation  
- `family_view.py` — fiche famille + navigation  
- `header_view.py` — affichage de HEAD  

#### `ui/widgets/`
Widgets réutilisables :

- `entity_listbox.py` — liste des entités  
- `entity_type_selector.py` — sélection du type d’entité  
- `gedcom_text_view.py` — zone GEDCOM avec couleurs  
- `search_bar.py` — barre de recherche  

---

## 🧪 Fichier GEDCOM d’exemple

Le dépôt contient un fichier :

```
cretel_ancestris.ged
```

Pour tester l’application.

---

## 🛡️ Script de lancement (`run.sh`)

Le script :

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

Pour toute question ou suggestion, ouvrez une issue ou contactez-moi.
