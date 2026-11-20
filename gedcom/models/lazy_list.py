"""Liste paresseuse pour les champs optionnels des modèles."""


class _LazyList:
    """Descripteur de liste paresseuse pour les champs optionnels."""

    def __set_name__(self, owner, name):
        """Mémorise le nom de stockage de l'attribut hôte."""
        self.storage_name = f"_{name}"

    def __get__(self, instance, owner=None):
        """Retourne la liste, créée au premier accès."""
        if instance is None:
            return self
        value = getattr(instance, self.storage_name)
        if value is None:
            value = []
            setattr(instance, self.storage_name, value)
        return value

    def __set__(self, instance, value):
        """Définit la liste (None pour réinitialiser)."""
        setattr(instance, self.storage_name, value if value else None)
