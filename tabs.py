

from data_table import DataTable


class Tab(DataTable):
    _structure = {
        "name": (0, 5, "cleanup"),
    }
    def __init__(self, data, parent=None):
        super().__init__(data, parent=parent)
