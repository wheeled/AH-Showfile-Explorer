

from data_table import DataTable


class Effect(DataTable):
    _structure = {
        "name": (2, 20, "cleanup"),
    }
    def __init__(self, data, parent=None):
        super().__init__(data, parent=parent)
