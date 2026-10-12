# Feuille de route

## Objectif

Donner une trajectoire claire pour faire évoluer GEDCOM Viewer sans casser
l’architecture existante ni perdre la simplicité d’usage actuelle.

## Priorité 1 — stabiliser le chargement asynchrone

### État du chargement

Terminée.

### Changements du chargement

- construction d’un `AppController` isolé dans le thread de travail ;
- publication de la nouvelle session uniquement après succès ;
- conservation de l’ancienne session en cas d’erreur ;
- gestion de la fermeture de la fenêtre et des résultats tardifs ;
- ajout de tests d’intégration et de cinq tests unitaires dédiés au chargement
  asynchrone.

## Priorité 2 — améliorer la maintenabilité de l’interface

### État de l’interface

Terminée.

### Composants extraits

- isolation de la coordination du chargement dans `ui/load_coordinator.py` ;
- extraction du panneau de recherche et de liste dans `ui/entity_list_panel.py` ;
- extraction de la barre de navigation dans `ui/navigation_bar.py` ;
- extraction du sélecteur de type d’entité dans `ui/entity_type_panel.py` ;
- extraction du panneau de contenu et vues détaillées dans `ui/detail_panel.py` ;
- extraction de l’en-tête dans `ui/app_header.py` ;
- extraction de la gestion des fichiers récents dans `ui/file_manager.py` ;
- extraction du menu applicatif dans `ui/application_menu.py` ;
- extraction du navigateur d’entités dans `ui/entity_browser.py` ;
- transfert du filtrage, du debounce, du tri et du remplissage de la liste vers
  `ui/entity_browser.py` ;
- extraction de la navigation d’entités dans `ui/entity_navigator.py` ;
- extraction de la gestion des vues détaillées dans `ui/entity_view_manager.py` ;
- mise en place d’un debounce de 100 ms sur la recherche côté interface ;
- réduction de la logique UI dans `ui/main_window.py`.

### Objectif interface

Rendre la fenêtre principale plus facile à maintenir et à faire évoluer.

### Actions interface

- extraire les sous-parties de la fenêtre en composants plus petits ;
- isoler la coordination du chargement dans `ui/load_coordinator.py` ;
- isoler le panneau de recherche et de liste dans `ui/entity_list_panel.py` ;
- isoler la barre de navigation dans `ui/navigation_bar.py` ;
- séparer la logique de recherche, de tri et de navigation ;
- limiter les recalculs de recherche avec un debounce côté interface ;
- isoler les vues détaillées derrière une API cohérente ;
- limiter la logique UI dans `ui/main_window.py`.

Les extractions prévues sont réalisées. La fenêtre principale conserve
l’orchestration de l’application et les transitions entre contrôleurs et vues.

### Bénéfices de la modularisation

- code plus lisible ;
- moins de couplage ;
- ajout de fonctionnalités plus simple.

## Priorité 2 bis — corriger les résolveurs figés et enrichir le formulaire Individu

### État des résolveurs

Terminée.

### Changements des résolveurs

- correction d’un bug où les résolveurs de pointeurs des vues restaient liés à
  l’ancien `AppController` après un chargement asynchrone (remplacement de
  `self.controller`), ce qui rendait silencieusement toutes les résolutions de
  noms inopérantes sans erreur visible ; les résolveurs sont désormais des
  fonctions qui accèdent à `self.controller` au moment de l’appel ;
- ajout de deux onglets en bas du formulaire Individu : **Familles (parent)**
  (liste à deux colonnes nom/identifiant, alimentée par
  `format_entity_display_name`) et **Enfants** (déduits des `FAMS` de
  l’individu) ;
- réutilisation de l’API `format_entity_label` / `format_entity_display_name`
  du `SearchController` plutôt qu’une logique de résolution dupliquée dans les
  vues ;
- `DetailPanel` sépare désormais le bloc GEDCOM brut et le formulaire d’entité
  avec un `PanedWindow` redimensionnable au lieu d’un partage figé à 50/50.

### Bénéfices des résolveurs

- fiabilité des noms affichés après le premier chargement de fichier ;
- ergonomie améliorée pour explorer les familles et enfants d’un individu ;
- panneau de détail redimensionnable selon les besoins de lecture.

## Priorité 2 ter — généraliser les onglets à deux colonnes dans les formulaires

### État des formulaires

Terminée.

### Changements des onglets

- ajout de quatre onglets en bas du formulaire Individu : **Notes** (liste à
  deux colonnes avec résolution des pointeurs `@N..@` via `set_note_resolver`
  et lien cliquable), **Textes**, **Propriétés**, **Occupations** ;
- ajout de quatre onglets en bas du formulaire Famille : **Enfants**,
  **Sources** et **Notes** en liste à deux colonnes (nom/titre, identifiant),
  **Événements** en liste simple ;
- réinitialisation automatique du champ de filtre de recherche lors du
  changement de type d’entité, pour éviter un filtre resté affiché mais
  incohérent avec la liste courante.

### Bénéfices des onglets

- présentation homogène (nom/titre + identifiant) pour toutes les listes de
  références GEDCOM dans les deux formulaires principaux ;
- navigation plus fiable vers les notes et sources référencées ;
- expérience de recherche plus prévisible entre deux types d’entités.

## Priorité 3 — gérer les gros GEDCOM plus proprement

### État de la performance

En cours — la recherche est optimisée et mesurée, l’historique est borné à 100
entrées et les listes optionnelles des individus sont allouées à la demande.
L’empreinte durable des lignes brutes, index et modèles reste à réduire.

