# Architecture du projet

## Vue d’ensemble

GEDCOM Viewer est une application desktop Python/Tkinter pour lire, rechercher et explorer des fichiers GEDCOM. Le projet est organisé selon une séparation classique entre interface, contrôleurs, service métier et parsing.

Le cœur du design est le suivant :

```text
main.py
  -> ui.main_window.GedcomViewer
      -> controllers.app_controller.AppController
          -> GedcomService
              -> GedcomParser
              -> EntityController
          -> SearchController
          -> PresentationController
      -> ui.views/*
```

## Structure du dépôt

```text
.
├── main.py
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── Makefile
├── run.sh
├── gedcom/
│   ├── parser.py
│   └── models/
├── controllers/
├── ui/
│   ├── locales/
│   ├── views/
│   ├── i18n.py
│   ├── main_window.py
│   ├── menus.py
│   ├── themes.py
│   └── syntax_highlighter.py
├── tests/
├── docs/
│   ├── screenshots/
│   ├── architecture.md
│   └── analysis.md
└── gedcom-test.ged
```

## Couches applicatives

### 1. Couche interface : ui/

Le dossier `ui/` contient tout ce qui concerne l’interface utilisateur :

- `main_window.py` : fenêtre principale, layout et orchestration des transitions
- `load_coordinator.py` : chargement asynchrone, polling et cycle de fermeture
- `entity_browser.py` : filtrage, debounce, tri et remplissage de la liste
- `entity_list_panel.py` : widgets de recherche, d’effacement et de liste
- `navigation_bar.py` : boutons et état visuel de l’historique
- `menus.py` : menu principal de l’application
- `themes.py` : palette visuelle et styles
- `syntax_highlighter.py` : coloration syntaxique du bloc GEDCOM brut
- `i18n.py` : gestion de la traduction
- `views/` : vues détaillées selon le type d’entité

L’UI est entièrement construite en `Tkinter` et reste centrée sur une fenêtre unique. `GedcomViewer` orchestre les transitions, tandis que `EntityBrowser` possède l’état et la logique de la liste.

Les vues `IndividualView` et `FamilyView` exposent des résolveurs (`set_family_name_resolver`, `set_family_member_resolver`, `set_family_label_resolver`, `set_family_display_name_resolver`, `set_name_resolver`, `set_source_resolver`, `set_note_resolver`, etc.) branchés depuis `main_window.py`. Ces résolveurs sont des fonctions qui accèdent à `self.controller` au moment de l’appel (et non des méthodes liées figées à la construction), car `self.controller` est remplacé par une nouvelle instance après chaque chargement asynchrone de fichier : un branchement figé continuerait sinon de pointer vers l’ancien contrôleur, désormais vide.

Le formulaire `IndividualView` affiche, en bas, six onglets alimentés par ces résolveurs :

- **Familles (parent)** : liste à deux colonnes (nom, identifiant) des familles où l’individu est conjoint (`FAMS`).
- **Enfants** : liste des enfants de ces familles, déduits en résolvant chaque `FAMS` puis ses `CHIL`.
- **Notes** : liste à deux colonnes ; les notes référencées par pointeur (`@N..@`) sont résolues via `set_note_resolver` et cliquables, les notes en texte inline restent affichées sans lien.
- **Textes**, **Propriétés**, **Occupations** : listes simples déplacées depuis les anciens champs en ligne.

Le formulaire `FamilyView` propose de la même façon quatre onglets en bas :

- **Enfants** et **Sources** : listes à deux colonnes (nom/titre, identifiant), cliquables.
- **Notes** : liste à deux colonnes, avec résolution et lien cliquable pour les notes référencées par pointeur.
- **Événements** : liste simple (pas d’identifiant pertinent).

Le changement de type d’entité dans le panneau de gauche réinitialise désormais le champ de filtre de recherche (`search_var`), pour éviter qu’un filtre resté affiché ne devienne incohérent avec la nouvelle liste affichée.

Le `DetailPanel` sépare le bloc GEDCOM brut et le formulaire d’entité au moyen d’un `tk.PanedWindow` redimensionnable (au lieu d’un simple `pack` figé), afin de permettre d’élargir librement l’un ou l’autre panneau.

### 2. Couche orchestration : controllers/

Les contrôleurs servent de façade entre l’UI et le service GEDCOM :

- `app_controller.py` : point d’entrée applicatif, initialisation des sous-contrôleurs
- `gedcom_service.py` : chargement du fichier GEDCOM et accès aux données chargées
- `entity_controller.py` : transformation des entités brutes en objets métier
- `search_controller.py` : tri, liste, recherche et libellés d’entités
- `presentation_controller.py` : préparation du contexte d’affichage et résolution de pointeurs

