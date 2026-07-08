import math

from data_table import DataTable


class Levels(DataTable):
    _structure = {  # attr_name: (start, length, method)
        # range(0, 96, 6) ???
        "MIX-01": (96, 6, "setting"),
        "MIX-02": (102, 6, "setting"),
        "MIX-03": (108, 6, "setting"),
        "MIX-04": (114, 6, "setting"),
        "MIX-05": (120, 6, "setting"),
        "MIX-06": (126, 6, "setting"),
        "MIX-07": (132, 6, "setting"),
        "MIX-08": (138, 6, "setting"),
        "MIX-09": (144, 6, "setting"),
        "MIX-10": (150, 6, "setting"),
        "MIX-11": (156, 6, "setting"),
        "MIX-12": (162, 6, "setting"),
        # 168, 174, 180, 186 TBD - possibly the other stereo outputs
        "MAINLR": (192, 6, "setting"),
        # 198-210 ???
        "FX-01": (210, 6, "setting"),
        "FX-02": (216, 6, "setting"),
        "FX-03": (222, 6, "setting"),
        "FX-04": (228, 6, "setting"),
        # 234-300 ???
    }
    def __init__(self, data, parent=None, **kwargs):
        super().__init__(data, parent=parent, **kwargs)
        # for key, value in kwargs.items():
        #     setattr(self, key, value)
        pass

    def setting(self, segment):
        # fader position in dB
        fader_position = round((self.signed_int(segment[:2], "little", False) - 0x8000) / 256, 1)
        # pan position in arbitrary units - max left: -37, centre: 0, max right: 37
        pan_position = self.signed_int(segment[2:4], "little", False) - 37
        return {"position": fader_position, "pan": pan_position, "type?": segment[4:]}