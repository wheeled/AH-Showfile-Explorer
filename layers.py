from data_table import DataTable


class Layer(DataTable):
    _structure = {}
    def __init__(self, data, parent=None, **kwargs):
        super().__init__(data, parent=parent, **kwargs)
        # for key, value in kwargs.items():
        #     setattr(self, key, value)
        self.lineup = [LayerChannel(self.data[n:n + 3], parent=self) for n in range(0, len(self.data), 3)]
        pass


class LayerChannel(DataTable):
    _structure = {
        "active": (0, 1, "bool"),
        "name": (1, 1, "lookup_name"),
        "unk2": (2, 1, "uint"),
    }
    def __init__(self, data, parent=None, **kwargs):
        super().__init__(data, parent=parent, **kwargs)
        # for key, value in kwargs.items():
        #     setattr(self, key, value)
        pass

    def lookup_name(self, segment):
        if not self.active:
            return ""
        else:
            try:
                return self.parent.parent.channel_names[segment[0]]
            except IndexError:
                pass
