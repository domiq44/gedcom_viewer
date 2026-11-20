# AGENTS.md — Principes de qualité génériques

Ce fichier énonce des **principes de qualité génériques et opposables**, indépendants de
tout détail d'implémentation, de langage ou de domaine. Il s'adresse aux agents et
contributeurs qui travaillent sur un projet logiciel.

## Comment utiliser ces deux fichiers

- **`AGENTS.md`** énonce les principes de qualité génériques applicables à tout projet.
- **`PROJECT.md`** (à la racine de chaque dépôt) définit les spécificités de stack,
  domaine et outillage du projet.
- En cas de doute, `AGENTS.md` prévaut sur les principes de qualité et
  `PROJECT.md` sur les détails d'implémentation.
- Toute modification de comportement, d'API ou d'architecture doit être répercutée
  dans les deux fichiers dans la même modification.

Les spécificités d'un projet donné (domaine, stack technique, arborescence,
outillage exact) vivent dans un fichier `PROJECT.md` placé à la racine du dépôt.

## 1. Principe directeur : Responsabilité Unique (SRP)

- Chaque module, classe, fonction et fichier de test a **une seule responsabilité**
  et une seule raison de changer.
- Un fichier = une responsabilité. Une entité qui fait « X et Y » doit être scindée
  en responsabilités distinctes (par exemple : rendu, défilement, copie et
  localisation sont des responsabilités séparables).
- Les tests respectent aussi le SRP : un fichier de test par module testé, une
  classe de test par unité, **un seul scénario par méthode de test**.
- La documentation décrit **un seul** sujet par fichier ou section.

## 2. Règles générales

- Respecter le style existant du projet (PEP 8 pour Python, ou équivalent pour les
  autres langages) et l'outil de formatage configuré.
- Ne pas introduire de dépendance sans vérifier qu'elle n'est pas déjà déclarée.
- Ne jamais committer de secrets, chemins absolus personnels ou données réelles.
- Ne pas modifier l'état UI persisté d'un outil tiers.
- Les fichiers Markdown se terminent par un **saut de ligne unique**.
- `README.md` reste une synthèse courte ; les détails d'installation, d'usage,
  de tests, de build et de CI sont répartis dans `docs/` ou `PROJECT.md`.

## 3. Commits & Git

- **Ne jamais committer sans demande explicite.**
- Vérifier `git status`, `git diff`, `git log --oneline -10` avant tout commit.
- Messages de commit concis, dans le style du dépôt.
- Ne pas forcer le push ; ne pas amender un commit raté (créer un nouveau commit).

## 4. Documentation du code : cartouches et docstrings

- **Tout fichier de code commence par un cartouche** (docstring de module ou
  commentaire d'en-tête selon le langage) indiquant son rôle, en tête de fichier
  avant les imports.
- **Chaque fonction et méthode est précédée d'une docstring** indiquant son rôle.
- Les docstrings décrivent **une seule responsabilité** (cohérent avec le SRP).
- Les documents Markdown portent un nom commençant par une majuscule et
  décrivent un seul sujet (cohérent avec le SRP).
- Les docstrings de test décrivent le comportement vérifié. Les commentaires
  descriptifs de test et les commentaires Given/When/Then sont la seule exception
  autorisée à la règle « aucun commentaire ».
- **Toujours maintenir la documentation à jour** : toute modification de
  comportement, d'API ou d'architecture doit être répercutée dans la même
  modification (docstrings, `README.md`, `AGENTS.md`, `PROJECT.md`, `docs/`).
  Une doc en retard sur le code est un bug.

## 5. Architecture : principes à respecter

Les principes ci-dessous sont des **exemples d'application du SRP** dans différents
contextes architecturaux. Certains sont spécifiques aux applications avec une
interface graphique ; les autres s'appliquent à tout type de logiciel.

### Domaine

- Un seul point de parsing ; un seul point de validation ; une seule source de
  vérité pour la gestion des continuations ou transformations de texte.
- Les modèles sont des wrappers paresseux autour des entités parsées : utiliser le
  lazy loading pour les champs optionnels.
- Les continuations préservent les espaces significatifs ; ne pas « nettoyer »
  les valeurs au risque de corrompre le texte.
- Ne pas dupliquer la logique de bas niveau.

### Contrôleurs / Présentateurs

- Une façade unique est utilisée par l'interface ; les contrôleurs ne sont pas
  instanciés directement par les vues.
- Les contrôleurs ne touchent jamais aux widgets de l'interface (applicable aux
  applications avec interface graphique).
- La logique de présentation (formatage, tri, libellés) n'appartient pas à l'UI.
- Respecter les gardes d'état (chargement / non-chargement).

### Interface (applications avec interface graphique)

- Les vues ne gardent jamais de référence directe au contrôleur : utiliser des
  fournisseurs (closures) pour permettre le remplacement de session.
- Toute mutation de widget se fait sur le thread de l'interface ; les accès
  concurrents passent par un mécanisme de file d'attente / polling.
- Les vues par entité partagent une base commune et surchargent le rendu.
- Les préférences de session (thème, langue, fichiers récents) sont isolées dans
  un module dédié ; l'orchestrateur principal reste responsable du cycle de vie.
- Accéder explicitement aux sous-composants plutôt que de dupliquer des alias.
- Le protocole des résolveurs (injection de fonctions de résolution de pointeurs
  et de formatage des détails) est **documenté** et doit rester stable.

## 6. Tests

- Utiliser exclusivement le framework de test unitaire du langage (ex: `unittest`
  pour Python).
- Les tests suivent l'arborescence de production.
- La découverte s'exécute de manière à éviter que les paquets de test ne masquent
  ceux de production.
