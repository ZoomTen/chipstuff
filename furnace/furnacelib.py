#!/usr/bin/python3
"""
This is a library for viewing and manipulating FurnaceTracker .fur files.
"""

import zlib
import io
import struct
from enum import Enum

FUR_STRING = b"-Furnace module-"

def read_as(format, file):
    """
    Frontend to struct.unpack with automatic size inference.
    Always operates in little-endian.

    Passing `format=string` will make it read a single null-terminated string
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

class FurnaceChip(Enum):
    """
    FurnaceTracker planned and implemented chip database.
    Contains console name, ID and number of channels.
    """
    YMU759            = (0x01, 17)
    GENESIS           = (0x02, 10) # YM2612 + SN76489
    SMS               = (0x03,  4) # SN76489
    GB                = (0x04,  4) # LR53902
    PCE               = (0x05,  6) # HuC6280
    NES               = (0x06,  5) # RP2A03
    C64_8580          = (0x07,  4) # SID r8580
    SEGA_ARCADE       = (0x08, 13) # YM2151 + SegaPCM
    NEO_GEO_CD        = (0x09, 13)
    GENESIS_EX        = (0x42, 13) # YM2612 + SN76489
    SMS_JP            = (0x43, 13) # SN76489 + YM2413
    NES_VRC7          = (0x46, 11) # RP2A03 + YM2413
    C64_6581          = (0x47,  3) # SID r6581
    NEO_GEO_CD_EX     = (0x49, 16)
    AY38910           = (0x80,  3)
    AMIGA             = (0x81,  4) # Paula
    YM2151            = (0x82,  8)
    YM2612            = (0x83,  6)
    TIA               = (0x84,  2)
    VIC20             = (0x85,  4)
    PET               = (0x86,  1)
    SNES              = (0x87,  8) # SPC700
    VRC6              = (0x88,  3)
    OPLL              = (0x89,  9) # YM2413
    FDS               = (0x8a,  1)
    MMC5              = (0x8b,  3)
    N163              = (0x8c,  8)
    OPN               = (0x8d,  6) # YM2203
    PC98              = (0x8e, 16) # YM2608
    OPL               = (0x8f,  9) # YM3526
    OPL2              = (0x90,  9) # YM3812
    OPL3              = (0x91, 18) # YMF262
    MULTIPCM          = (0x92, 24)
    PC_SPEAKER        = (0x93,  1) # Intel 8253
    POKEY             = (0x94,  4)
    RF5C68            = (0x95,  8)
    WONDERSWAN        = (0x96,  4)
    SAA1099           = (0x97,  6)
    OPZ               = (0x98,  8)
    POKEMON_MINI      = (0x99,  1)
    AY8930            = (0x9a,  3)
    SEGAPCM           = (0x9b, 16)
    VIRTUAL_BOY       = (0x9c,  6)
    VRC7              = (0x9d,  6)
    YM2610B           = (0x9e, 16)
    ZX_BEEPER         = (0x9f,  6)
    YM2612_EX         = (0xa0,  9)
    SCC               = (0xa1,  5)
    OPL_DRUMS         = (0xa2, 11)
    OPL2_DRUMS        = (0xa3, 11)
    OPL3_DRUMS        = (0xa4, 20)
    NEO_GEO           = (0xa5, 14)
    NEO_GEO_EX        = (0xa6, 17)
    OPLL_DRUMS        = (0xa7, 11)
    LYNX              = (0xa8,  4)
    SEGAPCM_DMF       = (0xa9,  5)
    MSM6295           = (0xaa,  4)
    MSM6258           = (0xab,  1)
    COMMANDER_X16     = (0xac, 17)
    BUBBLE_SYSTEM_WSG = (0xad,  2)
    SETA              = (0xae, 16)
    YM2610B_EX        = (0xaf, 19)
    QSOUND            = (0xe0, 19)

    def __new__(cls, id, channels):
        member = object.__new__(cls)
        member._value_ = id
        member.channels = channels
        return member

    def __repr__(self):
        return self.name

class FurnaceModule:
    """
    A representation of a FurnaceTracker module is contained
    within an instance's `module` variable.
    """

    def __init__(self, file_name=None, stream=None):
        """
        Initializes either an "empty" FurnaceTracker module, or, if
        supplied either a file name or a stream, deserializes a FurnaceTracker
        module from that.
        """
        self.file_name = None
        self.module = {
            "meta": {},
            "timing": {},
            "order": [],
            "patterns": [],
            "instruments": [],
            "wavetables": [],
            "chips": {},
            "info": {
                "masterVolume": 2.0
            }
        }

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
        print("TODO: current position in file: $%x" % stream.tell())

    def __read_header(self, stream):
        if stream.read(16) != FUR_STRING:
            raise Exception("Invalid Furnace module (magic number invalid)")
        # read version number
        self.module["meta"]["version"] = read_as_single("H", stream)
        self.__version = self.module["meta"]["version"]
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
        self.module["timing"]["timebase"] = read_as_single("B", stream) # 0-indexed
        self.module["timing"]["speed"] = read_as("BB", stream)
        self.module["timing"]["arpSpeed"] = read_as_single("B", stream)
        self.module["timing"]["clockSpeed"] = read_as_single("f", stream)

        # length of patterns
        self.module["info"]["patternLength"] = read_as_single("H", stream)
        self.__len_patterns = self.module["info"]["patternLength"]
        len_orders = read_as_single("H", stream)

        # highlights
        self.module["timing"]["highlight"] = read_as("BB", stream)

        num_instruments = read_as_single("H", stream)
        num_waves = read_as_single("H", stream)
        num_samples = read_as_single("H", stream)
        num_patterns = read_as_single("I", stream)

        # chip settings
        self.module["chips"]["list"] = []
        self.module["chips"]["volumes"] = []
        self.module["chips"]["panning"] = []
        self.module["chips"]["settings"] = []
        # soundchip list
        for chip_id in stream.read(32):
            if chip_id == 0:
                break;
            try:
                self.module["chips"]["list"].append( FurnaceChip(chip_id) )
            except ValueError:
                pass

        for i in range(32):
            self.module["chips"]["volumes"].append( read_as_single("b", stream) / 64 )

        for i in range(32):
            self.module["chips"]["panning"].append( read_as_single("b", stream) )

        for i in range(32):
            self.module["chips"]["settings"].append( stream.read(4) )

        # fill in metadata
        self.module["meta"]["name"] = read_as("string", stream)
        self.module["meta"]["author"] = read_as("string", stream)
        self.module["info"]["tuning"] = read_as_single("f", stream)

        # compat flags are blobs for now
        self.module["compatFlags"] = [stream.read(20)]

        self.__loc_instruments = [read_as_single("I", stream) for i in range(num_instruments)]
        self.__loc_waves = [read_as_single("I", stream) for i in range(num_waves)]
        self.__loc_samples = [read_as_single("I", stream) for i in range(num_samples)]
        self.__loc_patterns = [read_as_single("I", stream) for i in range(num_patterns)]

        # how many channels are there in total?
        num_channels = 0
        for chip in self.module["chips"]["list"]:
            num_channels += chip.channels

        # load orders
        self.module["order"] = {}
        for channel in range(num_channels):
            self.module["order"][channel] = []
            for order in range(len_orders):
                self.module["order"][channel].append(read_as_single("B", stream))

        # load channel settings
        self.module["info"]["effectColumns"] = []
        self.module["info"]["channelsShown"] = []
        self.module["info"]["channelsCollapsed"] = []
        self.module["info"]["channelNames"] = []
        self.module["info"]["channelAbbreviations"] = []

        # number of FX columns
        for channel in range(num_channels):
            self.module["info"]["effectColumns"].append(read_as_single("B", stream))

        # channels shown
        for channel in range(num_channels):
            status = read_as_single("B", stream)
            if status:
                self.module["info"]["channelsShown"].append(True)
            else:
                self.module["info"]["channelsShown"].append(False)

        # channels collapsed
        for channel in range(num_channels):
            status = read_as_single("B", stream)
            if status:
                self.module["info"]["channelsCollapsed"].append(True)
            else:
                self.module["info"]["channelsCollapsed"].append(False)

        # channel names shown in frame window
        for channel in range(num_channels):
            self.module["info"]["channelNames"].append(read_as("string", stream))

        # channel names shown in order window
        for channel in range(num_channels):
            self.module["info"]["channelAbbreviations"].append(read_as("string", stream))

        self.module["meta"]["comment"] = read_as("string", stream)

        if (self.__version >= 59):
            self.module["info"]["masterVolume"] = read_as_single("f", stream)

        extendedCompat = b''
        if (self.__version >= 70):
            extendedCompat += stream.read(1)
        if (self.__version >= 71):
            extendedCompat += stream.read(3)

    def __read_instruments(self, stream):
        # TODO
        print("TODO: instrument pointers ->", end=" ")
        for i in self.__loc_instruments:
            print("$%04x" % i, end=" ")
        print()

    def __read_wavetables(self, stream):
        # TODO
        print("TODO: wavetable pointers  ->", end=" ")
        for i in self.__loc_waves:
            print("$%04x" % i, end=" ")
        print()

    def __read_samples(self, stream):
        # TODO
        print("TODO: sample pointers     ->", end=" ")
        for i in self.__loc_samples:
            print("$%04x" % i, end=" ")
        print()

    def __read_patterns(self, stream):
        # TODO
        print("TODO: pattern pointers    ->", end=" ")
        for i in self.__loc_patterns:
            print("$%04x" % i, end=" ")
        print()

if __name__ == "__main__":
    import sys
    import pprint
    pp = pprint.PrettyPrinter(4)

    module = FurnaceModule(file_name=sys.argv[1])
    pp.pprint(module.module)
