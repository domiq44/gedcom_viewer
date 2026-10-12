# Analyse du projet

## Résumé

GEDCOM Viewer est un outil de lecture et d’exploration de fichiers GEDCOM. Le projet est fonctionnel, bien structuré pour une application desktop Python/Tkinter, et il est centré sur une expérience de consultation plutôt que sur une modification des données.

Le point fort majeur est qu’il ne s’agit pas seulement d’un parser : il combine parsing, modélisation métier, recherche, navigation par pointeurs et interface utilisateur dans une architecture cohérente.

## Ce qui fonctionne bien

### 1. Séparation des responsabilités

Le projet est divisé en couches relativement propres :

- `ui/` pour l’interface
- `controllers/` pour l’orchestration
- `gedcom/` pour le parsing et les modèles
- `tests/` pour la validation fonctionnelle

Cette séparation rend le code plus facile à comprendre et à faire évoluer.

### 2. Gestion GEDCOM solide

Le parser sait :

- lire des fichiers GEDCOM
- identifier les enregistrements de niveau 0
- indexer par type et par pointeur
- signaler les lignes malformées
- gérer les cas de chargement tolérant ou strict

La gestion des références comme `HUSB`, `WIFE`, `CHIL`, `SOUR`, `REPO`, `NOTE` et `OBJE` est particulièrement utile pour l’interface.

### 3. Expérience utilisateur satisfaisante

Le projet propose :

- recherche instantanée
- filtre par type d’entité
- tri numérique des identifiants
- historique de navigation
- affichage du bloc GEDCOM brut
- vues détaillées selon le type
- support multilingue

Cela donne un produit qui a un vrai aspect d’application utilisable, pas seulement une preuve de concept.

## Points faibles

### 1. UI très dense

La classe principale de l’interface dans `ui/main_window.py` est volumineuse. C’est le premier point limite du projet : elle mélange beaucoup de responsabilités.

À long terme, cela rendra le projet plus coûteux à maintenir, surtout si on ajoute des fonctionnalités ou de nouvelles vues.

### 2. Chargement entièrement en mémoire

Le README le note explicitement : le projet charge les données en mémoire intégralement. Ce choix est simple et performant pour des fichiers moyens, mais il devient une limitation pour des GEDCOM très volumineux.

C’est un point à surveiller si le projet doit gérer des bases familiales beaucoup plus importantes.

### 3. Validation GEDCOM partielle

Le mode strict est utile, mais il ne couvre pas toute la conformité GEDCOM. Le projet est fonctionnel et “fort” sur l’usage courant, mais pas encore une validation complète de standard.

Cela est acceptable pour un outil de consultation, mais il faut le garder en tête comme limite fonctionnelle.

### 4. Architecture encore orientée “application monolithique”

L’application est cohérente, mais elle n’a pas encore complètement franchi le pas vers un modèle plus modulaire. La logique de l’interface est encore très proche du reste du système.

## État actuel du projet

### Points de qualité

- bonne séparation des dossiers
- architecture globale cohérente
- logique métier lisible
- tests présents et utiles
- l’application est réellement exploitable

### Points à surveiller

- lourdeur de `ui/main_window.py`
- mémoire pour les gros GEDCOM
- validation GEDCOM standard complète
- potentiel de couplage entre UI et logique métier

### Constats vérifiés

- La suite complète contient 176 tests et passe localement.
- Le contrôle Black passe sur les 55 fichiers couverts par la CI.
- L’action GitHub CI #21 a réussi sur `b54e582`, y compris les tests sous Xvfb
  et le build PyInstaller.
- La compilation syntaxique de tous les fichiers Python passe.
- Le parser charge les fichiers en mémoire complète dans `gedcom/parser.py`.
- Le parseur préserve désormais les espaces répétés dans les valeurs de ligne.
- Le chargement asynchrone construit un contrôleur local dans le thread de travail
  puis le publie dans le thread Tkinter après succès.
