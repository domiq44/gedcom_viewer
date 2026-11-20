# Construction de l'exécutable

Construire une version autonome avec PyInstaller :

```bash
make dist
```

Le résultat est placé dans `dist/`. UPX est désactivé par défaut pour éviter une
dépendance externe et garder des builds reproductibles ; active-le avec
`GEDCOM_VIEWER_UPX=1` si UPX est installé et supporté par la cible.

Après construction, le smoke-test valide le démarrage de l'artefact :

```bash
make smoke
```

Les tests ne sont pas embarqués dans l'exécutable.
