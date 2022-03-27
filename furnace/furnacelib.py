#!/usr/bin/python3
"""
This is a library for viewing and manipulating FurnaceTracker .fur files.
"""

import zlib
import io
import struct

from furnacetypes import FurnaceNote, FurnaceInstrumentType, FurnaceChip

FUR_STRING = b"-Furnace module-"

def read_as(format, file):
    """
    Frontend to struct.unpack with automatic size inference.
    Always operates in little-endian.

    Passing `format="string"` will make it read a single null-terminated string
    from the file's current position.
    """
    if format == "string":
        text = ""
        buffer = file.read(1)
        while buffer != b"\x00":
            text += buffer.decode('ascii') # probably unsafe
            buffer = file.read(1)
        return text

    size = 0
    known_sizes = {
        "c": 1,
        "b": 1, "B": 1,
        "?": 1,
        "h": 2, "H": 2,
        "i": 4, "I": 4,
        "l": 4, "L": 4,
        "q": 8, "Q": 8,
        "e": 2, "f": 4,
        "d": 8
    }
    for i in format:
        size += known_sizes.get(i, 0)
    return struct.unpack("<"+format, file.read(size))

def read_as_single(format, file):
    """
    If the `read_as` format is a single character it'll still
    return a tuple. This function turns it into a single value.
    """
    return read_as(format, file)[0]

