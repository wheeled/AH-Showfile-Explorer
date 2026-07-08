import os

from data_table import DataTable


class Asset(DataTable):
    _structure = {
        'name': (20, 16, "cleanup"),
    }
    def __init__(self, filename, path):
        self.filename = filename
        self.path = path
        if not self.filename.upper().startswith(self.name_expected):
            raise ValueError(f"Invalid filename - expected name to start with '{self.name_expected}'")
        self.data = self.readfile()
        self.parse()

    @property
    def name_expected(self):
        if self.__class__.__name__ == "Library":
            return "LIB"
        else:
            return self.__class__.__name__.upper()

    def readfile(self):
        filepath = os.path.join(self.path, self.filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)
        with open(filepath, 'rb') as f:
            return f.read()



