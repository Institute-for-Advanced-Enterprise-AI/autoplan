import inspect


class Dependency:
    def __init__(self):
        self.item = None

    def __str__(self):
        return f"Dependency with item: {self.item}"

    def set(self, item):
        self.item = item
        for name, value in inspect.getmembers(item, callable):
            if not hasattr(self, name):
                setattr(self, name, value)
