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

En cours — les arbres d’événements et plusieurs champs optionnels (`NOTE`,
`TEXT`, `OCCU`, `PROP`, références `FAMS`/`OBJE`, événements familiaux et
événements `SOUR.DATA`) sont construits
à la demande. Les benchmarks mesurent maintenant ces familles de données.
L’empreinte des lignes brutes, des index et des modèles principaux reste le
chantier le plus important : le fichier GEDCOM est toujours chargé intégralement
en mémoire.

### Objectif performance

Réduire le coût mémoire et améliorer la scalabilité.

### Optimisations réalisées

- partage des lignes brutes du parser avec les entités ;
- arbres d’événements individuels et détails d’événement différés ;
- données optionnelles des modèles extraites à la demande, notamment
  `Individual` (`NOTE`, `TEXT`, `OCCU`, `PROP`, `FAMS`, `OBJE`), `Family` et
  `Source` ;
- slots sur les modèles volumineux et listes optionnelles paresseuses ;
- benchmark synthétique étendu aux familles, aux événements source, aux notes,
  textes, occupations, propriétés et références individuelles, ainsi qu’aux
  autres types d’entités ; il affiche la mémoire après chargement puis le delta
  après consultation de toutes les propriétés différées.

### Mesures synthétiques récentes

- sur 10 000 individus et 10 000 familles contenant 20 000 événements, la
  mémoire mesurée est passée de 16,5 à 14,7 MiB après différé des objets
  d’événement familiaux ;
- sur 10 000 modèles `Source`, l’accès aux événements ajoute 5,34 MiB dans une
  mesure isolée ;
- sur 10 000 modèles `Individual`, l’accès aux textes ajoute 1,74 MiB, et
  l’accès à deux occupations datées et une propriété ajoute 7,56 MiB dans des
  mesures isolées ;
- l’accès aux notes ajoute 2,59 MiB pour 10 000 modèles `Individual` dans une
  mesure synthétique isolée ;
- l’accès à deux références `FAMS` et deux références `OBJE` ajoute 3,52 MiB
  pour 10 000 modèles `Individual` dans une mesure synthétique isolée ;
- scénario combiné de 10 000 individus, 5 000 familles et 1 000 enregistrements
  de chaque autre type : 20,6 MiB après chargement, puis 34,7 MiB supplémentaires
  après accès aux données optionnelles ; ce delta comprend aussi les listes vides
  matérialisées et varie selon les données générées ;
- ces mesures synthétiques illustrent les allocations différées et ne
  représentent pas la consommation totale d’un gros fichier réel ;
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
- étudier la réduction des allocations des lignes brutes et index, ou une
  représentation partielle/mappée, sans perdre l’accès aux blocs GEDCOM bruts ;
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
attendu. Il vérifie également l’ordre et l’unicité de `HEAD`/`TRLR`, leur niveau
et l’absence de pointeur ou de valeur, les lignes vides et les sous-lignes de
`TRLR`. La conformité GEDCOM complète reste hors périmètre actuel.

### Objectif validation

Aller au-delà des anomalies structurelles de base.

### Actions validation

- formaliser les règles de validation par version GEDCOM ;
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
La dernière suite locale vérifiée passe 175 tests et Black passe sur les chemins
CI. Une action GitHub a été rapportée verte après le correctif Black, mais
l’exécution sur les commits les plus récents reste à confirmer.

### Objectif automatisation

Rendre les validations reproductibles pour les futures évolutions.

### Actions automatisation

- conserver la CI à jour avec les dépendances et versions Python supportées ;
- vérifier que le build PyInstaller reste exécutable sur les plateformes visées ;
- documenter les conventions de développement.

## Plan d’exécution recommandé

1. Mesurer puis réduire le coût des lignes brutes et index pour les gros GEDCOM.
2. Formaliser les prochaines règles de validation GEDCOM par version.
3. Confirmer l’action GitHub sur les commits les plus récents.
4. Extraire d’autres responsabilités de `ui/main_window.py` selon les besoins.

## Conclusion

Le chargement asynchrone est stabilisé et couvert par les tests. Plusieurs
structures métier optionnelles sont maintenant différées, mais les lignes brutes
et les index maintiennent une empreinte mémoire proportionnelle au fichier. Les
prochains travaux portent sur cette représentation, la validation GEDCOM par
version et la confirmation de la CI sur les changements récents.