- Un fichier de test par responsabilité testée ; une classe de test par unité.
  Un module multi-responsabilités donne lieu à plusieurs fichiers de test.
- Un seul scénario par méthode ; structure **AAA** avec commentaires
  Given/When/Then.
- Préférer les API publiques aux attributs privés ; isoler et nommer les tests
  white-box comme tels.
- **Toute modification du code** (fonctionnalité, correctif, refactoring) doit être
  couverte par un ou plusieurs tests qui échouent avant et passent après.
- Tout correctif de bug s'accompagne d'un test de non-régression.
- **Couverture suffisante** : ne jamais la faire baisser ; imposer un plancher via
  l'outil de couverture du projet (le seuil exact est défini dans `PROJECT.md`).
- Couvrir en priorité : validateur, continuations, coloration syntaxique, vues
  structurées, contrôleurs de recherche / d'entités / de présentation.

### Structure obligatoire : AAA + Given/When/Then

```python
# Vérifie qu'une continuation CONC concatène sans séparateur.
def test_conc_concatenates_without_separator(self):
    # Given (Arrange) une valeur texte
    text = "John"
    # When (Act) on ajoute une continuation CONC
    result = append_continuation(text, "CONC", "/Doe/")
    # Then (Assert) les valeurs sont concaténées sans séparateur
    self.assertEqual(result, "John/Doe/")
```

- **Toute fonction de test unitaire est précédée d'un commentaire décrivant ce
  qu'elle vérifie**, placé juste au-dessus de la fonction.
- **Un seul scénario par méthode** : plusieurs comportements = plusieurs méthodes.
- Les commentaires descriptifs de test et les commentaires Given/When/Then sont
  la seule exception à « aucun commentaire ».

## 7. Qualité & outillage

- **Lint** : utiliser un linter adapté au langage ; la CI vérifie qu'il passe.
- **Format** : utiliser l'outil de formatage du projet ; la CI vérifie qu'il est
  respecté.
- **Typage** : utiliser un vérificateur de types progressif sur les couches de
  production et les outils.
- **Couverture** : imposer un plancher de couverture (ex: 93 %) ; ne jamais le
  faire baisser. Mesurer avec l'outil de couverture du projet.
- **Dépendances** : maintenir un fichier de verrouillage avec les versions exactes
  utilisées par la CI ; auditer les dépendances (`pip-audit --strict` pour Python).
- **CI** : les actions sont épinglées à des versions explicites.
- Ne jamais ignorer un échec de lint, de format ou de typage.
- La CI exécute lint, format, tests, audit, benchmark et construit l'artefact.

## 8. Performance & mémoire

- Charger les données de manière économe : éviter les copies inutiles.
- Préférer le lazy loading pour les champs optionnels.
- Ne pas re-parser les données à chaque extraction : cacher les résultats
  (cache par entité ou par ligne).
- Mesurer tout impact avec le benchmark du projet.

## 9. Build & packaging

- Produire un build autonome via l'outil de packaging du projet.
- Les tests ne doivent pas être embarqués dans l'exécutable.
- Un smoke test de l'artefact doit valider le démarrage.
- Gérer les particularités d'environnement (saisie, affichage headless).
- Le benchmark CI doit utiliser un fichier représentatif ou synthétique.

## 10. Internationalisation

- Langues multiples ; l'anglais est la langue par défaut et le fallback.
- Toute nouvelle chaîne visible doit être ajoutée dans **tous** les fichiers de
  locale.
- Les clés avec `{placeholder}` doivent être appelées avec les kwargs correspondants.

## 11. Robustesse du chargement asynchrone

- Les callbacks de succès/erreur du chargement (polling) doivent être encadrés par
  un `try/except` : une exception ne doit pas interrompre la boucle de sondage ni
  laisser l'interface dans un état incohérent.
- Le remplacement de session n'a lieu qu'après un chargement réussi.
- Le worker reçoit un événement d'annulation qui est vérifié pendant le traitement ;
  un timeout ou une fermeture doit interrompre le traitement.
- Si l'application de la session échoue après publication du contrôleur, restaurer
  l'état UI complet depuis un instantané.

## 12. Thème et interface (applications avec interface graphique)

- Les couleurs et styles sont centralisés ; ne pas les sortir de la source unique.
- Prévoir un thème clair/sombre et, si possible, un changement de thème à l'exécution.
- Le re-thème passe par un registre par session : les composants exposant
  `apply_theme()` s'y enregistrent, sans liste codée en dur.

## 13. Benchmark

- Le benchmark rapporte des mesures de temps et de mémoire.
- L'enrichir avec des indicateurs de dispersion (médiane / p95), une mesure de
  mémoire résidente et une couverture de plusieurs types d'entités.
- Utiliser un fichier représentatif ou synthétique ; éviter les micro-fixtures de
  quelques lignes pour les mesures de performance.

## 14. À éviter (dette technique)

- Dupliquer la logique de bas niveau (continuations, parsing, validation).
- Sortir des couleurs/styles centralisés.
- Dupliquer des alias de widgets.
- Laisser du code mort (imports inutilisés, fonctions non appelées, descripteurs
  masqués par une propriété).
- Mélanger les formes de données (dict / tuple / objet) : normaliser via un point
  unique.
- Ajouter des prints de debug en production.

## 15. Vérifications avant de finaliser

1. Le linter passe.
2. Le formatage passe.
3. Les tests passent.
4. La couverture ne régresse pas.
5. Chaque module a un cartouche ; chaque fonction/méthode a une docstring.
6. Aucune donnée personnelle ni chemin absolu dans le code ou les tests.
