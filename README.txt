Méthode 1 : Utiliser venv (La méthode standard en Python 3)

C'est la méthode recommandée par la documentation Python.
Le module venv est inclus dans la bibliothèque standard de Python.

Commande à exécuter dans le terminal, à la racine de votre projet :

    python3 -m venv .venv

Explication :

    python3 : Assurez-vous d'appeler l'interpréteur Python que vous souhaitez utiliser.
    -m venv : Indique à Python d'exécuter le module venv.
    .venv : C'est le nom du répertoire que vous voulez créer. Le point (.) le rend caché, ce qui est la convention pour les environnements virtuels.

Que fait cette commande ?
Elle crée un dossier nommé .venv/ contenant une copie minimaliste de l'interpréteur Python, ainsi que les scripts nécessaires pour gérer les paquets installés spécifiquement pour ce projet.
Comment activer l'environnement après sa création ?

Une fois créé, vous devez l'activer pour que votre terminal utilise les paquets de cet environnement au lieu de ceux du système :

Sur macOS/Linux :

    source .venv/bin/activate

Sur Windows (Command Prompt) :

    .venv\Scripts\activate.bat

Sur Windows (PowerShell) :

    .venv\Scripts\Activate.ps1

