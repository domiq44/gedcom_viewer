#!/bin/bash
set -e

# Generateur de fichier GEDCOM de test pour les captures d'ecran de l'arbre
# d'ascendance. Construit un fichier a 7 generations (56 individus) avec une
# photo associee a chaque individu (OBJE @OX@ -> photo_individuX.png). Le
# fichier est ecrit dans /tmp/test_arbre_ascendance.ged et l'application est
# ensuite lancee pour capture manuelle.
#
# Les 56 photos PNG sont generees automatiquement dans /tmp/ par
# scripts/generer_photos_png.py avant la creation du GEDCOM.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GEDCOM_FILE="/tmp/test_arbre_ascendance.ged"

# --- Generation des photos PNG (56 fichiers photo_individuX.png dans /tmp/) ---
python3 "$PROJECT_DIR/scripts/generer_photos_png.py" /tmp

# --- Fonctions de construction GEDCOM ---

# Ecrit un enregistrement OBJE (objet multimedia) avec titre et fichier image.
# $1 = pointeur OBJE (ex: @O1@)
# $2 = titre
# $3 = fichier image
ecrire_objet_multimedia() {
    echo "0 $1 OBJE"
    echo "1 TITL $2"
    echo "1 FILE $3"
    echo "1 FORM PNG"
}

# Ecrit un enregistrement INDI (individu) avec ses champs optionnels.
# $1 = pointeur INDI (ex: @I1@)
# $2 = nom (GEDCOM avec /surnom/)
# $3 = sexe (M/F)
# $4 = date naissance (ou vide)
# $5 = date deces (ou vide)
# $6 = FAMC (ou vide)
# $7 = FAMS (ou vide)
# $8 = OBJE pointeur (ou vide)
ecrire_individu() {
    echo "0 $1 INDI"
    echo "1 NAME $2"
    echo "1 SEX $3"
    if [ -n "$4" ]; then echo "1 BIRT"; echo "2 DATE $4"; fi
    if [ -n "$5" ]; then echo "1 DEAT"; echo "2 DATE $5"; fi
    if [ -n "$6" ]; then echo "1 FAMC $6"; fi
    if [ -n "$7" ]; then echo "1 FAMS $7"; fi
    if [ -n "$8" ]; then echo "1 OBJE $8"; fi
}

# Ecrit un enregistrement FAM (famille) avec ses epoux et sa date de mariage.
# $1 = pointeur FAM (ex: @F1@)
# $2 = mari (ou vide)
# $3 = femme (ou vide)
# $4 = date mariage (ou vide)
ecrire_famille() {
    echo "0 $1 FAM"
    if [ -n "$2" ]; then echo "1 HUSB $2"; fi
    if [ -n "$3" ]; then echo "1 WIFE $3"; fi
    if [ -n "$4" ]; then echo "1 MARR"; echo "2 DATE $4"; fi
}

echo "=== Génération du fichier GEDCOM de test ==="

cat > "$GEDCOM_FILE" << 'GEDCOM_HEADER'
0 HEAD
1 SOUR GEDCOM_VIEWER
2 NAME GEDCOM Viewer Test
2 VERSION 1.0
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
1 SUBM @S1@
1 DATE 19 NOV 2026
0 @S1@ SUBM
1 NAME Dominique Test
1 CHAN
2 DATE 1 JAN 2020
GEDCOM_HEADER

# Tout ce qui suit est ajoute au fichier GEDCOM.
exec >> "$GEDCOM_FILE"

# --- Génération 0 (racine) ---
ecrire_individu  "@I1@"  "Individu /1/" F "15 APR 1950" ""   "@F1@" "@F8@" "@O1@"

# --- Génération 1 (parents de I1) ---
ecrire_individu  "@I2@"  "Individu /2/" M "5 MAY 1945" "10 JAN 2010" "@F2@" "@F1@" "@O2@"
ecrire_individu  "@I3@"  "Individu /3/" F "20 JUN 1952" "15 SEP 2015" "@F3@" "@F1@" "@O3@"
ecrire_famille   "@F1@" "@I2@" "@I3@" "1 JAN 1970"

