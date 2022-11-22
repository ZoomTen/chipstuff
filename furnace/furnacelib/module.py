#!/usr/bin/python3
"""
This is a library for viewing and manipulating FurnaceTracker .fur files.
"""

import zlib
import io
from .util import read_as, read_as_single, write_as, truthy_to_boolbyte
from .types import FurnaceChip, FurnaceNote, FurnaceInstrumentType, FurnaceMacroItem
from .instrument import FurnaceInstrument
from .instrument_dx import FurnaceInstrumentDX
from .wavetable import FurnaceWavetable
from .sample import FurnaceSample
from .pattern import FurnacePattern

FUR_STRING = b"-Furnace module-"

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

    `compatFlags`, `extendedCompatFlags`
    ------------------------------------
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
        * `patternLength` - Nominal length of patterns.
        * `tuning` - A `float` that indicated which frequency A-4 is tuned to.

    `meta`
    ------
    Metadata about the module. Contained within:
        * `author` - Song author.
        * `comment` - Song comment.
        * `name` - Song name.
        * `version` - An `integer` indicating the file type version.

    `instruments`
    -------------
    A list of `FurnaceInstrument` used in the module.

    `order`
    -------
    A `dict` containing lists of order numbers per channel.

    `patterns`
    ----------
    A list of `FurnacePattern` used in the module.

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
        self.extendedCompatFlags = None
        self.patterns = []
        self.instruments = []
        self.wavetables = []
        self.samples = []

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

    def make_new(self):
        """
        Create a minimal FurnaceTracker module.
        """
        self.meta = {
            "author": "",
            "comment": "",
            "name": "",
            "version": 83
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
        self.extendedCompatFlags = b"\x00" * 32
        self.compatFlags = [
            b"\x00\x01\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00",
            b"\x00\x00\x01\x01"
        ]
        self.patterns = []
        for i in range(4):
            self.patterns.append(
                FurnacePattern(init_data={
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
            )
        self.instruments = []
        self.wavetables = []
        self.samples = []

    def save_to_stream(self, stream):
        """
        Save an uncompressed Furnace module file.
        This is untested.
        """
        version = self.meta["version"]
        
        stream.write(FUR_STRING)
        # assume that song info always come after the basic header
        write_as("hhi", (version, 0, 0x20), stream)
        stream.write(b"\x00" * 8)
        
        stream.write(b"INFO")
        stream.write(b"\x00" * 4)
        write_as("bbbbf", (
            self.timing["timebase"],
            *self.timing["speed"],
            self.timing["arpSpeed"],
            self.timing["clockSpeed"]
        ), stream)
        
        length = 0
        for i in self.patterns:
            new_length = len(i.data)
            if new_length > length:
                length = new_length
        
        order_length = len(self.order[0])
        
        write_as("hhbbhhhi", (
                length,
                order_length,
                *self.timing["highlight"],
                len(self.instruments),
                len(self.wavetables),
                len(self.samples),
                len(self.patterns)
            ), stream
        )
        
        chips = [b"\x00"] * 32
        chips_pos = 0
        for i in self.chips["list"]:
            chips[chips_pos] = int.to_bytes(i.value, 1, "little")
            chips_pos += 1
        stream.write(b"".join(chips))
        
        for i in self.chips["volume"]:
            write_as("B", [int(i * 64)], stream)
        
        for i in self.chips["panning"]:
            write_as("B", [int(i * 64)], stream)
        
        for i in self.chips["settings"]:
            stream.write(i)
        
        write_as("string", self.meta["name"], stream)
        write_as("string", self.meta["author"], stream)
        write_as("f", (self.info["tuning"],), stream)
        
        # compatFlags are a blob for now
        for i in self.compatFlags:
            stream.write(i)
        
        # to get back to later
        pointer_locs = {}
        data_locs = {
            "instruments":[],
            "wavetables":[],
            "samples":[],
            "patterns":[]
        }
        pointer_locs["instruments"] = stream.tell()
        for i in range( len(self.instruments) ):
            write_as("i", (0,), stream)
        pointer_locs["wavetables"] = stream.tell()
        for i in range( len(self.wavetables) ):
            write_as("i", (0,), stream)
        pointer_locs["samples"] = stream.tell()
        for i in range( len(self.samples) ):
            write_as("i", (0,), stream)
        pointer_locs["patterns"] = stream.tell()
        for i in range( len(self.patterns) ):
            write_as("i", (0,), stream)
        
        # write ordering
        for i in range(order_length):
            for j in self.order:
                write_as("b", (self.order[j][i],), stream)
        
        for i in self.info["effectColumns"]:
            write_as("b", (i,), stream)
        
        for i in self.info["channelsShown"]:
            stream.write( truthy_to_boolbyte(i) )
        
        for i in self.info["channelsCollapsed"]:
            stream.write( truthy_to_boolbyte(i) )
        
        for i in self.info["channelNames"]:
            write_as("string", i, stream)
        
        for i in self.info["channelAbbreviations"]:
            write_as("string", i, stream)
        
        write_as("string", self.meta["comment"], stream)
        
        if version >= 59:
            write_as("f", (self.info["masterVolume"],), stream)
        
        if version >= 70:
            # extend compat are also a blob for now
            if self.extendedCompatFlags:
                stream.write(self.extendedCompatFlags)
        
        # save patterns
        for i in self.patterns:
            data_locs["patterns"].append( stream.tell() )
            i.save_to_stream(stream)
        
        # TODO: instruments
        # TODO: wavetables
        # TODO: samples
        
        # go back to pointers
        stream.seek( pointer_locs["patterns"] )
        for i in data_locs["patterns"]:
            write_as("i", (i,), stream)
        
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

        # how many orders
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
        if (self.__version >= 72):
            extendedCompat += stream.read(2)
        if (self.__version >= 78):
            extendedCompat += stream.read(1)
        if (self.__version >= 83):
            extendedCompat += stream.read(2)
        
        self.extendedCompatFlags = extendedCompat

    def __read_instruments(self, stream):
        for i in self.__loc_instruments:
            stream.seek(i)
            inst_type = stream.read(4)
            stream.seek(-4, 1)
            if inst_type == b"INST":
                self.instruments.append(
                    FurnaceInstrument(stream=stream)
                )
            elif inst_type == b"INS2": # dev127+
                self.instruments.append(
                    FurnaceInstrumentDX(stream=stream)
                )
            else:
                raise Exception("Unknown instrument type?")

    def __read_wavetables(self, stream):
        for i in self.__loc_waves:
            stream.seek(i)
            self.wavetables.append(
                FurnaceWavetable(stream=stream)
            )

    def __read_samples(self, stream):
        for i in self.__loc_samples:
            stream.seek(i)
            self.samples.append(
                FurnaceSample(stream=stream)
            )

    def __read_patterns(self, stream):
        for i in self.__loc_patterns:
            stream.seek(i)
            self.patterns.append(
                FurnacePattern(
                    stream=stream,
                    stream_info={
                        "effectColumns": self.info["effectColumns"],
                        "patternLength": self.info["patternLength"]
                    }
                )
            )

    def __repr__(self):
        return "<Furnace module '%s' by %s>" % (
            self.meta["name"], self.meta["author"]
        )