class FurnaceModule:
    """
    A representation of a FurnaceTracker module is contained
    within an instance's `module` variable.

    List of attributes:

    `chips`
    -------
    Information about the soundchips that this module uses.
    Contained within:
        * `list` - A `list` containing the chip IDs (`FurnaceChip` enum)
        * `panning` - A `list` containing the panning information for each chip.
        * `settings` - Currently a binary blob `list` containing sound chip settings.
        * `volumes` - A `list` containing the volume information for each chip.

    `compatFlags`
    -------------
    Currently a binary blob `list` detailing which compatibility flags are set.

    `info`
    ------
    General module information. Contained within:
        * `channelNames` - A `list` of strings. Corresponds to channel order.
        * `channelAbbreviations` - A `list` of strings. Corresponds to channel order.
        * `channelsCollapsed` - A `list` of booleans. Corresponds to channel order.
        * `channelsShown` - A `list` of booleans. Corresponds to channel order.
        * `effectColumns` - A `list` of integers. Corresponds to channel order.
        * `masterVolume` - Available in later Furnace builds. 2.0 by default.
        * `patternLength`
        * `tuning`

    `instruments`
    -------------
    TODO

    `meta`
    ------
    TODO

    `order`
    -------
    TODO

    `patterns`
    ----------
    TODO

    `timing`
    --------
    TODO

    `wavetables`
    ------------
    TODO
    """

    def __init__(self, new_module=False, file_name=None, stream=None):
        """
        Initializes either an "empty" FurnaceTracker module, or, if
        supplied either a file name or a stream, deserializes a FurnaceTracker
        module from that.
        """
        self.file_name = None

        # initialize as if we just started a new module

        self.meta = {}
        self.timing = {}
        self.order = {}
        self.chips = {}
        self.info = {}
        self.compatFlags = []
        self.patterns = []
        self.instruments = []
        self.wavetables = []

        # these are only used in the loading routines
        self.__version = None
        self.__song_info_ptr = None
        self.__loc_instruments = None
        self.__loc_waves = None
        self.__loc_samples = None
        self.__loc_patterns = None

        if type(file_name) is str:
            self.load_from_file(file_name)
        elif stream is not None:
            self.load_from_stream(stream)

    def load_from_file(self, file_name):
        """
        Deserializes a .fur file. Automatically detects compressed or
        uncompressed files.
        """
        self.file_name = file_name
        with open(file_name, "rb") as fur_in:
            # uncompressed file
            if fur_in.read(16) == FUR_STRING:
                fur_in.seek(0)
                return self.load_from_bytes( fur_in.read() )
            # compressed file
            fur_in.seek(0)
            return self.load_from_bytes(
                zlib.decompress( fur_in.read() )
            )

    def decompress_to_file(in_name, out_name):
        """
        Decompresses a Zlib-compressed .fur file (in_name) to an uncompressed
        .fur file (out_name) that Furnace can still open.

        This method does not need instantiation to be run.
        """
        with open(in_name, "rb") as fur_in:
            with open(out_name, "wb") as fur_out:
                fur_out.write(
                    zlib.decompress( fur_in.read() )
                )

    def load_from_bytes(self, bytes):
        """
        Loads a FurnaceTracker module from raw bytes.
        (Must be in uncompressed form)
        """
        return self.load_from_stream(
            io.BytesIO(bytes)
        )

    def load_from_stream(self, stream):
        """
        Core unpacking routine, loads a module from a stream object
        (either file-like or BytesIO). Stream must be uncompressed!
        """
        self.__read_header(stream)
        self.__read_info(stream)
        self.__read_instruments(stream)
        self.__read_wavetables(stream)
        self.__read_samples(stream)
        self.__read_patterns(stream)
        #print("TODO: current position in file: $%x" % stream.tell())

    def make_new(self):
        """
        Create a minimal FurnaceTracker module.
        """
        self.meta = {
            "author": "",
            "comment": "",
            "name": "",
            "version": 70
        }
        self.timing = {
            "arpSpeed": 1,
            "clockSpeed": 60.0,
            "highlight": (4, 16),
            "speed": (6, 6),
            "timebase": 0
        }
        self.order = {
            0: [0],
            1: [0],
            2: [0],
            3: [0]
        }
        self.chips = {
            "panning": [0 for x in range(32)],
            "volume": [1.0 for x in range(32)],
            "settings": [b"\x00\x00\x00\x00" for x in range(32)],
            "list": [FurnaceChip.GB]
        }
        self.info = {
            "channelAbbreviations": ['' for x in range(4)],
            "channelNames": ['' for x in range(4)],
            "channelsCollapsed": [False for x in range(4)],
            "channelsShown": [True for x in range(4)],
            "effectColumns": [1 for x in range(4)],
            "masterVolume": 1.0,
            "patternLength": 1,
            "tuning": 440.0
        }
        self.compatFlags = [
            b"\x00\x01\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00",
            b"\x00\x00\x01\x01"
        ]
        self.patterns = []
        for i in range(4):
            self.patterns.append({
                "channel":i,
                "index":0,
                "name":"",
                "data":[
                    {
                        "effects":[(-1,-1)],
                        "instrument":-1,
                        "note":FurnaceNote.__,
                        "octave":0,
                        "volume":-1
                    }
                ]
            })
        self.instruments = []
        self.wavetables = []
        self.samples = []

    def __read_header(self, stream):
        if stream.read(16) != FUR_STRING:
            raise Exception("Invalid Furnace module (magic number invalid)")
        # read version number
        self.meta["version"] = read_as_single("H", stream)
        self.__version = self.meta["version"]
        stream.read(2) # XXX reserved
        self.__song_info_ptr = read_as_single("I", stream)
        stream.read(8) # XXX reserved

    def __read_info(self, stream):
        # read song info
        stream.seek(self.__song_info_ptr)
        if stream.read(4) != b"INFO":
            raise Exception("Broken INFO header")
        stream.read(4) # XXX reserved

        # timing info
        self.timing["timebase"] = read_as_single("B", stream) # 0-indexed
        self.timing["speed"] = read_as("BB", stream)
        self.timing["arpSpeed"] = read_as_single("B", stream)
        self.timing["clockSpeed"] = read_as_single("f", stream)

        # length of patterns
        self.info["patternLength"] = read_as_single("H", stream)
        self.__len_patterns = self.info["patternLength"]
        len_orders = read_as_single("H", stream)

        # highlights
        self.timing["highlight"] = read_as("BB", stream)

        num_instruments = read_as_single("H", stream)
        num_waves = read_as_single("H", stream)
        num_samples = read_as_single("H", stream)
        num_patterns = read_as_single("I", stream)

        # chip settings
        self.chips["list"] = []
        self.chips["volumes"] = []
        self.chips["panning"] = []
        self.chips["settings"] = []
        # soundchip list
        for chip_id in stream.read(32):
            if chip_id == 0:
                break;
            try:
                self.chips["list"].append( FurnaceChip(chip_id) )
            except ValueError:
                pass

        for i in range(32):
            self.chips["volumes"].append( read_as_single("b", stream) / 64 )

        for i in range(32):
            self.chips["panning"].append( read_as_single("b", stream) )

        for i in range(32):
            self.chips["settings"].append( stream.read(4) )

        # fill in metadata
        self.meta["name"] = read_as("string", stream)
        self.meta["author"] = read_as("string", stream)
        self.info["tuning"] = read_as_single("f", stream)

        # compat flags are blobs for now
        self.compatFlags = [stream.read(20)]

        self.__loc_instruments = [read_as_single("I", stream) for i in range(num_instruments)]
        self.__loc_waves = [read_as_single("I", stream) for i in range(num_waves)]
        self.__loc_samples = [read_as_single("I", stream) for i in range(num_samples)]
        self.__loc_patterns = [read_as_single("I", stream) for i in range(num_patterns)]

        # how many channels are there in total?
        num_channels = 0
        for chip in self.chips["list"]:
            num_channels += chip.channels

        # load orders
        self.order = {}
        for channel in range(num_channels):
            self.order[channel] = []
            for order in range(len_orders):
                self.order[channel].append(read_as_single("B", stream))

        # load channel settings
        self.info["effectColumns"] = []
        self.info["channelsShown"] = []
        self.info["channelsCollapsed"] = []
        self.info["channelNames"] = []
        self.info["channelAbbreviations"] = []

        # number of FX columns
        for channel in range(num_channels):
            self.info["effectColumns"].append(read_as_single("B", stream))

        # channels shown
        for channel in range(num_channels):
            status = read_as_single("B", stream)
            if status:
                self.info["channelsShown"].append(True)
            else:
                self.info["channelsShown"].append(False)

        # channels collapsed
        for channel in range(num_channels):
            status = read_as_single("B", stream)
            if status:
                self.info["channelsCollapsed"].append(True)
            else:
                self.info["channelsCollapsed"].append(False)

        # channel names shown in frame window
        for channel in range(num_channels):
            self.info["channelNames"].append(read_as("string", stream))

        # channel names shown in order window
        for channel in range(num_channels):
            self.info["channelAbbreviations"].append(read_as("string", stream))

        self.meta["comment"] = read_as("string", stream)

        if (self.__version >= 59):
            self.info["masterVolume"] = read_as_single("f", stream)

        extendedCompat = b''
        if (self.__version >= 70):
            extendedCompat += stream.read(1)
        if (self.__version >= 71):
            extendedCompat += stream.read(3)

    def __read_instruments(self, stream):
        for i in self.__loc_instruments:
            stream.seek(i)
            self.instruments.append(
                FurnaceInstrument(stream=stream)
            )

    def __read_wavetables(self, stream):
        for i in self.__loc_waves:
            stream.seek(i)
            self.wavetables.append(
                FurnaceWavetable(stream=stream)
            )

    def __read_samples(self, stream):
        # TODO
        #print("TODO: sample pointers     ->", end=" ")
        #for i in self.__loc_samples:
            #print("$%04x" % i, end=" ")
        #print()
        pass

    def __read_patterns(self, stream):
        for i in self.__loc_patterns:
            stream.seek(i)

            new_patr = {}
            if stream.read(4) != b"PATR":
                raise Exception("Not a pattern?")

            stream.read(4) # reserved
            new_patr["channel"] = read_as_single("H", stream)
            channel = new_patr["channel"]
            new_patr["index"] = read_as_single("H", stream)
            stream.read(4) # reserved
            new_patr["data"] = []

            effects = self.info["effectColumns"][channel]
            pattern_length = self.info["patternLength"]

            for p in range(pattern_length):
                new_row = {}
                new_row["note"] = read_as_single("H", stream)
                new_row["note"] = FurnaceNote(new_row["note"])

                new_row["octave"] = read_as_single("H", stream)
                new_row["instrument"] = read_as_single("h", stream)

                new_row["volume"] = read_as_single("h", stream)

                new_row["effects"] = []
                for x in range(effects):
                    new_row["effects"].append(read_as("hh", stream))

                new_patr["data"].append(new_row)

            new_patr["name"] = read_as("string", stream)
            self.patterns.append(new_patr)

    def __repr__(self):
        return "<Furnace module '%s' by %s>" % (
            self.meta["name"], self.meta["author"]
        )