# --- Génération 2 (grands-parents de I1) ---
ecrire_individu  "@I4@"  "Individu /4/" M "12 MAR 1920" "3 JUL 1985" "@F4@" "@F2@" "@O4@"
ecrire_individu  "@I5@"  "Individu /5/" F "8 NOV 1922" ""       "@F5@" "@F2@" "@O5@"
ecrire_individu  "@I6@"  "Individu /6/" M "25 DEC 1918" "14 FEB 1990" "@F5@" "@F3@" "@O6@"
ecrire_individu  "@I7@"  "Individu /7/" F "30 APR 1925" "22 MAY 2005" ""   "@F3@" "@O7@"
ecrire_famille   "@F2@" "@I4@" "@I5@" "15 JUN 1945"
ecrire_famille   "@F3@" "@I6@" "@I7@" "10 SEP 1948"

# --- Génération 3 (arrière-grands-parents de I1) ---
ecrire_individu  "@I8@"  "Individu /8/" M "2 FEB 1895" "5 JAN 1970"  "@F9@" "@F4@" "@O8@"
ecrire_individu  "@I9@"  "Individu /9/" F "14 JUL 1898" "12 AUG 1975" ""    "@F4@" "@O9@"
ecrire_individu  "@I10@" "Individu /10/" M "8 MAY 1890" "3 MAR 1965" "@F13@" "@F5@" "@O10@"
ecrire_individu  "@I11@" "Individu /11/" F "22 OCT 1893" "30 SEP 1980" ""    "@F5@" "@O11@"
ecrire_individu  "@I12@" "Individu /12/" M "" "15 NOV 1955"   "" "@F6@" "@O12@"
ecrire_individu  "@I13@" "Individu /13/" F "" "8 APR 1958"     "" "@F6@" "@O13@"
ecrire_individu  "@I14@" "Individu /14/" M "2 FEB 1895" "22 JAN 1960" "" "@F7@" "@O14@"
ecrire_individu  "@I15@" "Individu /15/" F "14 JUL 1898" "30 SEP 1980" "" "@F7@" "@O15@"
ecrire_famille   "@F4@" "@I8@" "@I9@" "1915"
ecrire_famille   "@F5@" "@I10@" "@I11@" "1912"
ecrire_famille   "@F6@" "@I12@" "@I13@" "1905"
ecrire_famille   "@F7@" "@I14@" "@I15@" "1908"

# --- Génération 4 (5ème génération visible) ---
ecrire_individu  "@I19@" "Individu /19/" M "10 JAN 1865" "15 MAR 1930" "@F11@" "@F9@" "@O19@"
ecrire_individu  "@I20@" "Individu /20/" F "22 SEP 1870" "10 NOV 1945" "@F12@" "@F9@" "@O20@"
ecrire_individu  "@I27@" "Individu /27/" M "2 FEB 1865" "15 JAN 1930" "@F14@" "@F13@" "@O27@"
ecrire_individu  "@I28@" "Individu /28/" F "14 JUL 1870" "12 AUG 1940" "@F15@" "@F13@" "@O28@"
ecrire_famille   "@F9@" "@I19@" "@I20@" "1890"
ecrire_famille   "@F13@" "@I27@" "@I28@" "1890"