- Les résolveurs de pointeurs des vues (`ui/views/*.py`) sont désormais branchés via
  des fonctions qui lisent `self.controller` dynamiquement dans `main_window.py`,
  et non plus via des méthodes liées figées à la construction. Un bug a été corrigé à
  ce sujet : après un chargement asynchrone, `self.controller` est remplacé par une
  nouvelle instance, ce qui rendait silencieusement inopérants tous les résolveurs
  bindés à l'ancien contrôleur (aucune exception, résolution systématique à `None`).
- La coordination du chargement est isolée dans `ui/load_coordinator.py`, tandis
  que `ui/main_window.py` conserve l’application du résultat à l’interface.
- `ui/entity_browser.py` possède le filtrage, le debounce, le tri et le remplissage
  de la liste; `ui/entity_list_panel.py` construit les widgets correspondants.
- La barre de navigation est isolée dans `ui/navigation_bar.py`, tandis que la
  fenêtre conserve la navigation métier et l'historique.
- Le formulaire Individu propose deux onglets en bas (Familles (parent) à deux
  colonnes nom/identifiant, et Enfants), alimentés par les mêmes résolveurs.
- Le `DetailPanel` sépare désormais le bloc GEDCOM brut et le formulaire d’entité
  via un `PanedWindow` redimensionnable.
- L'historique de navigation conserve au plus 100 contextes complets.
- Les valeurs ASCII utilisent `casefold()` directement; les textes non ASCII
  conservent la normalisation Unicode qui ignore les accents. Cette optimisation
  accélère les recherches sans index de recherche persistant.
- L'interface applique désormais un debounce de 100 ms avant de relancer la
  recherche et annule ce callback lors de la fermeture.

Le risque de concurrence initial a été traité : le parser du service actif n'est
plus remplacé depuis le thread de travail. L'ancienne session reste cohérente
pendant le chargement et est conservée en cas d'erreur. Les résultats tardifs sont
ignorés lorsque la fenêtre est en cours de fermeture.