class FurnaceInstrument:
    # TODO: make it read .fui files
    def __init__(self, file_name=None, stream=None):
        self.data = {}
        self.version = None
        self.type = None
        self.name = None

        if type(file_name) is str:
            self.load_from_file(file_name)
        elif stream is not None:
            self.load_from_stream(stream)

    def load_from_file(self, file_name):
        pass

    def load_from_bytes(self, bytes):
        pass

    def load_from_stream(self, stream):
        self.__read_header(stream)
        self.__read_fm(stream)
        self.__read_gameboy(stream)
        self.__read_c64(stream)
        self.__read_amiga(stream)
        self.__read_standard(stream)
        # TODO: complete this
        #print("TODO: current position in file: $%x" % stream.tell())

    def __read_header(self, stream):
        if stream.read(4) != b"INST":
            raise Exception("Not an instrument?")

        stream.read(4) # reserved
        self.version = read_as_single("H", stream)
        self.type = FurnaceInstrumentType(stream.read(1)[0])
        stream.read(1) # reserved
        self.name = read_as("string", stream)

    def __read_fm(self, stream):
        self.data["fm"] = {}
        self.data["fm"]["alg"] = read_as_single("B", stream)
        self.data["fm"]["feedback"] = read_as_single("B", stream)
        self.data["fm"]["fms"] = read_as_single("B", stream)
        self.data["fm"]["ams"] = read_as_single("B", stream)
        self.data["fm"]["opCount"] = read_as_single("B", stream)
        if self.version >= 60:
            self.data["fm"]["opll"] = read_as_single("B", stream)
        else:
            stream.read(1) # reserved
        stream.read(2) # reserved

        self.data["fm"]["ops"] = []
        for op in range(4):
            new_op = {}
            new_op["am"]        = read_as_single("B", stream)
            new_op["ar"]        = read_as_single("B", stream)
            new_op["dr"]        = read_as_single("B", stream)
            new_op["mult"]      = read_as_single("B", stream)
            new_op["rr"]        = read_as_single("B", stream)
            new_op["sl"]        = read_as_single("B", stream)
            new_op["tl"]        = read_as_single("B", stream)
            new_op["dt2"]       = read_as_single("B", stream)
            new_op["rs"]        = read_as_single("B", stream)
            new_op["dt"]        = read_as_single("B", stream)
            new_op["d2r"]       = read_as_single("B", stream)
            new_op["ssgEnv"]    = read_as_single("B", stream)
            new_op["dam"]       = read_as_single("B", stream)
            new_op["dvb"]       = read_as_single("B", stream)
            new_op["egt"]       = read_as_single("B", stream)
            new_op["ksl"]       = read_as_single("B", stream)
            new_op["sus"]       = read_as_single("B", stream)
            new_op["vib"]       = read_as_single("B", stream)
            new_op["ws"]        = read_as_single("B", stream)
            new_op["ksr"]       = read_as_single("B", stream)
            stream.read(12) # reserved

            self.data["fm"]["ops"].append(new_op)

    def __read_gameboy(self, stream):
        self.data["gameboy"] = {}
        self.data["gameboy"]["volume"]       = read_as_single("B", stream)
        self.data["gameboy"]["direction"]    = read_as_single("B", stream)
        self.data["gameboy"]["length"]       = read_as_single("B", stream)
        self.data["gameboy"]["soundLength"]  = read_as_single("B", stream)

    def __read_c64(self, stream):
        self.data["c64"] = {}
        self.data["c64"]["triangle"]         = read_as_single("B", stream)
        self.data["c64"]["saw"]              = read_as_single("B", stream)
        self.data["c64"]["pulse"]            = read_as_single("B", stream)
        self.data["c64"]["noise"]            = read_as_single("B", stream)
        self.data["c64"]["adsr"]             = read_as("BBBB", stream)
        self.data["c64"]["duty"]             = read_as_single("H", stream)
        self.data["c64"]["ringMod"]          = read_as_single("B", stream)
        self.data["c64"]["oscSync"]          = read_as_single("B", stream)
        self.data["c64"]["toFilter"]         = read_as_single("B", stream)
        self.data["c64"]["initFilter"]       = read_as_single("B", stream)
        self.data["c64"]["volMacroAsCutoff"] = read_as_single("B", stream)
        self.data["c64"]["resonance"]        = read_as_single("B", stream)
        self.data["c64"]["lowPass"]          = read_as_single("B", stream)
        self.data["c64"]["bandPass"]         = read_as_single("B", stream)
        self.data["c64"]["highPass"]         = read_as_single("B", stream)
        self.data["c64"]["ch3Off"]           = read_as_single("B", stream)
        self.data["c64"]["cutoff"]           = read_as_single("H", stream)
        self.data["c64"]["absDutyMacro"]     = read_as_single("B", stream)
        self.data["c64"]["absFilterMacro"]   = read_as_single("B", stream)

    def __read_amiga(self, stream):
        self.data["amiga"] = {}
        self.data["amiga"]["sampleId"] = read_as_single("H", stream)
        stream.read(14) # reserved

    def __read_standard(self, stream):
        # TODO: complete this
        self.data["standard"] = {}
        std_macro_lengths = {
            "volume": read_as_single("I", stream),
            "arp": read_as_single("I", stream),
            "duty": read_as_single("I", stream),
            "wave": read_as_single("I", stream),
        }
        if self.version >= 17:
            std_macro_lengths["pitch"] = read_as_single("I", stream)
            std_macro_lengths["x1"]    = read_as_single("I", stream)
            std_macro_lengths["x2"]    = read_as_single("I", stream)
            std_macro_lengths["x3"]    = read_as_single("I", stream)

    def __repr__(self):
        return "<Furnace %s instrument '%s'>" % (
            self.type, self.name)

