import zlib
import io
from .util import read_as, read_as_single, write_as
from .types import FurnaceChip, FurnaceNote, FurnaceInstrumentType, FurnaceMacroItem

class FurnaceSample:
    # does it even have a separate file format??
    def __init__(self, file_name=None, stream=None):
        self.data = []
        self.info = {
            "sampleRate": None,
            "depth": None,
            "name": None,
            "volume": None,
            "pitch": None
        }

        if type(file_name) is str:
            self.load_from_file(file_name)
        elif stream is not None:
            self.load_from_stream(stream)

    def load_from_file(self, file_name):
        pass

    def load_from_bytes(self, bytes):
        pass

    def load_from_stream(self, stream):
        self.__read_header_and_sample(stream)

    def __read_header_and_sample(self, stream):
        if stream.read(4) != b"SMPL":
            raise Exception("Not a wavetable?")
        stream.read(4) # reserved

        self.info["name"] = read_as("string", stream)

        length = read_as_single("i", stream)
        self.info["sampleRate"] = read_as_single("i", stream)
        self.info["volume"] = read_as_single("h", stream)
        self.info["pitch"] = read_as_single("h", stream)
        self.info["depth"] = FurnaceSampleType( read_as_single("b", stream) )

        stream.read(1)

        self.info["baseRate"] = read_as_single("h", stream)
        self.info["loopPoint"] = read_as_single("i", stream)

        # how do I check versions in isolation??
        for i in range(length):
            self.data.append(read_as_single("b", stream))

    def __repr__(self):
        return "<Furnace wavetable '%s'>" % ( self.name )

