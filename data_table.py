from __future__ import annotations

import hashlib
import math
# import mmh3
import zlib

# from numpy.distutils.extension import cxx_ext_re


class DataTable:
    _structure: dict[str, tuple[int, int, str]] = {}
    _offset = 10658
    _interval = 638.5
    _f_low = 20
    _multiplier = 10 ** (1 / 24)  # 1.10069417
    def __init__(self, data, parent=None, **kwargs):
        self.parent = parent
        # TODO: allow absolute addressing of the asset data via the parent-child relationship
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.data = data
        self.length = len(data)
        self.attrs = self.parse()

    def __repr__(self):
        if hasattr(self, "name"):
            return f"{self.__class__.__name__}('{self.name}')"
        else:
            return f"{self.__class__.__name__}()"

    def __eq__(self, other):
        return self.data == other.data

    @property
    def _bin(self) -> str:
        return "".join(f"{b:08b}" for b in self.data)

    @property
    def _bin_lsb_first(self) -> str:
        return "".join(f"{b:08b}" for b in self.data)[::-1]

    @property
    def _hex(self) -> str:
        return hex(int.from_bytes(self.data, "big"))

    @property
    def _rev(self) -> str:
        return self.data[::-1]

    @property
    def _rev_bin(self) -> str:
        return "".join(f"{b:08b}" for b in self._rev)

    @property
    def unattributed(self) -> list[tuple[int, int, str]]:
        if hasattr(self, "attrs"):
            attributed = [i for attr in self.attrs for i in
                          range(self._structure[attr][0], self._structure[attr][0] + self._structure[attr][1])]
            unattributed = [i for i in range(len(self.data)) if i not in attributed]
            reduced = []
            start = 0
            for index, i in enumerate(unattributed):
                if index == len(unattributed) - 1 or i + 1 != unattributed[index + 1]:
                    reduced.append((
                        unattributed[start],
                        unattributed[index] + 1 - unattributed[start],
                        self.hex(self.data[slice(unattributed[start], unattributed[index] + 1)]),
                    ))
                    start = index + 1
            return reduced
        return None

    def bfp16(self, segment, exp_len=8, mant_len=7) -> float:
        if isinstance(segment, bytes):
            segment = self.bin(segment)
        if len(segment) != 16:
            raise ValueError("bfp16 only works with 2 bytes or 16 bits")
        return self.ieee_flt(segment, exp_len=exp_len, mant_len=mant_len)

    def bin(self, segment) -> str:
        return "".join(f"{b:08b}" for b in segment)

    @staticmethod
    def bool(segment):
        return bool(int.from_bytes(segment, "big"))

    @staticmethod
    def cleanup(segment):
        try:
            return segment.replace(b'\x00', b'').decode('utf-8')
        except:
            return segment

    def compare(self, other, explode=False):
        if not isinstance(other, self.__class__):
            raise TypeError("can only compare two objects of the same class")
        differences = []
        if explode is True and self.attrs:
            for attr in self.attrs:
                if attr not in other.attrs:
                    differences.append({attr: (getattr(self, attr), None)})
                elif getattr(self, attr) != getattr(other, attr):
                    if isinstance(getattr(self, attr), DataTable):
                        differences.append({attr: getattr(self, attr).compare(getattr(other, attr), explode=explode)})
                    else:
                        differences.append({attr: (getattr(self, attr), getattr(other, attr))})
        else:
            diff_self = diff_other = b''
            diff_loc = 0
            for i, char in enumerate(self.data):
                if char != other.data[i]:
                    if not diff_self:
                        diff_loc = i
                    diff_self += self.data[i:i+1]
                    diff_other += other.data[i:i+1]
                else:
                    if diff_self:
                        differences.append((diff_loc, diff_self, diff_other))
                    diff_self = diff_other = b''
            if diff_self:
                differences.append((diff_loc, diff_self, diff_other))
        return differences

    def delay(self, segment):
        return round(self.uint(segment) / 96, 2)

    def dB_level(self, segment):
        return self.sig_digits((self.uint(segment) - 0x8000) / 256)

    def flt16(self, segment, exp_len=5, mant_len=10):  # not used
        if isinstance(segment, bytes):
            segment = self.bin(segment)
        if len(segment) != 16:
            raise ValueError("flt16 only works with 2 bytes or 16 bits")
        return self.ieee_flt(segment, exp_len=exp_len, mant_len=mant_len)

    def freq_flt(self, segment):
        # series = [(int(10658 + n * 638.5), round(20 * 1.1006941712522096 ** n, 1)) for n in range(128)]
        value = int("".join(f"{b:08b}" for b in segment[::-1]), 2)
        exp = (value - self._offset) / self._interval
        freq = self._f_low * self._multiplier ** exp
        return self.sig_digits(freq)

    def generic(self, segment):
        return DataTable(segment)

    @staticmethod
    def hex(segment) -> str:
        digits = 2 * len(segment)
        return f'0x{int.from_bytes(segment, "big"):0{digits}x}'

    def ieee_flt(self, segment=None, sign=None, exponent_raw=None, mantissa=None, exp_len=8, mant_len=23) -> float:
        """ Convert binary data into the floating point value """
        if segment is None:
            segment = self._bin
        if sign is None:
            sign = int(segment[:1], 2)
        if exponent_raw is None:
            exponent_raw = int(segment[1:exp_len + 1], 2)
        if mantissa is None:
            mantissa = int(segment[exp_len + 1:], 2)
        sign_mult = -1 if sign == 1 else 1
        exponent = exponent_raw - (2 ** (exp_len - 1) - 1)
        mant_mult = 1
        for b in range(mant_len - 1, -1, -1):
            if mantissa & (2 ** b):
                mant_mult += 1 / (2 ** (mant_len - b))
        return sign_mult * (2 ** exponent) * mant_mult

    def log_range(self, segment, low=50e-6, high=5.0):
        fraction = (self.uint(segment) - 10123) / (39912 - 10123)
        extent = math.log(high) - math.log(low)
        value = math.exp(extent * fraction + math.log(low))
        return self.sig_digits(value)

    @staticmethod
    def nop(segment):
        return segment

    def parse(self) -> list:
        for attr in self._structure:
            start, length, method = self._structure[attr]
            segment = self.data[start:start + length]
            setattr(self, attr, getattr(self, method)(segment))
        return [attr for attr in self._structure]

    @staticmethod
    def sig_digits(value, digits=2, transition=0.2):
        # transition is the value at which the rounding changes, e.g. if transition=0.2:
        #   sig_digits(12345) = 12300
        #   sig_digits(23456) = 23000
        if value > 0.0:
            order = math.log10(value / transition)
        elif value < 0.0:
            order = math.log10(-value / transition)
        else:
            order = 0
        round_to = 2 - int(order) + int(order < 0)
        return round(value, round_to)

    @staticmethod
    def signed_int(segment, byte_order="big", signed=True) -> int:
        if isinstance(segment, bytes) and byte_order == "little":
            binary = "".join(f"{b:08b}" for b in segment[::-1])
        elif isinstance(segment, bytes):
            binary = "".join(f"{b:08b}" for b in segment)
        else:
            binary = segment
        bits = len(binary)
        val = int(binary, 2)
        if signed and binary[0] == '1':
            val -= (1 << bits)
        try:
            in_bytes = val.to_bytes((bits + 7) // 8, byte_order, signed=signed)
            signed_int = int.from_bytes(in_bytes, byteorder=byte_order, signed=signed)
        except OverflowError:
            signed_int = 0
        return signed_int

    def uint(self, segment):
        return self.signed_int(segment, byte_order="little", signed=False)


class Group(DataTable):
    _structure = {
        "unk04": (4, 1, "uint"),
        "unk08": (8, 2, "uint"),
        "name": (11, 6, "cleanup"),
    }
    def __init__(self, data, parent=None):
        super().__init__(data, parent=parent)


class Mute(DataTable):  # ???
    _structure = {
        "unk08": (8, 1, "uint"),
        "name": (9, 6, "cleanup"),
    }
    def __init__(self, data, parent=None):
        super().__init__(data, parent=parent)


class Checksum(DataTable):  # ???
    def __init__(self, data, parent=None, method="crc32"):
        super().__init__(data, parent=parent)
        self.raw = self.parent.data[:-4]
        self.checksum = self.uint(data)
        self.checksum_reordered = self.signed_int(data, byte_order="big", signed=False)
        self.derived = getattr(self, method)(self.raw)
        # for method in ("crc32", "adler32", "sum32", "mmh3", "sha256"):
        #     print(method, getattr(self, method)(self.raw))
        # print(self.checksum_reordered, self.checksum, len(self.raw))

    @property
    def match(self):
        return self.checksum == self.derived

    @staticmethod
    def crc32(data):  # this is not correct
        return zlib.crc32(data)

    # @staticmethod
    # def adler32(data):
    #     return zlib.adler32(data)
    #
    # @staticmethod
    # def sum32(data):
    #     return sum(data) & 0xFFFFFFFF
    #
    # @staticmethod
    # def mmh3(data):
    #     return mmh3.hash(data, signed=False)
    #
    # @staticmethod
    # def sha256(data):
    #     return hashlib.sha256(data).digest()[:4]
    #
    # @staticmethod
    # def xor32(data: bytes) -> bytes:
    #     """Calculates a 4-byte checksum by XORing data in 32-bit chunks."""
    #     # Ensure data length is a multiple of 4 by padding with trailing zeros
    #     remainder = len(data) % 4
    #     if remainder:
    #         data += b'\x00' * (4 - remainder)
    #
    #     # Initialize the checksum with the first 4 bytes
    #     checksum = int.from_bytes(data[0:4], byteorder='big')
    #
    #     # XOR subsequent 4-byte chunks
    #     for i in range(4, len(data), 4):
    #         chunk = int.from_bytes(data[i:i + 4], byteorder='big')
    #         checksum ^= chunk
    #
    #     # Return the checksum as a 4-byte object
    #     return checksum.to_bytes(4, byteorder='big')