### Objectif performance

Réduire le coût mémoire et améliorer la scalabilité.

### Actions performance

- identifier les points de chargement en mémoire complète ;
- partager les chaînes des lignes brutes entre le parser et les entités ;
- construire les arbres d’événements individuels à la demande ;
- allouer à la demande les listes optionnelles de `Individual` ;
- utiliser des slots sur les objets `Individual` pour réduire leur surcharge ;
- allouer à la demande les listes optionnelles de `Family` et utiliser des slots ;
- allouer à la demande les listes optionnelles de `Source` et utiliser des slots ;
- allouer à la demande les listes optionnelles de `Repository` et utiliser des slots ;
- allouer à la demande les listes optionnelles de `Submitter` et utiliser des slots ;
- allouer à la demande les listes optionnelles de `Note` et utiliser des slots ;
- utiliser des slots et allouer les détails d’`Event` à la demande ;
- utiliser des slots sur les objets `MultimediaObject` ;
- maintenir le benchmark synthétique dans `benchmarks/benchmark_search.py`, avec
  des options pour familles, événements, notes, sources, dépôts, submitters et
  médias ;
- recherche de 100 000 individus : environ 298 ms avec la normalisation Unicode
  complète et 29 ms avec le fast path ASCII ; le dernier pic mémoire mesuré est
  de 67,3 MiB, contre 99,3 MiB avant l’allocation paresseuse des listes ;
- mesure synthétique séparée de 50 000 familles éparses : 19,6 MiB après slots et listes
  paresseuses, contre 41,0 MiB avant ;
- mesure synthétique de 50 000 sources éparses : 16,5 MiB après slots et listes
  paresseuses, contre 32,5 MiB avant ;
- mesure synthétique de 50 000 dépôts épars : 15,2 MiB après slots et listes
  paresseuses, contre 25,9 MiB avant ;
- mesure synthétique de 50 000 submitters épars : 12,2 MiB après slots et listes
  paresseuses, contre 19,9 MiB avant ;
- mesure synthétique de 50 000 notes éparses : 13,6 MiB après slots et listes
  paresseuses, contre 26,5 MiB avant ;
- mesure synthétique de 100 000 événements sans détails : 6,1 MiB après slots et
  détails paresseux, contre 15,3 MiB avant ;
- mesure synthétique de 50 000 objets multimédias : 13,8 MiB après slots, contre
  15,7 MiB avant ;
- mesure combinée reproductible avec 100 000 individus et 50 000 familles : 103,4 MiB ;
- étudier un chargement partiel ou paresseux pour les gros fichiers ;
- conserver une API stable pour les contrôleurs existants.

### Historique de navigation

L’historique conserve au plus 100 contextes. Les entrées les plus anciennes
sont évincées au-delà de cette limite.

### Bénéfice performance

- meilleure tolérance aux fichiers volumineux ;
- plus d’aisance dans les cas de grande généalogie ;
- réduction des risques de saturation mémoire.

## Priorité 4 — enrichir la validation GEDCOM

### État de la validation

Partiellement couverte : le mode strict détecte les anomalies structurelles,
les références inconnues et certaines références incompatibles avec le type
attendu. La conformité GEDCOM complète reste hors périmètre actuel.

### Objectif validation

Aller au-delà des anomalies structurelles de base.

### Actions validation

- formaliser les règles de validation GEDCOM ;
- distinguer les erreurs de structure et les erreurs de sémantique ;
- exposer des diagnostics plus explicites dans l’interface ;
- étendre la couverture de tests sur les cas non conformes.

### Bénéfice validation

- meilleure fiabilité du chargement ;
- plus de confiance pour les fichiers réels ;
- meilleure qualité des messages utilisateur.

## Priorité 5 — renforcer la robustesse des vues et des références

### Objectif robustesse

Rendre l’application plus stable face aux données incomplètes ou mal formées.

### Actions robustesse

- sécuriser davantage les résolutions de pointeurs ;
- traiter proprement les entités inconnues ou manquantes ;
- normaliser les messages d’erreur autour des liens brisés ;
- augmenter la couverture des scénarios de navigation.

### Bénéfice robustesse

- moins de bugs sur les fichiers hétérogènes ;
- meilleure expérience dans les cas limites ;
- plus de confiance sur les liens internes.

## Priorité 6 — automatiser la qualité du projet

### CI en place

Workflow configuré dans `.github/workflows/ci.yml` : tests Tkinter sous Xvfb,
compilation syntaxique, contrôle Black et build PyInstaller sur Ubuntu 24.04.
Le premier résultat d’exécution sur GitHub Actions reste à confirmer.

### Objectif automatisation

Rendre les validations reproductibles pour les futures évolutions.

### Actions automatisation

- conserver la CI à jour avec les dépendances et versions Python supportées ;
- vérifier que le build PyInstaller reste exécutable sur les plateformes visées ;
- documenter les conventions de développement.

## Plan d’exécution recommandé

1. Mesurer puis réduire l’empreinte mémoire des gros GEDCOM, en évaluant le
  chargement paresseux.
2. Définir et tester les prochaines règles de validation GEDCOM.
3. Confirmer le premier passage CI sous Xvfb sur GitHub Actions.
4. Extraire d’autres responsabilités de `ui/main_window.py` selon les besoins.

## Conclusion

Le chargement asynchrone est stabilisé et couvert par les tests. La recherche est
plus rapide sans index mémoire persistant. Les prochains travaux portent sur la
mémoire des gros fichiers, la validation GEDCOM et la confirmation du workflow CI.
