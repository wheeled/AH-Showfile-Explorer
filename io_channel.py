import math

from data_table import DataTable


"""
col_sch = [[
    ch.data[byte] for ch in sc0830.io_channels
    if ch.name in ['MIC 1', 'MIC 2', 'VOX 1', 'VOX 2', 'Room L', 'Room R']]
    for byte in range(len(sc0830.io_channels))]
[(index, array) for index, array in enumerate(col_sch) if all([
    array[0] == array[1], array[1] != array[2], array[2] == array[3]
])]
"""

class IOChannel(DataTable):
    _structure = {  # attr_name: (start, length, method)
        "name": (0, 6, "cleanup"),
        "unk016": (16, 1, "hex"),
        "pad": (17, 1, "bool"),  # wrong
        "phantom_power": (18, 1, "bool"),
        "active": (20, 1, "bool"),
        "unk021": (21, 3, "hex"),
        "channel": (24, 1, "parse_ch"),
        "interface": (26, 1, "parse_if"),
        "unk043": (43, 1, "hex"),
        "unk047": (47, 1, "hex"),
        "unk057": (57, 1, "hex"),
        "unk059": (59, 1, "hex"),
        "unk067": (67, 2, "hex"),
        "unk080": (80, 2, "hex"),
        "hpf_freq": (84, 2, "freq_flt"),  # confirmed
        "unk087": (87, 1, "hex"),  # 0 or 1 - prob hpf_in
        "gate": (92, 32, "parse_gate"),  # confirmed
        "peq": (124, 24, "parse_eq"),  # confirmed
        "compressor": (244, 40, "parse_comp"),
        "unk295": (295, 1, "hex"),  # MIC 1-4 are different
        "unk301": (301, 1, "hex"),  # ???
        "delay": (304, 2, "parse_delay"),  # confirmed
        "group": (316, 1, "uint"),  # group number?  drums 01, band 02
        "unk320": (320, 1, "hex"),  # another group number? drums and band both 02
        "unk324": (324, 2, "hex"),  # ST1, MP3 and PC-USB are different
        "unk328": (328, 1, "hex"),  # 0-87 are 03, 88-103 (outputs) are 02, 104-121 are 03 again
        "unk331": (331, 2, "hex"),  #
        "end": (333, 3, "hex"),
    }
    def __init__(self, data, parent=None):
        super().__init__(data, parent=parent)

    def parse_delay(self, segment):
        return round(self.uint(segment) / 96, 2)

    @staticmethod
    def parse_ch(segment):
        return ord(segment) + 1

    def parse_comp(self, segment):
        return Compressor(segment, parent=self)

    def parse_eq(self, segment):
        return ParametricEQ(segment, parent=self)

    def parse_gate(self, segment):
        return Gate(segment, parent=self)

    def parse_if(self, segment):
        # 0 none; 1 local; 2 Slink; 22 fx
        if segment == b'\x01':
            return "Local"
        elif segment == b'\x02':
            return "SLink"
        elif segment == b'\x22':
            return "Fx"
        elif segment == b'\x00':
            return None
        else:
            return segment

    def stereo_r(self, segment):
        if segment not in (b'\xfa', b'\xf8'):
            raise ValueError("unexpected mono/l/r flag value")
        elif segment == b'\xfa':
            return True
        else:
            return False


class ParametricEQ(DataTable):
    _structure = {
        "LF": (0, 6, "parse_params"),
        "LM": (6, 6, "parse_params"),
        "HM": (12, 6, "parse_params"),
        "HF": (18, 6, "parse_params"),
    }
    def __init__(self, data, parent=None):
        super().__init__(data, parent=parent)

    def parse_params(self, data):
        return PEQ_Band(data, parent=self)


