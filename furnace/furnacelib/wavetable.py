import zlib
import io
from .util import read_as, read_as_single, write_as
from .types import FurnaceChip, FurnaceNote, FurnaceInstrumentType, FurnaceMacroItem


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

