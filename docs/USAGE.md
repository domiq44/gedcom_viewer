# Utilisation

## Ouvrir un fichier

Dans le menu **Fichier** :

- **Ouvrir un fichier GEDCOM** charge le fichier en mode tolérant.
- **Ouvrir et valider un fichier GEDCOM** active le mode strict et refuse le
  fichier si les anomalies prises en charge par le validateur sont détectées.

Les fichiers ouverts depuis la liste des récents sont chargés en mode tolérant.
La fermeture du fichier courant ne quitte pas l'application : les données de la
session et l'historique de navigation sont libérés, mais le fichier reste dans la
liste des récents.

## Navigation et vues

La fenêtre permet de sélectionner un type d'entité, d'ouvrir sa fiche, puis de
suivre les pointeurs cliquables. Le panneau de détail juxtapose les vues
**GEDCOM** et **Fiche** ; leur séparateur vertical peut être déplacé pour régler
leurs largeurs. Les en-têtes et leurs commandes suivent ce séparateur.

« Montrer la vue » et « Montrer GEDCOM » contrôlent séparément les deux panneaux.
La fiche est visible par défaut et les choix sont mémorisés entre les lancements.
Si l'on masque le dernier panneau visible, l'autre s'affiche automatiquement.

Le sélecteur de type mémorise la dernière entité consultée pour chaque type et
restaure sa fiche ainsi que son bloc GEDCOM brut lorsqu'on revient à ce type, y
compris pour chaque occurrence de citation. Cette mémoire est réinitialisée
lorsqu'un autre fichier est chargé ou que le fichier courant est fermé.

## Recherche

La recherche s'applique au type d'entité sélectionné. Elle ignore la casse et
les accents : `cretel` trouve aussi `crétel`, `Crétel` et `Cretel`. La liste est
mise à jour après une courte temporisation afin d'éviter les recalculs à chaque
frappe.

| Type | Champs recherchés |
| --- | --- |
| `INDI` | Pointeur et `NAME` |
| `FAM` | Pointeur et noms des individus `HUSB`, `WIFE` et `CHIL` référencés |
| `SOUR` | Pointeur, `TITL` et pointeur `REPO` du dépôt |
| `CITE` | Pointeur et titre de source, dépôt de la source (`REPO`), fiche associée, contexte et page |
| `REPO` | Pointeur et `NAME` |
| `NOTE` | Pointeur et texte |
| `OBJE` | Pointeur, `TITL` et `FILE` |
| `SUBM` | Pointeur, `NAME` et `EMAIL` |

Les pointeurs sont triés numériquement lorsque c'est possible. Le tri par nom ou
titre dépend des données de l'entité et de ses références.

## Fiches et interactions

Dans les fiches Individu et Famille, les libellés et les valeurs peuvent être
sélectionnés et copiés avec `Ctrl+C`. Les références cliquables s'ouvrent au
clic simple. Les URL `http://` et `https://` présentes dans les notes et les
autres valeurs ouvrent leur adresse dans le navigateur au clic.

Chaque section possède aussi une commande **Copier** qui copie son titre, ses
libellés et ses valeurs. La fiche défile avec la molette de la souris, le
trackpad ou sa barre de défilement.

Les tags GEDCOM standards rencontrés ont des libellés traduits ; les extensions
`_XXX` sont affichées telles quelles. Les autres tags inconnus restent signalés
par « Other GEDCOM ». Les lieux géolocalisés utilisent aussi des libellés dédiés
pour `MAP`, `LATI` et `LONG` dans les fiches Individu et Famille.

Dans la section Événements, les pointeurs vers des individus ou objets
multimédias sont affichés avec leur nom et s'ouvrent au clic simple. Pour un
média, son titre est préféré ; à défaut, le chemin `FILE` est affiché sans
modifier ses séparateurs, qu'il soit au format Linux ou Windows.

Dans la fiche Famille, les tags `TEXT`, `NOTE`, `CONC` et `CONT` d'un mariage ou
d'un divorce sont regroupés en blocs complets, avec les retours à la ligne
conservés.

## Citations

La consultation des citations `n SOUR @...@` (`n > 0`) est limitée aux sources
présentes dans le fichier. Chaque occurrence est listée séparément ; sa fiche
présente la source, la fiche associée, le contexte, la page et les détails. Les
continuations `CONT`/`CONC` du texte sont regroupées et les deux références
restent navigables.

## Multimédia

Les images locales sont prévisualisées avec Pillow et la première page des PDF
avec PDFium, lorsqu'il est disponible. Les aperçus sont confinés au répertoire
du fichier GEDCOM, limités aux extensions d'image ou de PDF prises en charge et
bornés en taille ; sans PDFium, les PDF affichent un aperçu indisponible.

## Thèmes et langues

L'interface est disponible en anglais, français, espagnol, allemand, italien et
portugais. L'anglais est la langue par défaut ; un changement de langue prend
effect au redémarrage.

Les thèmes clair et sombre sont sélectionnables dans le menu `Aide > Thème` et
appliqués à l'exécution ; le choix est mémorisé avec les préférences.

Les données conservées par l'application sont décrites dans
[Préférences](PREFERENCES.md).
