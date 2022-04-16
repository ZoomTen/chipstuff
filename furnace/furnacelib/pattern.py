import zlib
import io
from .util import read_as, read_as_single, write_as
from .types import FurnaceChip, FurnaceNote, FurnaceInstrumentType, FurnaceMacroItem

class FurnacePattern:
    """
    stream_info = {
        "effectColumns": <int>,
        "patternLength": <int>
    }
    """
    # does it even have a separate file format??
    def __init__(self, init_data=None, file_name=None, stream=None, stream_info=None):
        self.channel = 0
        self.index = 0
        self.data = []
        self.name = ""

        if stream is not None:
            if stream_info is not None:
                self.load_from_stream(stream, stream_info)
        elif init_data is not None:
            self.channel = init_data["channel"]
            self.index = init_data["index"]
            self.name = init_data["name"]
            self.data = init_data["data"]

    def load_from_file(self, file_name):
        pass

    def load_from_bytes(self, bytes):
        pass

    def load_from_stream(self, stream, stream_info):
        self.__read_pattern(stream, stream_info)
    
    def save_to_stream(self, stream):
        stream.write(b"PATR")
        stream.write(b"\x00" * 4) # reserved
        write_as("hh", (self.channel, self.index,), stream)
        stream.write(b"\x00" * 4) # reserved
        for i in self.data:
            write_as("h", (i["note"].value,), stream)
            if i["note"] == FurnaceNote.C_:
                write_as("h", (i["octave"] - 1,), stream)
            else:
                write_as("h", (i["octave"],), stream)
            write_as("h", (i["instrument"],), stream)
            write_as("h", (i["volume"],), stream)
            for fx in i["effects"]:
                write_as("hh", fx, stream)
            write_as("string", self.name, stream)

    def __read_pattern(self, stream, stream_info):
        if stream.read(4) != b"PATR":
            raise Exception("Not a pattern?")
        
        stream.read(4) # reserved
        
        self.channel = read_as_single("H", stream)
        self.index = read_as_single("H", stream)
        
        stream.read(4) # reserved
        
        effects = stream_info["effectColumns"][self.channel]
        pattern_length = stream_info["patternLength"]
        
        for p in range(pattern_length):
            new_row = {}
            new_row["note"] = read_as_single("H", stream)
            new_row["note"] = FurnaceNote(new_row["note"])

            new_row["octave"] = read_as_single("H", stream)

            # work around quirk, thanks Delek!
            if new_row["note"] == FurnaceNote.C_:
                new_row["octave"] += 1

            new_row["instrument"] = read_as_single("h", stream)

            new_row["volume"] = read_as_single("h", stream)

            new_row["effects"] = []
            for x in range(effects):
                new_row["effects"].append(read_as("hh", stream))

            self.data.append(new_row)

        self.name = read_as("string", stream)

    def __repr__(self):
        return "<Furnace pattern [ch.%2d, id.%2d] '%s'>" % (
            self.channel,
            self.index,
            self.name
        )