Cette couche est la partie la plus structurée du projet et elle joue le rôle d’interface métier propre.

### 3. Couche métier / parsing : gedcom/

Le package `gedcom/` est composé de :

- `parser.py` : lecture du fichier, découpage en enregistrements, indexation et validation structurelle
- `models/` : objets métier comme `Individual`, `Family`, `Source`, `Repository`, `Note`, `MultimediaObject`, `Submitter`

Le parser construit des entités brutes puis les objets métier sont produits par `EntityController`.

## Flux de chargement

Le flux métier est simple et linéaire :

```text
Fichier GEDCOM
  -> GedcomParser.load(...)
  -> extraction des enregistrements
  -> indexation par type et pointeur
  -> EntityController.build_*
  -> AppController / SearchController / PresentationController
  -> affichage Tkinter
```

Le chargement est exécuté dans un thread de travail pour éviter de bloquer
l’interface. Le worker construit une nouvelle instance complète de
`AppController` sans modifier la session active, puis transmet le résultat au
thread principal de Tkinter via une file de messages. L’interface publie cette
nouvelle session uniquement après un chargement réussi.

En cas d’erreur, l’ancienne session reste disponible. Lors de la fermeture de la
fenêtre, les résultats asynchrones en attente sont ignorés et aucun nouveau
chargement n’est accepté.

## Gestion des entités

Le projet supporte les types GEDCOM classiques :

- `INDI`
- `FAM`
- `SOUR`
- `REPO`
- `NOTE`
- `OBJE`
- `SUBM`

Chaque type est transformé en objet métier dédié, ce qui permet de garder un accès plus lisible pour l’UI et la recherche.

## Recherche et navigation

La recherche est centralisée dans `SearchController` et prend en charge :

- la liste des entités filtrées par type
- le tri selon le nom, le titre ou le pointeur
- la recherche insensible à la casse et aux accents
- la résolution des références GEDCOM telles que `HUSB`, `WIFE`, `CHIL`, `SOUR`, `REPO`, etc.

La navigation entre pointeurs est également couverte au niveau de l’UI, avec historique précédent/suivant.

## Validation GEDCOM

Le parser de `gedcom/parser.py` supporte deux modes :

- mode tolérant : charge les données et signale les anomalies
- mode strict : refuse le fichier si des anomalies détectées le rendent invalide

Les règles vérifiées portent notamment sur :

- lignes malformées
- préservation des espaces répétés dans les valeurs
- sauts de niveau
- pointeurs invalides
- pointeurs manquants sur les enregistrements indexés (`INDI`, `FAM`, `SOUR`,
  `REPO`, `SUBM`, `OBJE`)
- pointeurs de référence mal formés
- références obligatoires manquantes
- doublons de pointeurs
- références inconnues ou incompatibles avec le type attendu par leur tag
- références `ALIA`, `FAMC` et `FAMS` de niveau 1 dans `INDI`
- référence `ASSO` de niveau 1 dans `INDI`
- références `HUSB`, `WIFE` et `CHIL` de niveau 1 dans `FAM`
- référence `SUBM` de niveau 1 dans `HEAD`
- référence `REPO` de niveau 1 dans `SOUR`
- ordre attendu de `HEAD` et `TRLR`
- absence de sous-enregistrements après `TRLR`
- absence ou multiplicité de `HEAD` / `TRLR`

## Dépendances

Le projet dépend de :

- Python 3
- Tkinter
- Pillow pour la prévisualisation des images
- PyInstaller pour la génération d’exécutable
- Black pour le formatage

Les dépendances sont gérées via `requirements.txt`, `requirements-dev.txt`, et le `Makefile`.

## Forces de l’architecture

- séparation claire entre interface, contrôleurs et parsing
- logique de recherche centralisée
- objets métier lisibles
- support de validation strict/tolérant
- bonne séparation des responsabilités par dossier

## Points de friction

- la fenêtre principale `main_window.py` est très dense
- l’UI est fortement centralisée dans un seul composant
- le chargement des gros fichiers est entièrement en mémoire
- la validation GEDCOM est structurée mais reste limitée à un niveau fonctionnel

Le chargement asynchrone est désormais isolé dans `LoadCoordinator` et testé. Les points encore ouverts
concernent principalement la mémoire des gros fichiers, l’annulation explicite
d’un chargement et l’affichage éventuel d’une progression.

## Conclusion

L’architecture est cohérente pour une application de consultation de fichiers GEDCOM. Elle est simple à comprendre, proprement découpée, et suffisamment modulable pour évoluer sans réécrire tout le projet.

Le principal travail d’évolution à venir porte surtout sur la modularisation
progressive de l’interface et sur la gestion de fichiers très volumineux.
