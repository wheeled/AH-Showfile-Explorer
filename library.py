# library.py
from asset import Asset


class Library(Asset):
    _structure = {
        'name': (0x170, 8, "cleanup"),  # not certain of the length
    }
    def __init__(self, filename, path, format="SQ"):
        super().__init__(filename, path)
        if format == "QU":
            # QU files only support name parsing for now
            self._structure["name"] = (0x1e8, 8, "cleanup")
            self.parse()
        else:
            pass


