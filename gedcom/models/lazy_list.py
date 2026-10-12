class _LazyList:
    def __set_name__(self, owner, name):
        self.storage_name = f"_{name}"

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        value = getattr(instance, self.storage_name)
        if value is None:
            value = []
            setattr(instance, self.storage_name, value)
        return value

    def __set__(self, instance, value):
        setattr(instance, self.storage_name, value if value else None)
