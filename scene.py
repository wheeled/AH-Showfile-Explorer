
from asset import Asset
from effects import Effect
from io_channel import IOChannel
from layers import Layer
from levels import Levels
from tabs import Tab
from data_table import DataTable, DataTableList, Group, Mute, Checksum


class Scene(Asset):
    _structure = {
        'name': (20, 16, "cleanup"),  # not certain of the length
    }
    attrs = ["io_channels", "channel_levels", "layers", "mix_groups", "mute_groups", "effects"]
    def __init__(self, filename, path, format="SQ", **kwargs):
        super().__init__(filename, path, **kwargs)
        if format == "QU":
            # QU files only support name parsing for now
            self._structure["name"] = (12, 8, "cleanup")
            self.parse()
        else:
            self.block_locations = [self.data.find(chr(n).encode('utf-8') + b'\xa5\xa5\xa5') for n in range(16)]
            # [-1, 56, 880, 41876, 42648, 43420, 80024, 81288, 83036, 83060, 83096, 84572, 84600, 87400, 89900, -1]
            self.io_channels = self.channels()
            self.channel_names = [ch.name for tag, ch in self.io_channels]
            self.layer_setup = None
            self.layers = None
            self.parse_layers()
            self.channel_levels = self.levels()
            self.effects = None
            self.effects_suffix = None
            self.parse_effects()
            self.parse_block_e()

    @property
    def block_0(self):
        # location 8 is involved with one of the changes in scene8f [(8, b'\x1a', b'\x14')]
        block_id = 0
        return DataTable(self.block(block_id))

    @property
    def mix_groups(self):
        # no differences noticed
        block_id = 3
        record_length = 24
        return DataTableList(self.block(block_id), Group, record_length, "mix-group", parent=self)

    @property
    def mute_groups(self):
        # no differences noticed
        block_id = 4
        record_length = 24
        return DataTableList(self.block(block_id), Mute, record_length, "mute-group", parent=self)

    @property
    def block_6(self):
        # only difference noticed at byte 38
        # repeats at intervals of 4 bytes
        # two groups of bytes with unusual values
        block_id = 6
        temp = DataTable(self.block(block_id))
        interval = 4
        # return [(n, interval, temp.hex(temp.data[n:n + interval])) for n in range(0, len(temp.data), interval)]
        return temp

    @property
    def block_7(self):
        # differences every 4 bytes (divider b'\xfe'); from 414th record pattern changes to every 6 bytes
        # repatch may be at bytes 32 and 36
        # block_7 = [(index, hex(record), [sc0830.signed_int(record[n:n + 1]) for n in range(len(record))]) for index, record in enumerate(sc0830.block_7.data.split(b'\xfe'))]
        block_id = 7
        temp = DataTable(self.block(block_id))
        # return [[record[n] for n in range(len(record))] for record in temp.data.split(b'\xfe')]
        return temp

    @property
    def block_8(self):
        # no differences noticed
        # repeats at 8-byte intervals
        block_id = 8
        return DataTable(self.block(block_id))

    @property
    def block_9(self):
        # no differences noticed
        block_id = 9
        return DataTable(self.block(block_id))

    @property
    def block_a(self):
        # no differences noticed
        block_id = 10
        temp = DataTable(self.block(block_id))
        interval = 8  # for 32 records, then 32 bytes until the end?
        return [temp.data[n:n + interval] for n in range(0, len(temp.data), interval)]

    @property
    def block_b(self):
        # differences at bytes 0, 19
        block_id = 11
        return DataTable(self.block(block_id))

    @property
    def block_c(self):
        # differences every 8 bytes (e.g. 830, b'@', b'\x00') and at byte 1392
        block_id = 12
        temp = DataTable(self.block(block_id))
        interval = 8  # for 64 records, and possibly longer
        return [temp.data[n:n + interval] for n in range(0, len(temp.data), interval)]

    # @property
    def parse_block_e(self):
        # regular differences - appears to be multiple tables, including six identified as "Tab 1" to "Tab 6"
        # large block before Tabs, and another block after
        # only data appears to be in
        #  - first 178 bytes, especially towards the end of that block (followed by b'\xff\xff')
        #  - next 614 bytes, especially towards the end of that block (followed by b'\xff\xff')
        #  - next 300 * 6 bytes, which are numbered 1 to 300 and include b'\xff\xff'
        # then there are other blocks which appear to be formatted but empty
        # last 4 bytes are checksum?
        block_id = 14
        data = self.block(block_id)
        self.block_e_pt_1 = DataTable(data[:4372])
        self.empty_tabs = [Tab(data[4372 + n * 612:4372 + (n + 1) * 612]) for n in range(6)]
        self.for_future_use = DataTable(data[4372+6*612:-4])
        self.checksum = Checksum(data[-4:], parent=self)
        return

    def block(self, block_id):
        return self.data[slice(*self.limits(block_id))]

    def channels(self):  # block includes both inputs and outputs
        block_id = 2
        record_length = 336  # TODO: can it be derived from the data?
        return DataTableList(self.block(block_id), IOChannel, record_length, "IO-port", parent=self)

    def divider(self, block_id):
        return chr(block_id).encode('utf-8') + b'\xa5\xa5\xa5'

    def levels(self):
        block_id = 5
        record_length = 300  # based on pattern of repetition of b'\xfe\xff'
        ch_levels = DataTableList(self.block(block_id), Levels, record_length, "ch-levels", parent=self)
        return ch_levels

    def limits(self, block_id):
        if block_id == 0:
            start = 0
        else:
            start = self.data.find(self.divider(block_id)) + len(self.divider(block_id))
        end = self.data.find(self.divider(block_id + 1))
        if end == -1:
            end = None
        return start, end

    def parse_effects(self):
        block_id = 13
        record_length = 154
        self.effects = DataTableList(self.block(block_id)[:-(len(self.block(block_id)) % record_length)], Effect, record_length, "effect", parent=self)
        self.effects_suffix = DataTable(self.block(block_id)[record_length * len(self.effects):])

    def parse_layers(self):
        # channel assignments to layers - 8 layers with 32 records each (96 bytes) demarcation byte b'\xff'
        block_id = 1
        divider = b'\xff'
        self.layer_setup = DataTable(self.block(block_id)[:44], parent=self)
        sections = self.block(block_id)[45:].split(divider)
        self.layers = [Layer(sections[n], parent=self, name=f"Layer {c}") for n, c in enumerate("ABCDEFGH")]
        return

    def sections(self, block_id, record_length, exact_fit=True):
        block = self.block(block_id)
        records = len(block) / record_length
        if records - int(records) == 0 or exact_fit is False:
            records = int(records)
        else:
            raise ValueError(f"block size ({len(block)}) is not an integer multiple of record_length ({record_length})")
        return [block[n * record_length:(n + 1) * record_length] for n in range(records)]