class FurnaceWavetable:
    # TODO: make it read .fuw files
    def __init__(self, file_name=None, stream=None):
        self.data = []
        self.range = (-1, -1)
        self.name = None

        if type(file_name) is str:
            self.load_from_file(file_name)
        elif stream is not None:
            self.load_from_stream(stream)

    def load_from_file(self, file_name):
        pass

    def load_from_bytes(self, bytes):
        pass

    def load_from_stream(self, stream):
        self.__read_header(stream)
        self.__read_wave(stream)

    def __read_header(self, stream):
        if stream.read(4) != b"WAVE":
            raise Exception("Not a wavetable?")
        stream.read(4) # reserved
        self.name = read_as("string", stream)

    def __read_wave(self, stream):
        wave_size = read_as_single("I", stream)
        self.range = read_as("II", stream)
        for i in range(wave_size):
            # some values can extend beyond the range so clip it manually
            # if you need to
            self.data.append( read_as_single("I", stream) )

    def __repr__(self):
        return "<Furnace wavetable '%s'>" % ( self.name )

if __name__ == "__main__":
    import sys
    import pprint
    pp = pprint.PrettyPrinter(4)

    module = FurnaceModule(file_name=sys.argv[1])
    pp.pprint(
        (
            module.wavetables
        )
    )