class PEQ_Band(DataTable):
    _structure = {
        "gain": (0, 2, "parse_gain"),
        "frequency": (2, 2, "parse_freq"),
        "width": (4, 1, "parse_width"),
        "type": (5, 1, "parse_type"),
    }
    def __init__(self, data, parent=None):
        super().__init__(data, parent=parent)

    def parse_freq(self, segment):
        return self.freq_flt(segment)

    def parse_gain(self, segment):
        gain_int = self.signed_int("".join(f"{b:08b}" for b in segment[::-1])[2:])
        return self.sig_digits(gain_int / 256)
        # return int(gain_int / 25.6) / 10  # truncate to one decimal

    @staticmethod
    def parse_type(segment):
        types = {
            b'\x00': "bandpass",
            b'\x07': "shelf",
            b'\x0b': "highpass",
            b'\n': "lowpass",
        }
        if segment in types:
            return types[segment]
        else:
            return segment

    @staticmethod
    def parse_width(segment):
        widths = {  # in octaves
            b'\x19': "1/9", b'\x18': "0.13", b'\x17': "1/6", b'\x16': "0.2", b'\x15': "1/4", b'\x14': "0.3",
            b'\x13': "1/3", b'\x12': "0.4", b'\x11': "0.45", b'\x10': "0.5", b'\x0f': "0.55", b'\x0e': "0.6",
            b'\x0d': "2/3", b'\x0c': "0.7", b'\x0b': "3/4", b'\x0a': "0.8", b'\x09': "0.85", b'\x08': "0.9",
            b'\x07': "0.95", b'\x06': "1", b'\x05': "1.1", b'\x04': "1.2", b'\x03': "1.3", b'\x02': "1.4",
            b'\x01': "1.5", b'\x00': None,
        }
        if segment in widths:
            return widths[segment]
        else:
            return segment


class Compressor(DataTable):
    _structure = {
        "attack": (0, 2, "log_range"),  # confirmed
        "release": (2, 2, "log_range"),  # confirmed
        "threshold": (4, 2, "dB_level"),  # confirmed
        "gain": (6, 2, "dB_level"),  # confirmed
        "unk252": (8, 2, "hex"),
        # "comp_mode": (),  # RMS or Peak
        # "side_chain": (),  # self-keyed or another channel
        # "filter_mode": (),  # HPF, BPF or LPF
        # "filter_freq": (, 2, "freq_flt"),
        # "filter_in": (, 1, "bool"),
        # "parallel_path": (, 1, "bool"),
        # "dry_level": (, 2, "dB_level"),
        # "wet_level": (, 2, "dB_level"),
        # "soft_knee": (, 1, "bool"),
        # "comp_in": (, 1, "bool"),
        "unk255": (11, 1, "hex"),  # ch 106 is different
        "unk257": (13, 3, "hex"),  # ch 106 is different
        "unk262": (18, 4, "hex"),  # ch 106 is different
        "unk267": (23, 1, "hex"),  # compressor parameter ???
        "ratio": (38, 2, "hex"),  # compressor parameter ???
    }
    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)


class Gate(DataTable):
    _structure = {
        "attack": (0, 2, "log_range"),  # s
        "release": (2, 2, "log_range"),  # s
        "hold": (4, 2, "log_range"),  # s
        "threshold": (6, 2, "dB_level"),  # dB
        "depth": (8, 2, "dB_level"),  # dB
        # "side_chain": (),  # self-keyed or another channel
        "gate_hpf_freq": (24, 2, "freq_flt"),  # confirmed
        "gate_hpf_in": (27, 1, "bool"),  # confirmed
        "gate_in": (29, 1, "bool"),
    }
    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)


class Unk(DataTable):
    _structure = {
        'byte_0': (0, 1, 'hex'),
        'byte_1': (1, 1, 'hex'),
        'byte_2': (2, 1, 'hex'),
        'byte_3': (3, 1, 'hex'),
        'byte_4': (4, 1, 'hex'),
        'byte_5': (5, 1, 'hex'),
    }
    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)
