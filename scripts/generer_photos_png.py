#!/usr/bin/env python3
"""Génère les 56 images PNG photo_individu1.png .. photo_individu56.png.

Chaque image (400x400) contient :
- un fond de couleur unique (palette de 52 couleurs qui se repete),
- un disque blanc centré dans la partie haute de l'image,
- le numero de l'individu ecrit au centre du disque, de la couleur du fond,
- le libelle "Individu X" en blanc, inscrit sous le disque.

Les fichiers sont ecrits dans le repertoire passe en argument (par defaut /tmp/).
Ce script rend scripts/lancer_pour_capture.sh autonome.
"""

from __future__ import annotations

import os
import sys
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit(
        "Pillow est requis pour generer les photos: pip install Pillow"
    ) from exc

WIDTH = 400
HEIGHT = 400
CENTER_X = WIDTH // 2

# --- Geometrie du disque (partie haute de l'image) ---
DISQUE_CENTRE_X = CENTER_X
DISQUE_CENTRE_Y = 160  # centre vertical du disque (dans la partie haute)
DISQUE_RAYON = 110  # diamètre 220 px, laisse de la place en dessous
DISQUE_COULEUR = (255, 255, 255)  # blanc

# --- Zone du texte "Individu X" (sous le disque) ---
TEXTE_COULEUR = (255, 255, 255)  # blanc
TEXTE_Y = DISQUE_CENTRE_Y + DISQUE_RAYON + 25  # juste sous le disque

# --- Chiffre (dans le disque, couleur du fond pour contraste) ---
CHIFFRE_TAILLE = int(DISQUE_RAYON * 0.7)  # bien contenu dans le disque
LIBELLE_TAILLE = 30

# Palette des 52 couleurs de fond (extraite des PNG de reference).
# L'individu N utilise la couleur palette[(N-1) % 52].
PALETTE_FOND = [
    (255, 100, 100),  # 1
    (100, 150, 255),  # 2
    (100, 255, 100),  # 3
    (255, 255, 100),  # 4
    (255, 100, 255),  # 5
    (100, 255, 255),  # 6
    (200, 100, 255),  # 7
    (255, 150, 50),  # 8
    (50, 200, 100),  # 9
    (200, 50, 50),  # 10
    (150, 100, 255),  # 11
    (255, 200, 50),  # 12
    (50, 255, 200),  # 13
    (200, 50, 100),  # 14
    (255, 100, 150),  # 15
    (100, 200, 50),  # 16
    (200, 200, 50),  # 17
    (50, 150, 255),  # 18
    (255, 50, 200),  # 19
    (150, 255, 50),  # 20
    (255, 150, 100),  # 21
    (100, 100, 255),  # 22
    (255, 50, 50),  # 23
    (50, 255, 50),  # 24
    (50, 50, 255),  # 25
    (255, 255, 50),  # 26
    (255, 100, 50),  # 27
    (100, 255, 150),  # 28
    (150, 50, 255),  # 29
    (200, 255, 50),  # 30
    (50, 200, 255),  # 31
    (255, 200, 100),  # 32
    (100, 255, 50),  # 33
    (255, 50, 150),  # 34
    (150, 150, 255),  # 35
    (255, 100, 200),  # 36
    (50, 255, 100),  # 37
    (200, 100, 255),  # 38
    (255, 150, 50),  # 39
    (100, 200, 255),  # 40
    (255, 50, 100),  # 41
    (50, 150, 100),  # 42
    (100, 255, 200),  # 43
    (200, 50, 200),  # 44
    (255, 200, 50),  # 45
    (50, 200, 150),  # 46
    (150, 255, 100),  # 47
    (100, 50, 255),  # 48
    (255, 100, 50),  # 49
    (50, 100, 255),  # 50
    (200, 255, 100),  # 51
    (100, 150, 50),  # 52
]

FONT_PATHS = [
    "/usr/share/fonts/google-carlito-fonts/Carlito-Bold.ttf",
    "/usr/share/fonts/google-droid-sans-fonts/DroidSans-Bold.ttf",
    "/usr/share/fonts/adwaita-sans-fonts/AdwaitaSans-Regular.ttf",
]


def _charger_police(taille: int) -> Any:
    """Charge la premiere police TrueType disponible a la taille donnee."""
    for path in FONT_PATHS:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, taille)
            except OSError:
                continue
    return ImageFont.load_default()


def generer_photo(chemin: str, numero: int) -> None:
    """Genere une image PNG : fond colore, disque blanc, chiffre et libelle."""
    fond = PALETTE_FOND[(numero - 1) % len(PALETTE_FOND)]
    image = Image.new("RGB", (WIDTH, HEIGHT), fond)
    draw = ImageDraw.Draw(image)

    # --- 1. Disque blanc (partie haute) ---
    x0 = DISQUE_CENTRE_X - DISQUE_RAYON
    y0 = DISQUE_CENTRE_Y - DISQUE_RAYON
    x1 = DISQUE_CENTRE_X + DISQUE_RAYON
    y1 = DISQUE_CENTRE_Y + DISQUE_RAYON
    draw.ellipse([x0, y0, x1, y1], fill=DISQUE_COULEUR)

    # --- 2. Chiffre au centre du disque (couleur du fond) ---
    # anchor="mm" = middle-middle : le texte est centre exactement sur le
    # point (DISQUE_CENTRE_X, DISQUE_CENTRE_Y), independamment de la baseline.
    police_chiffre = _charger_police(CHIFFRE_TAILLE)
    draw.text(
        (DISQUE_CENTRE_X, DISQUE_CENTRE_Y),
        str(numero),
        fill=fond,
        font=police_chiffre,
        anchor="mm",
    )

    # --- 3. Libelle "Individu X" en dessous du disque (blanc) ---
    police_libelle = _charger_police(LIBELLE_TAILLE)
    draw.text(
        (CENTER_X, TEXTE_Y),
        f"Individu {numero}",
        fill=TEXTE_COULEUR,
        font=police_libelle,
        anchor="ma",  # middle-top : centre horizontalement, aligne en haut
    )

    image.save(chemin, format="PNG")


def main() -> int:
    """Genere les 56 photos PNG dans le repertoire cible."""
    repertoire = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    os.makedirs(repertoire, exist_ok=True)
    for i in range(1, 57):
        chemin = os.path.join(repertoire, f"photo_individu{i}.png")
        generer_photo(chemin, i)
    print("56 photo(s) PNG generee(s) dans", repertoire)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
