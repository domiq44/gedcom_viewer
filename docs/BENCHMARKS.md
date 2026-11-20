# Performances et benchmarks

## Comportement du parseur

Le parseur construit une seule fois les tuples `(niveau, pointeur, tag, valeur)`
et les réutilise pour l'indexation et la validation. Les modèles exposent leurs
champs optionnels via des collections paresseuses. Les grandes listes et arbres
restent proportionnels à la taille du fichier.

## Mesures

Le benchmark mesure :

- le temps de chargement ;
- le temps de recherche, rapporté en médiane et p95 ;
- les allocations Python suivies par `tracemalloc` ;
- la mémoire résidente maximale via `getrusage`.

Les allocations suivies ne représentent pas toute la mémoire résidente du
processus et les temps dépendent de la machine.

## Scénarios synthétiques

Lancer les scénarios par défaut (10 000, 50 000 et 100 000 individus) :

```bash
python3 benchmarks/benchmark_search.py
```

Les seuils de dépassement sont facultatifs ; quand ils sont fournis, le
benchmark renvoie un code de sortie non nul :

| Option | Garde-fou |
| --- | --- |
| `--max-load-seconds` | Temps de chargement maximal |
| `--max-search-median-ms` | Médiane de recherche maximale |
| `--max-rss-mib` | Mémoire résidente maximale |

La CI mesure les tailles 20 000, 50 000 et 100 000 individus avec des seuils
de 30 s de chargement, 2 000 ms de médiane de recherche et 2 048 MiB de RSS.
Ces valeurs offrent une marge confortable sur les exécuteurs standards et
détectent une régression d'un ordre de grandeur.

Mesurer un fichier existant sans afficher son chemin ni ses valeurs GEDCOM :

```bash
python3 benchmarks/benchmark_search.py --file /path/to/family.ged --repeats 1
```

Ajouter des familles ou des enregistrements auxiliaires :

```bash
python3 benchmarks/benchmark_search.py --sizes 100000 --families 50000 --repeats 1
python3 benchmarks/benchmark_search.py --sizes 10000 --other-entities 10000 --events-per-source 2 --repeats 1
```

Générer un GEDCOM de benchmark représentatif :

```bash
python3 benchmarks/generate_gedcom.py --output /tmp/gedcom-benchmark.ged --individuals 2000
```

## Options de données synthétiques

| Option | Données ajoutées |
| --- | --- |
| `--families` | Nombre de familles reliées aux individus |
| `--other-entities` | Ce nombre d'enregistrements `NOTE`, `SOUR`, `REPO`, `SUBM` et `OBJE` |
| `--texts-per-individual`, `--notes-per-individual` | Textes ou notes avec continuation |
| `--occupations-per-individual`, `--properties-per-individual` | Occupations datées ou tags `PROP` |
| `--fams-per-individual`, `--obje-per-individual` | Références aux familles ou médias ; nécessitent respectivement `--families` ou `--other-entities` |
| `--events-per-family`, `--events-per-source` | Événements familiaux `MARR` ou événements `DATA/EVEN` dans les sources |
| `--metadata-per-source` | Notes, références `SOUR` et `REFN` ; nécessite `--other-entities` |

`--file` ne peut pas être combiné avec les options qui génèrent des données
synthétiques. `--query` et `--repeats` permettent de régler la recherche
mesurée ; consulte `python3 benchmarks/benchmark_search.py --help` pour la liste
complète des paramètres.