# --- Génération 5 (parents de I19/I20 et I27/I28) ---
ecrire_individu  "@I21@" "Individu /21/" M "5 MAY 1885" "20 JAN 1950" "" "@F10@" "@O21@"
ecrire_individu  "@I22@" "Individu /22/" F "15 AUG 1890" "5 JUL 1960" "" "@F10@" "@O22@"
ecrire_individu  "@I23@" "Individu /23/" M "20 JAN 1835" "5 NOV 1910" "" "@F11@" "@O23@"
ecrire_individu  "@I24@" "Individu /24/" F "8 APR 1840" "12 JUL 1920" "" "@F11@" "@O24@"
ecrire_individu  "@I25@" "Individu /25/" M "15 MAR 1840" "30 SEP 1905" "" "@F12@" "@O25@"
ecrire_individu  "@I26@" "Individu /26/" F "22 JUL 1845" "8 JAN 1925" "" "@F12@" "@O26@"
ecrire_individu  "@I29@" "Individu /29/" M "20 JAN 1835" "5 NOV 1910" "" "@F14@" "@O29@"
ecrire_individu  "@I30@" "Individu /30/" F "8 APR 1840" "12 JUL 1920" "" "@F14@" "@O30@"
ecrire_individu  "@I31@" "Individu /31/" M "15 MAR 1840" "30 SEP 1905" "" "@F15@" "@O31@"
ecrire_individu  "@I32@" "Individu /32/" F "22 JUL 1845" "8 JAN 1925" "" "@F15@" "@O32@"
ecrire_famille   "@F10@" "@I21@" "@I22@" "1905"
ecrire_famille   "@F11@" "@I23@" "@I24@" "1860"
ecrire_famille   "@F12@" "@I25@" "@I26@" "1865"
ecrire_famille   "@F14@" "@I29@" "@I30@" "1860"
ecrire_famille   "@F15@" "@I31@" "@I32@" "1865"

# --- Générations 6 et 7 (parents des générations 5) ---
ecrire_individu  "@I33@" "Individu /33/" M "10 JAN 1810" "20 MAR 1880" "" "@F16@" "@O33@"
ecrire_individu  "@I34@" "Individu /34/" F "15 APR 1815" "5 JUL 1885" "" "@F16@" "@O34@"
ecrire_individu  "@I35@" "Individu /35/" M "3 MAY 1820" "10 SEP 1890" "" "@F17@" "@O35@"
ecrire_individu  "@I36@" "Individu /36/" F "22 OCT 1825" "30 JAN 1895" "" "@F17@" "@O36@"
ecrire_individu  "@I37@" "Individu /37/" M "8 FEB 1818" "14 JUN 1882" "" "@F18@" "@O37@"
ecrire_individu  "@I38@" "Individu /38/" F "30 NOV 1822" "18 DEC 1888" "" "@F18@" "@O38@"
ecrire_individu  "@I39@" "Individu /39/" M "25 JUL 1828" "7 APR 1898" "" "@F19@" "@O39@"
ecrire_individu  "@I40@" "Individu /40/" F "12 DEC 1832" "22 FEB 1902" "" "@F19@" "@O40@"
ecrire_famille   "@F16@" "@I33@" "@I34@" "1850"
ecrire_famille   "@F17@" "@I35@" "@I36@" "1852"
ecrire_famille   "@F18@" "@I37@" "@I38@" "1855"
ecrire_famille   "@F19@" "@I39@" "@I40@" "1858"