La commande de validation complète est :

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests
```

Dernière validation locale : les 176 tests passent; la CI utilise Xvfb pour les
tests Tkinter.

## Recommandations prioritaires

### Priorité 1 : protéger les données personnelles dans les journaux (traitée)

Les lignes GEDCOM malformées, les chemins locaux et les messages d’exception
peuvent révéler des données personnelles. Les logs du parser et de l’interface
ne consignent que la nature de l’anomalie, les compteurs utiles et le type
d’erreur, sans contenu GEDCOM ni chemin. Des tests de non-divulgation couvrent
ces cas.

### Priorité 2 : mesurer et maîtriser la mémoire

Le benchmark reproductible est disponible dans
`benchmarks/benchmark_search.py`. Sur 100 000 individus, le dernier run a mesuré
29,8 MiB côté parser, 34,3 MiB pour les modèles et 64,1 MiB retenus au pic.
Le chargement a pris 5,28 s; la recherche ASCII 42,7 ms, contre 337 ms avec la
normalisation Unicode complète. La consultation des champs optionnels ajoute
73,8 MiB, notamment parce que toutes les listes vides sont alors matérialisées.
Ces temps varient selon l’environnement. La validation évite
également les collections temporaires proportionnelles aux enregistrements
valides. Le benchmark reproduit maintenant les scénarios de familles,
d’événements, de sources et de champs optionnels individuels via ses options
CLI (`--events-per-source`, `--texts-per-individual`, `--notes-per-individual`,
`--occupations-per-individual`, `--properties-per-individual`,
`--fams-per-individual`, `--obje-per-individual`, `--metadata-per-source`). Il
rapporte la mémoire du parser, l’incrément des modèles et le delta après
consultation des propriétés différées.
Une mesure
synthétique séparée de 50 000 familles avec seulement les
 références des conjoints donne 19,6 MiB pour `Family`, contre 41,0 MiB avant les
 slots et les listes paresseuses. Le benchmark accepte désormais `--families`;
 100 000 individus avec 50 000 familles mesurent 103,4 MiB au pic. Le parser
 conserve toujours les lignes, index et modèles métier. Des mesures synthétiques
séparées de 50 000 sources et 50 000 notes éparses passent respectivement de
32,5 à 16,5 MiB et de 26,5 à 13,6 MiB avec slots et listes paresseuses.
Plusieurs données optionnelles sont désormais différées : événements familiaux
et source, références `FAMS` et `OBJE`, notes, textes, occupations et propriétés
individuels. Des mesures
isolées estiment à 5,34 MiB le coût d’événements pour 10 000 sources consultées,
et à 4,15 MiB celui des notes et références de 10 000 sources,
à 2,59 MiB celui des notes pour 10 000 individus, à 1,74 MiB celui des textes,
et à 7,56 MiB celui de deux occupations datées et une propriété pour 10 000
individus. Les références `FAMS` et `OBJE` ajoutent 3,52 MiB après accès pour
10 000 individus en mesure synthétique. Un scénario combiné de 10 000 individus,
5 000 familles et 1 000 enregistrements par autre type mesure 9,1 MiB dans le
parser (tampon brut et offsets) et 5,9 MiB supplémentaires pour les modèles
(15,0 MiB retenus au total). La consultation des propriétés ajoute 35,1 MiB,
listes vides matérialisées comprises. Le chargement tracé passe de 3,81 s avec
la liste de lignes à 3,42 s avec le tampon compact sur ce scénario. Ces mesures
 synthétiques n’incluent pas l’empreinte totale du fichier GEDCOM : les lignes
 brutes restent toutes en mémoire. Cent mille objets `Event` sans détails
passent de 15,3 à 6,1 MiB avec slots et détails paresseux. Cinquante mille
objets multimédias passent de 15,7 à 13,8 MiB avec slots.
Une mesure de 50 000 dépôts épars passe de 25,9 à 15,2 MiB avec slots et listes
paresseuses. Cinquante mille submitters épars passent de 19,9 à 12,2 MiB avec
slots et listes paresseuses.

### Historique de navigation : limitation réalisée

L'historique est limité à 100 entrées dans `controllers/navigation_history.py`.

### Priorité 3 : poursuivre la modularisation de l'interface si nécessaire

Les composants principaux (chargement, recherche et liste, navigation, détail,
vues) sont déjà extraits. La fenêtre principale conserve l'orchestration; de
nouvelles extractions peuvent suivre les besoins plutôt que constituer un chantier
de refonte.

### Priorité 4 : consolider la validation GEDCOM

Le mode strict est une bonne base. L’étape suivante serait d’ajouter des règles de validation plus complètes, avec diagnostics plus explicites pour les fichiers GEDCOM réels.

### Priorité 5 : automatiser la qualité du projet

La CI est définie dans `.github/workflows/ci.yml`. Elle exécute les tests Tkinter
sous Xvfb, la compilation syntaxique, le contrôle Black et le build PyInstaller.
L’action CI #21 a réussi sur `b54e582`; le travail restant est de maintenir ces
gates vertes pour les changements suivants.

## Ordre d'exécution recommandé

1. Mesurer sur des GEDCOM réels et évaluer une lecture incrémentale ou mappée
   pour les fichiers dont le tampon compact reste trop volumineux.
2. Définir les versions GEDCOM ciblées et compléter les règles strictes.
3. Garder les tests, Black et PyInstaller verts en CI.
4. Extraire d’autres responsabilités de `ui/main_window.py` selon les besoins.

## Conclusion

Le projet a une base technique cohérente et n’a pas besoin d’être réécrit. Les
chantiers restants sont ciblés : confirmer les performances sur des données
réelles, étudier le traitement incrémental des très gros fichiers et préciser la
portée de la validation GEDCOM.

En l’état, c’est un projet sérieux, fonctionnel et bien orienté vers un besoin réel : lire et consulter des arbres généalogiques de manière claire et fiable.
