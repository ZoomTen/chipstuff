import zlib
import io
from copy import deepcopy
from .util import read_as, read_as_single, write_as
from .types import FurnaceChip, FurnaceNote, FurnaceInstrumentType, FurnaceMacroItem, FurnaceMacroType, FurnaceMacroCode, FurnaceMacroSize
import struct

# Newer Furnace instrument type (>= 127)

class FurnaceInstrumentDX:
    def __init__(self, make_new=False, file_name=None, stream=None):
        self.data = [] # is feature blocks now
        self.version = None
        self.type = None
        self.name = None
        self.wavetables = []
        self.samples = []
        
        if make_new:
            self.make_new()
        else:
            if type(file_name) is str:
                self.load_from_file(file_name)
            elif stream is not None:
                self.load_from_stream(stream)

    def load_from_file(self):
        pass

    def load_from_stream(self, stream):
        self.__read_header(stream)
        self.__read_features(stream)

    def __read_header(self, stream):
        if stream.read(4) != b"INS2":
            raise Exception("Not an instrument?")
        stream.read(4) # skip size
        self.version = read_as_single("H", stream)
        self.type = FurnaceInstrumentType(read_as_single("H", stream))
    
    def __read_features(self, stream):
        while True:
            feature = FuiDXFeatureBlock.from_stream(stream)
            self.data.append(feature)
            if feature.code == "NA":
                # no way of really making it a pointer...
                self.name = feature.interpret_data()
            if feature.code == "EN":
                return

    def make_new(self):
        pass

    def __repr__(self):
        return "<Furnace dev127+ %s instrument '%s'>" % (
            self.type, self.name)

class FuiDXFeatureBlock:
    def __init__(self, code="NA", data=b""):
        if len(code.encode('ascii')) != 2:
            raise Exception("Feature code must be 2 characters long!")
        self.code = code
        self.data = data
    
    def from_stream(stream):
        code = stream.read(2).decode('ascii')
        size = read_as_single("H", stream)
        return FuiDXFeatureBlock(
            code=code,
            data=stream.read(size)
        )

    def serialize(self):
        if self.code == "EN":
            return b"EN"
        else:
            return 
            pass

    def interpret_data(self):
    # this will return a string or a dict
    # same format as before
        data = io.BytesIO(self.data)
        if self.code == "EN":
            return # EOF
        elif self.code == "NA":
            return read_as("string", data)
        elif self.code == "FM":
            return # TODO
        elif self.code == "MA":
            macro_list = []
            header_len = read_as_single("H", data)
            while True:
                new_macro = {}
                new_macro["kind"] = FurnaceMacroCode(read_as_single("B", data))
                if new_macro["kind"] == FurnaceMacroCode.STOP:
                    macro_list.append(new_macro)
                    return macro_list
                length = read_as_single("B", data)
                loop = read_as_single("B", data)
                release = read_as_single("B", data)
                mode = read_as_single("B", data)
                open_type_word = read_as_single("B", data)
                new_macro["open"] = open_type_word & 0b1
                new_macro["type"] = FurnaceMacroType((open_type_word & 0b110) >> 1)
                new_macro["wordSize"] = FurnaceMacroSize((open_type_word & 0b11000000) >> 6)
                new_macro["delay"] = read_as_single("B", data)
                new_macro["speed"] = read_as_single("B", data)
                macro_data = []
                for i in range(length):
                    entry = data.read(new_macro["wordSize"].num_bytes)
                    if new_macro["wordSize"] == FurnaceMacroSize.UINT8:
                        entry = struct.unpack("<B", entry)
                    elif new_macro["wordSize"] == FurnaceMacroSize.INT8:
                        entry = struct.unpack("<b", entry)
                    elif new_macro["wordSize"] == FurnaceMacroSize.INT16:
                        entry = struct.unpack("<h", entry)
                    elif new_macro["wordSize"] == FurnaceMacroSize.INT32:
                        entry = struct.unpack("<i", entry)
                    macro_data.append(entry[0])
                if new_macro["type"] == FurnaceMacroType.SEQUENCE:
                    if loop != 255:
                        macro_data.insert(loop, FurnaceMacroItem.LOOP)
                    if release != 255:
                        macro_data.insert(release, FurnaceMacroItem.RELEASE)
                new_macro["data"] = macro_data
                macro_list.append(new_macro)
            return macro_list
        elif self.code == "64":
            return # TODO
        elif self.code == "GB":
            env = read_as_single("B", data)
            vl = env & 0b1111
            dr = (env & 0b10000) >> 4
            ln = (env & 0b11100000) >> 5
            sl = read_as_single("B", data)
            fl = read_as_single("B", data)
            swe = bool(fl & 0b1)
            ie = bool(fl & 0b10)
            hwsl = read_as_single("B", data)
            hws = []
            for i in range(hwsl):
                hws.append(data.read(3))
            return {
                "envelope": {
                    "volume": vl,
                    "direction": dr,
                    "length": ln
                },
                "soundLength": sl,
                "flags": {
                    "softwareEnvelope": swe,
                    "initEnvelope": ie
                },
                "sequence": hws,
            }
        elif self.code == "SM":
            return # TODO
        elif self.code == "O1":
            return # TODO
        elif self.code == "O2":
            return # TODO
        elif self.code == "O3":
            return # TODO
        elif self.code == "O4":
            return # TODO
        elif self.code == "LD":
            return # TODO
        elif self.code == "SN":
            return # TODO
        elif self.code == "N1":
            return {
                "waveInit": read_as_single("i", data),
                "wavePos": read_as_single("b", data),
                "waveLen": read_as_single("b", data),
                "waveMode": read_as_single("b", data),
            }
        elif self.code == "FD":
            return # TODO
        elif self.code == "WS":
            return # TODO
        elif self.code == "SL":
            return # TODO
        elif self.code == "WL":
            return # TODO
        elif self.code == "MP":
            return # TODO
        elif self.code == "SU":
            return # TODO
        elif self.code == "ES":
            return # TODO
        elif self.code == "X1":
            return # TODO
    
    def __repr__(self):
        if self.code == "EN":
            return "<Terminator block>"
        elif self.code == "NA":
            return "<Name block '%s'>" % self.interpret_data()
        elif self.code == "FM":
            return "<FM instrument data>"
        elif self.code == "MA":
            return "<Macro data>"
        elif self.code == "64":
            return "<Commodore 64 instrument data>"
        elif self.code == "GB":
            return "<Game Boy instrument data>"
        elif self.code == "SM":
            return "<Sample instrument data>"
        elif self.code == "O1":
            return "<FM op 1 macros>"
        elif self.code == "O2":
            return "<FM op 2 macros>"
        elif self.code == "O3":
            return "<FM op 3 macros>"
        elif self.code == "O4":
            return "<FM op 4 macros>"
        elif self.code == "LD":
            return "<OPLL drums data>"
        elif self.code == "SN":
            return "<SNES instrument data>"
        elif self.code == "N1":
            return "<Namco 163 instrument data>"
        elif self.code == "FD":
            return "<FDS / Virtual Boy instrument data>"
        elif self.code == "WS":
            return "<Wavetable synth data>"
        elif self.code == "SL":
            return "<Sample list>"
        elif self.code == "WL":
            return "<Wavetable list>"
        elif self.code == "MP":
            return "<MultiPCM instrument data>"
        elif self.code == "SU":
            return "<Tildearrow Sound Unit instrument data>"
        elif self.code == "ES":
            return "<ES5506 instrument data>"
        elif self.code == "X1":
            return "<X1-010 instrument data>"
        return "<Instrument block '%s'>" % self.code