ecrire_individu  "@I41@" "Individu /41/" M "5 MAR 1785" "3 JAN 1855" "" "@F20@" "@O41@"
ecrire_individu  "@I42@" "Individu /42/" F "18 JUN 1790" "12 MAY 1860" "" "@F20@" "@O42@"
ecrire_individu  "@I43@" "Individu /43/" M "22 OCT 1795" "8 SEP 1865" "" "@F21@" "@O43@"
ecrire_individu  "@I44@" "Individu /44/" F "7 DEC 1800" "30 MAR 1870" "" "@F21@" "@O44@"
ecrire_individu  "@I45@" "Individu /45/" M "14 FEB 1805" "21 JUL 1875" "" "@F22@" "@O45@"
ecrire_individu  "@I46@" "Individu /46/" F "29 APR 1810" "14 NOV 1880" "" "@F22@" "@O46@"
ecrire_individu  "@I47@" "Individu /47/" M "3 SEP 1808" "6 FEB 1878" "" "@F23@" "@O47@"
ecrire_individu  "@I48@" "Individu /48/" F "16 JAN 1812" "28 AUG 1882" "" "@F23@" "@O48@"
ecrire_individu  "@I49@" "Individu /49/" M "8 MAY 1803" "15 MAR 1873" "" "@F24@" "@O49@"
ecrire_individu  "@I50@" "Individu /50/" F "21 NOV 1807" "3 JUL 1877" "" "@F24@" "@O50@"
ecrire_individu  "@I51@" "Individu /51/" M "12 JUL 1800" "25 OCT 1870" "" "@F25@" "@O51@"
ecrire_individu  "@I52@" "Individu /52/" F "3 DEC 1804" "19 JAN 1874" "" "@F25@" "@O52@"
ecrire_individu  "@I53@" "Individu /53/" M "7 APR 1798" "11 DEC 1868" "" "@F26@" "@O53@"
ecrire_individu  "@I54@" "Individu /54/" F "23 OCT 1802" "6 JUN 1872" "" "@F26@" "@O54@"
ecrire_individu  "@I55@" "Individu /55/" M "30 JUN 1806" "22 FEB 1876" "" "@F27@" "@O55@"
ecrire_individu  "@I56@" "Individu /56/" F "14 MAR 1810" "4 SEP 1880" "" "@F27@" "@O56@"
ecrire_famille   "@F20@" "@I41@" "@I42@" "1825"
ecrire_famille   "@F21@" "@I43@" "@I44@" "1828"
ecrire_famille   "@F22@" "@I45@" "@I46@" "1832"
ecrire_famille   "@F23@" "@I47@" "@I48@" "1835"
ecrire_famille   "@F24@" "@I49@" "@I50@" "1838"
ecrire_famille   "@F25@" "@I51@" "@I52@" "1840"
ecrire_famille   "@F26@" "@I53@" "@I54@" "1845"
ecrire_famille   "@F27@" "@I55@" "@I56@" "1848"

# --- Famille de l'individu racine (I1) ---
ecrire_individu  "@I16@" "Individu /16/" M "20 MAR 1948" "" "" "@F8@" "@O16@"
ecrire_individu  "@I17@" "Individu /17/" M "12 JUL 1973" "" "@F8@" "" "@O17@"
ecrire_individu  "@I18@" "Individu /18/" F "3 MAR 1976" "" "@F8@" "" "@O18@"
ecrire_famille   "@F8@" "@I16@" "@I1@" "5 JUN 1972"

# --- Objets multimédia ---
for i in $(seq 1 56); do
    ecrire_objet_multimedia "@O$i@" "Photo Individu $i" "photo_individu$i.png"
done

echo "0 TRLR"

# Supprime les lignes vides.
sed -i '/^$/d' "$GEDCOM_FILE"

echo "Fichier GEDCOM généré : $GEDCOM_FILE"
echo ""
echo "=== Lancement de GEDCOM Viewer ==="
echo "Instructions :"
echo "  1. Dans l'application, ouvrez le fichier : $GEDCOM_FILE"
echo "  2. Allez dans l'onglet 'Arbre d'ascendance' (Ancestor tree)"
echo "  3. Sélectionnez l'individu @I1@ (racine) pour voir l'arbre"
echo "     (5 générations visibles, 6ème génération après clic sur \">\")"
echo "  4. L'individu @I1@ est accompagné de son époux @I16@ et de ses"
echo "     enfants @I17@ et @I18@ dans les vues détaillées"
echo "  5. Sur @I19@, @I20@, @I27@ et @I28@ (5ème génération), un bouton"
echo "     \">\" apparaît car ils ont des parents"
echo "  6. Cliquez sur \">\" pour décaler l'arbre d'une génération vers la gauche"
echo "  7. Faites votre capture d'écran"
echo "  8. Quittez l'application quand vous avez terminé"
echo ""

export DISPLAY="${DISPLAY:-:0}"
python3 "$PROJECT_DIR/main.py"

echo "Application fermée."
