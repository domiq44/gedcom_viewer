# Formats et limites

## Lecture et encodage

Les fichiers sont décodés en UTF-8, avec ou sans BOM. En mode strict, la
présence et la non-vacuité de `HEAD.CHAR` sont vérifiées, mais sa valeur ne
choisit pas le décodeur : GEDCOM 5.5.1 définit `CHAR` avec des valeurs telles
que `ANSEL`, `ANSI`, `ASCII` ou `UTF-8`, mais l'application ne décode qu'en
UTF-8 et ne gère ni l'encodage ANSEL, ni l'encodage ANSI. Les séquences qui ne
sont pas valides en UTF-8 sont remplacées ; leur nombre est signalé dans le
journal. Les espaces répétés dans les valeurs sont préservés.

## Validation stricte

Le mode strict contrôle notamment la structure des lignes et des enregistrements,
les pointeurs requis, les références connues et certains contextes de tags. Pour
un en-tête déclaré GEDCOM 5.5.1, il vérifie aussi la présence, l'unicité et la
validité de `HEAD.SOUR`, `HEAD.CHAR` et `HEAD.SUBM`, ainsi que plusieurs règles
sur `HEAD.GEDC`, `VERS` et `FORM`. Il contrôle également les niveaux ASCII
canoniques, la première ligne de niveau 0, les valeurs `SEX`, les formats de
dates courants et les cardinalités principales des enregistrements `INDI`, `FAM`,
`REPO` et `SUBM`.

Cette validation reste ciblée et ne garantit pas la conformité complète au
standard GEDCOM. Elle ne contrôle pas la hiérarchie interne de tous les tags ni
toutes les cardinalités fines du standard. En mode tolérant, les anomalies sont
signalées dans le journal et le chargement continue lorsque c'est possible. Le
rapport d'erreurs est borné à 1000 entrées, suivies d'un message de troncature,
pour éviter des journaux démesurés sur les fichiers très malformés.

## Mémoire

Le fichier est chargé intégralement en mémoire. Les données optionnelles et
certains arbres d'événements sont construits à la demande pour réduire les
allocations initiales, mais la mémoire nécessaire augmente avec la taille du
GEDCOM. Utilise le [benchmark](BENCHMARKS.md) sur tes propres fichiers pour
mesurer leur coût dans ton environnement.
