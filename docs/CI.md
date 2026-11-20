# Intégration continue

La CI s'exécute sur Linux (Ubuntu 24.04) pour Python 3.11, 3.12 et 3.13. Elle
enchaîne :

1. installation des dépendances depuis `requirements-lock.txt`, avec cache pip
   indexé sur le verrou ;
2. `pip check` et `pip-audit --strict` ;
3. lint (ruff, `black --check`, compilation) et conformité (locales, docstrings,
   commentaires de test) ;
4. `make typecheck` ;
5. tests sous Xvfb avec couverture minimale de 93 % et garde-fou dédié aux
   modules critiques ;
6. génération d'un GEDCOM de benchmark représentatif puis benchmark de
   recherche ;
7. benchmark synthétique 20 000 / 50 000 / 100 000 individus avec seuils de
   chargement, de médiane de recherche et de mémoire résidente ;
8. construction PyInstaller, smoke-test de l'artefact puis publication de
   `dist/` en artefact GitHub Actions ;

Un second travail, `domain-tests`, exécute les tests du domaine (`tests/gedcom`)
sur Windows et macOS pour Python 3.12. Ces tests ne dépendent ni de Tkinter ni
d'un affichage : ils valident le parseur, le validateur, les continuations et les
modèles sur les plateformes de bureau.

Les actions GitHub sont épinglées à des versions explicites
(`actions/checkout@v4.2.2`, `actions/setup-python@v5.6.0`). La matrice
multiplateforme reste volontairement limitée aux tests du domaine tant que
l'interface graphique n'est pas prioritaire sur ces plateformes.
