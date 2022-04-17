#!/usr/bin/env python3
import sys
from enum import Enum, auto
import struct
from furnacelib import FurnaceInstrument

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

class EnumShowNameOnly(Enum):
    """
    Just an Enum, except if you `print` 'em it'll just show the
    name of the enum and not also its class.
    """
    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()

# TODO: finish these and copy these three classes to ../famitracker
class FamitrackerInstType(EnumShowNameOnly):
    """
    Instrument types registered in Famitracker
    """
    INST_NONE = 0
    INST_2A03 = 1
    INST_VRC6 = 2
    INST_VRC7 = 3
    INST_FDS  = 4
    INST_N163 = 5
    INST_S5B  = 6

class FamitrackerSeqSpecials(EnumShowNameOnly):
    SEQ_LOOP = auto()
    SEQ_RELEASE = auto()

class FamitrackerInstrument:
    def __init__(self, file_name=None):
        self.name = None
        self.type = None
        self.macros = {}
        self.data = {}
        
        if file_name:
            with open(file_name, "rb") as fi:
                self.load_from_stream(fi)
    
    def load_from_stream(self, stream):
        # redirect to these loading functions when the type is set
        redirection_funct = {
            FamitrackerInstType.INST_NONE: self.__read_null_instrument,
            FamitrackerInstType.INST_2A03: self.__read_2a03_instrument,
            FamitrackerInstType.INST_VRC6: self.__read_vrc6_instrument,
            FamitrackerInstType.INST_VRC7: self.__read_vrc7_instrument,
            FamitrackerInstType.INST_FDS:  self.__read_fds_instrument,
            FamitrackerInstType.INST_N163: self.__read_n163_instrument,
            FamitrackerInstType.INST_S5B:  self.__read_s5b_instrument,
        }
        
        self.__read_header(stream)
        redirection_funct[self.type](stream)
        
    def __read_header(self, stream):
        # skip magic number
        stream.read(
            len("FTI2.4")
        )
        
        # instrument type
        self.type = FamitrackerInstType(
            read_as_single("b", stream)
        )
        
        # instrument name
        name_length = read_as_single("i", stream)
        self.name = stream.read(name_length).decode("ascii")
        
    def __read_null_instrument(self, stream):
        pass
    
    def __read_general_macros(self, stream):
        num_macros = read_as_single("b", stream)
        
        macro_names = ["volume", "arp", "pitch", "hipitch", "duty"]
        
        for macro_num in range(num_macros):
            enabled = read_as_single("b", stream)
            
            if enabled:
                sizes = {
                    "macroLength": read_as_single("i", stream),
                    "loopPos": read_as_single("i", stream),
                    "relPos": read_as_single("i", stream),
                    "setting": read_as_single("i", stream)
                }
                macro = []
                for i in range(sizes["macroLength"]):
                    macro.append( read_as_single("b", stream) )
                
                if sizes["loopPos"] > -1:
                    macro.insert( sizes["loopPos"], FamitrackerSeqSpecials.SEQ_LOOP )
                    
                if sizes["relPos"] > -1:
                    macro.insert( sizes["relPos"]+1, FamitrackerSeqSpecials.SEQ_RELEASE )
                
                self.macros[ macro_names[macro_num] ] = macro
                
                if macro_names[macro_num] == "arp":
                    self.data["isArpFixed"] = (True if sizes["setting"] else False)
        
    def __read_2a03_instrument(self, stream):
        self.__read_general_macros(stream)
        # dpcm is not used
    
    def __read_vrc6_instrument(self, stream):
        self.__read_general_macros(stream)
    
    def __read_vrc7_instrument(self, stream):
        self.data = {
            "patchNum": read_as_single("i", stream),
            "customParams": [int.from_bytes(x, "little") for x in read_as("cccccccc", stream)]
        }
    
    def __read_fds_instrument(self, stream):
        pass # XXX TODO
    
    def __read_n163_instrument(self, stream):
        pass # XXX TODO
    
    def __read_s5b_instrument(self, stream):
        pass # XXX TODO

if __name__ == "__main__":
    inst = FamitrackerInstrument(sys.argv[1])
    print("name:   ", inst.name)
    print("type:   ", inst.type)
    print("macros: ", inst.macros)
    print("data:   ", inst.data)
    
    # TODO: implement the furnace instrument exporter
    out_inst = FurnaceInstrument()