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

## Recommandations prioritaires

### Priorité 1 : réduire le couplage UI / logique

Il serait bénéfique de découper les responsabilités de la fenêtre principale en composants plus petits :

- panneau de recherche
- liste des entités
- panneau de détail
- navigation
- gestion des paramètres

Cela améliorerait la maintenabilité.

### Priorité 2 : sécuriser la gestion des fichiers volumineux

Le projet mériterait un axe de travail sur :

- chargement paresseux
- index compact
- données calculées à la demande

Même sans changer l’API publique, on peut faire évoluer la façon dont les données sont stockées.

### Priorité 3 : consolider la validation GEDCOM

Le mode strict est une bonne base. L’étape suivante serait d’ajouter des règles de validation plus complètes, avec diagnostics plus explicites pour les fichiers GEDCOM réels.

## Conclusion

Le projet a une bonne base technique, une architecture pensée, et une fonctionnalité utile. Il n’a pas besoin d’être totalement réécrit, mais il gagnerait nettement à être refactoré un peu plus sur la partie interface et sur la gestion des gros volumes de données.

En l’état, c’est un projet sérieux, fonctionnel et bien orienté vers un besoin réel : lire et consulter des arbres généalogiques de manière claire et fiable.
