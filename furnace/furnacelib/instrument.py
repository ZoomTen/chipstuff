import zlib
import io
from copy import deepcopy
from .util import read_as, read_as_single, write_as
from .types import FurnaceChip, FurnaceNote, FurnaceInstrumentType, FurnaceMacroItem

class FurnaceInstrument:
    def __init__(self, make_new=False, file_name=None, stream=None):
        self.data = {}
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

    def make_new(self):
        self.data = {
            "fm": {
                "alg": 0,"feedback": 4,
                "fms": 0,"ams": 0,
                "opCount": 2,"opll": 0,
                "ops": [
                    {
                        "am": 0,"ar": 31,"dr": 8,"mult": 5,
                        "rr": 3,"sl": 15,"tl": 42,"dt2": 0,
                        "rs": 0,"dt": 5,"d2r": 0,"ssgEnv": 0,
                        "dam": 0,"dvb": 0,"egt": 0,"ksl": 0,
                        "sus": 0,"vib": 0,"ws": 0,"ksr": 0,
                    },
                    {
                        "am": 0,"ar": 31,"dr": 4,"mult": 1,
                        "rr": 1,"sl": 11,"tl": 48,"dt2": 0,
                        "rs": 0,"dt": 5,"d2r": 0,"ssgEnv": 0,
                        "dam": 0,"dvb": 0,"egt": 0,"ksl": 0,
                        "sus": 0,"vib": 0,"ws": 0,"ksr": 0,
                    },
                    {
                        "am": 0,"ar": 31,"dr": 10,"mult": 1,
                        "rr": 4,"sl": 15,"tl": 18,"dt2": 0,
                        "rs": 0,"dt": 0,"d2r": 0,"ssgEnv": 0,
                        "dam": 0,"dvb": 0,"egt": 0,"ksl": 0,
                        "sus": 0,"vib": 0,"ws": 0,"ksr": 0,
                    },
                    {
                        "am": 0,"ar": 31,"dr": 9,"mult": 1,
                        "rr": 9,"sl": 15,"tl": 2,"dt2": 0,
                        "rs": 0,"dt": 0,"d2r": 0,"ssgEnv": 0,
                        "dam": 0,"dvb": 0,"egt": 0,"ksl": 0,
                        "sus": 0,"vib": 0,"ws": 0,"ksr": 0,
                    },
                ],
            },
            "gameboy": {"volume": 15, "direction": 0, "length": 2, "soundLength": 64},
            "c64": {
                "triangle": 0,"saw": 1,"pulse": 0,"noise": 0,
                "adsr": (0, 8, 0, 0),"duty": 2048,
                "ringMod": 0,"oscSync": 0,
                "toFilter": 0,"initFilter": 0,
                "volMacroAsCutoff": 0,"resonance": 0,
                "lowPass": 0,"bandPass": 0,"highPass": 0,
                "ch3Off": 0,"cutoff": 0,
                "absDutyMacro": 0,"absFilterMacro": 0,
            },
            "amiga": {"sampleId": 0, "mode": 0, "waveLength": 31},
            "macros": {
                "volume": [],"arp": [],"duty": [],"wave": [],"pitch": [],
                "x1": [], "x2": [],"x3": [],"alg": [],"feedback": [],
                "fms": [],"ams": [],"arpMode": 0,
                "ops": [
                    {
                        "am": [],"ar": [],"dr": [],"mult": [],
                        "rr": [],"sl": [],"tl": [],"dt2": [],
                        "rs": [],"dt": [],"d2r": [],"ssgEnv": [],
                        "dam": [],"dvb": [],"egt": [],"ksl": [],
                        "sus": [],"vib": [],"ws": [],"ksr": [],
                    },{
                        "am": [],"ar": [],"dr": [],"mult": [],
                        "rr": [],"sl": [],"tl": [],"dt2": [],
                        "rs": [],"dt": [],"d2r": [],"ssgEnv": [],
                        "dam": [],"dvb": [],"egt": [],"ksl": [],
                        "sus": [],"vib": [],"ws": [],"ksr": [],
                    },{
                        "am": [],"ar": [],"dr": [],"mult": [],
                        "rr": [],"sl": [],"tl": [],"dt2": [],
                        "rs": [],"dt": [],"d2r": [],"ssgEnv": [],
                        "dam": [],"dvb": [],"egt": [],"ksl": [],
                        "sus": [],"vib": [],"ws": [],"ksr": [],
                    },{
                        "am": [],"ar": [],"dr": [],"mult": [],
                        "rr": [],"sl": [],"tl": [],"dt2": [],
                        "rs": [],"dt": [],"d2r": [],"ssgEnv": [],
                        "dam": [],"dvb": [],"egt": [],"ksl": [],
                        "sus": [],"vib": [],"ws": [],"ksr": [],
                    },
                ],
                "leftPan": [],"rightPan": [], "phaseReset": [],
                "x4": [],"x5": [],"x6": [],"x7": [],"x8": [],
            },
            "oplDrums": {
                "fixedFreq": 0,"kickFreq": 1312,
                "snareHiFreq": 1360,"tomTopFreq": 448,
            },
            "sampleEx": [],
            "n163": {"waveInit": -1, "wavePos": 0, "waveLen": 32, "waveMode": 3},
            "fds": {
                "modSpeed": 0,
                "modDepth": 0,
                "modInit": 0,
                "modTable": [0] * 32,
            },
            "opz": {"fms2": 0, "ams2": 0},
            "waveSynth": {
                "wave1": 0,"wave2": 0,
                "rateDiv": 1,"effect": 0,
                "enabled": 0,"global": 0,
                "speed": 0,"params": [0, 0, 0, 0],
            },
        }
        self.version = 84
        self.type = FurnaceInstrumentType.STANDARD
        self.name = "Blank instrument"
        self.wavetables = []
        self.samples = []
        
    def load_from_file(self, file_name):
        """
        Deserializes a .fui file. Automatically detects compressed or
        uncompressed files.
        """
        self.file_name = file_name
        with open(file_name, "rb") as stream:
            if stream.read(16) != b"-Furnace instr.-":
                raise Exception("Not an instrument file?")
            
            stream.read(2) # format version, not sure if this is relevant
            stream.read(2) # reserved
            
            inst_loc = read_as_single("i", stream)
            num_wavetables = read_as_single("h", stream)
            num_samples    = read_as_single("h", stream)
            stream.read(4) # reserved
            # TODO: populate wavetables
            # TODO: populate samples
            
            self.load_from_stream(stream)

    def save_to_file(self, file_name):
        with open(file_name, "wb") as stream:
            stream.write(b"-Furnace instr.-")
            stream.write( int.to_bytes(self.version, 2, 'little') )
            
            stream.write(b"\x00\x00") # reserved
            
            stream.write(b"\x20\x00\x00\x00") # XXX: inst_loc, assume 0x20
            stream.write(b"\x00\x00") # XXX: wavetables
            stream.write(b"\x00\x00") # XXX: samples
            
            stream.write(b"\x00\x00\x00\x00") # reserved
            
            self.save_to_stream(stream)

    def load_from_stream(self, stream):
        self.__read_header(stream)
        self.__read_fm(stream)
        self.__read_gameboy(stream)
        self.__read_c64(stream)
        self.__read_amiga(stream)
        self.__read_standard(stream)
        if self.version >= 29:
            self.__read_op_macros(stream)
        if self.version >= 44:
            self.__read_release_points(stream)
            self.__read_op_release_points(stream)
        if self.version >= 61:
            self.__read_ex_op_macros(stream)
        if self.version >= 63:
            self.__read_opl_drums(stream)
        if self.version >= 67:
            self.__read_ex_sample_data(stream)
        if self.version >= 73:
            self.__read_n163_data(stream)
        if self.version >= 76:
            self.__read_ex_macros(stream)
            self.__read_fds_data(stream)
        if self.version >= 77:
            self.__read_opz_data(stream)
        if self.version >= 79:
            self.__read_wavesynth_data(stream)

    def save_to_stream(self, stream):
        self.__save_header(stream)
        self.__save_fm(stream)
        self.__save_gameboy(stream)
        self.__save_c64(stream)
        self.__save_amiga(stream)
        self.__save_standard(stream)
        if self.version >= 29:
            self.__save_op_macros(stream)
        if self.version >= 44:
            self.__save_release_points(stream)
            self.__save_op_release_points(stream)
        if self.version >= 61:
            self.__save_ex_op_macros(stream)
        if self.version >= 63:
            self.__save_opl_drums(stream)
        if self.version >= 67:
            self.__save_ex_sample_data(stream)
        if self.version >= 73:
            self.__save_n163_data(stream)
        if self.version >= 76:
            self.__save_ex_macros(stream)
            self.__save_fds_data(stream)
        if self.version >= 77:
            self.__save_opz_data(stream)
        if self.version >= 79:
            self.__save_wavesynth_data(stream)

# Operator macros

    def __read_op_macros(self, stream):
        self.data["macros"]["ops"] = []
        op_macro_lengths = {
            "am": [],
            "ar": [],
            "dr": [],
            "mult": [],
            "rr": [],
            "sl": [],
            "tl": [],
            "dt2": [],
            "rs": [],
            "dt": [],
            "d2r": [],
            "ssgEnv": []
        }
        op_macro_loops = {}
        for i in op_macro_lengths:
            op_macro_loops[i] = []

        # read the actual macros
        for op in range(4):
            for i in op_macro_lengths:
                op_macro_lengths[i].append( read_as_single("i", stream) )
            for i in op_macro_lengths:
                op_macro_loops[i].append( read_as_single("i", stream) )
            # XXX: skip open
            stream.read(12)

        for op in range(4):
            new_op = {}
            for i in op_macro_lengths:
                new_op[i] = []
            for i in op_macro_lengths:
                for j in range( op_macro_lengths[i][op] ):
                    new_op[i].append( read_as_single("b", stream) )
            for i in op_macro_loops:
                selected = op_macro_loops[i][op]
                if selected > -1:
                    new_op[i].insert(selected, FurnaceMacroItem.LOOP)
            self.data["macros"]["ops"].append(new_op)
    
    def __save_op_macros(self, stream):
        for opdata in self.data["macros"]["ops"]:
            order = [\
                "am","ar","dr","mult","rr","sl","tl","dt2","rs","dt",\
                "d2r","ssgEnv"\
            ]
            # get raw macros
            raw_macros = {}
            for param in order:
                raw_macros[param] = [\
                    x for x in filter( \
                        lambda x: isinstance(x, int), \
                        opdata[param] \
                    )\
                ]
            
            # length
            for param in order:
                write_as("i", (len(opdata[param]),), stream)
            
            # loop
            for param in order:
                try:
                    write_as("i", (opdata[param].index(FurnaceMacroItem.LOOP),), stream)
                except ValueError:
                    write_as("i", (-1,), stream)
            
            # open
            for param in order:
                write_as("b", (0,), stream)
            
            # data
            for param in order:
                write_as(\
                    "b" * len(raw_macros[param]),
                    raw_macros[param],
                    stream
                )

# Release points

    def __read_release_points(self, stream):
        release_points = {
            "volume": read_as_single("i", stream),
            "arp": read_as_single("i", stream),
            "duty": read_as_single("i", stream),
            "wave": read_as_single("i", stream),
            "pitch": read_as_single("i", stream),
            "x1": read_as_single("i", stream),
            "x2": read_as_single("i", stream),
            "x3": read_as_single("i", stream),
            "alg": read_as_single("i", stream),
            "feedback": read_as_single("i", stream),
            "fms": read_as_single("i", stream),
            "ams": read_as_single("i", stream)
        }
        for i in release_points:
            if release_points[i] > -1:
                self.data["macros"][i].insert(release_points[i], FurnaceMacroItem.RELEASE)

    def __save_release_points(self, stream):
        rel_point_names = [\
            "volume", "arp", "duty", "wave", "pitch", "x1", "x2", "x3",\
            "alg", "feedback", "fms", "ams"\
        ]
        for name in rel_point_names:
            try:
                write_as("i", (self.data["macros"][name].index(FurnaceMacroItem.RELEASE),), stream)
            except ValueError:
                write_as("i", (-1,), stream)

# Operator release points

    def __read_op_release_points(self, stream):
        op_macro_releases = {
            "am": [],
            "ar": [],
            "dr": [],
            "mult": [],
            "rr": [],
            "sl": [],
            "tl": [],
            "dt2": [],
            "rs": [],
            "dt": [],
            "d2r": [],
            "ssgEnv": []
        }
        for op in range(4):
            for i in op_macro_releases:
                op_macro_releases[i].append( read_as_single("i", stream) )

        for op in range(4):
            for i in op_macro_releases:
                selected = op_macro_releases[i][op]
                if selected > -1:
                    self.data["macros"]["ops"][op][i].insert(selected, FurnaceMacroItem.LOOP)

    def __save_op_release_points(self, stream):
        macro_rel_names = [\
            "am", "ar", "dr", "mult", "rr", "sl", "tl", "dt2", "rs", "dt", "d2r", "ssgEnv"\
        ]
        for op in range(4):
            for name in macro_rel_names:
                try:
                    write_as("i", (\
                        self.data["macros"]["ops"][op][name].index(FurnaceMacroItem.RELEASE),\
                    ), stream)
                except ValueError:
                    write_as("i", (-1,), stream)

# Extended Operator macros

    def __read_ex_op_macros(self, stream):
        op_macro_lengths = {
            "dam": [],
            "dvb": [],
            "egt": [],
            "ksl": [],
            "sus": [],
            "vib": [],
            "ws": [],
            "ksr": []
        }
        op_macro_loops = {}
        op_macro_releases = {}
        for i in op_macro_lengths:
            op_macro_loops[i] = []
            op_macro_releases[i] = []

        # read the actual macros
        for op in range(4):
            for i in op_macro_lengths:
                op_macro_lengths[i].append( read_as_single("i", stream) )
            for i in op_macro_lengths:
                op_macro_loops[i].append( read_as_single("i", stream) )
            for i in op_macro_lengths:
                op_macro_releases[i].append( read_as_single("i", stream) )
            # XXX: skip open
            stream.read(8)

        for op in range(4):
            for i in op_macro_lengths:
                self.data["macros"]["ops"][op][i] = []
            for i in op_macro_lengths:
                for j in range( op_macro_lengths[i][op] ):
                    self.data["macros"]["ops"][op][i].append( read_as_single("b", stream) )
            for i in op_macro_loops:
                selected = op_macro_loops[i][op]
                if selected > -1:
                    self.data["macros"]["ops"][op][i].insert(selected, FurnaceMacroItem.LOOP)
            for i in op_macro_releases:
                selected = op_macro_releases[i][op]
                if selected > -1:
                    self.data["macros"]["ops"][op][i].insert(selected, FurnaceMacroItem.RELEASE)

    def __save_ex_op_macros(self, stream):
        for opdata in self.data["macros"]["ops"]:
            order = [\
                "dam","dvb","egt","ksl","sus","vib","ws","ksr"\
            ]
            # get raw macros
            raw_macros = {}
            for param in order:
                raw_macros[param] = [\
                    x for x in filter( \
                        lambda x: isinstance(x, int), \
                        opdata[param] \
                    )\
                ]
            
            # length
            for param in order:
                write_as("i", (len(opdata[param]),), stream)
            
            # loop
            for param in order:
                try:
                    write_as("i", (opdata[param].index(FurnaceMacroItem.LOOP),), stream)
                except ValueError:
                    write_as("i", (-1,), stream)
            
            # release
            for param in order:
                try:
                    write_as("i", (opdata[param].index(FurnaceMacroItem.RELEASE),), stream)
                except ValueError:
                    write_as("i", (-1,), stream)
            
            # open
            for param in order:
                write_as("b", (0,), stream)
            
            # data
            for param in order:
                write_as(\
                    "b" * len(raw_macros[param]),
                    raw_macros[param],
                    stream
                )

# OPL Drums

    def __read_opl_drums(self, stream):
        self.data["oplDrums"] = {}
        self.data["oplDrums"]["fixedFreq"] = read_as_single("b", stream)
        stream.read(1) # reserved
        self.data["oplDrums"]["kickFreq"] = read_as_single("h", stream)
        self.data["oplDrums"]["snareHiFreq"] = read_as_single("h", stream)
        self.data["oplDrums"]["tomTopFreq"] = read_as_single("h", stream)

    def __save_opl_drums(self, stream):
        write_as("bbhhh",
            (
                self.data["oplDrums"]["fixedFreq"],
                0, # XXX reserved
                self.data["oplDrums"]["kickFreq"],
                self.data["oplDrums"]["snareHiFreq"],
                self.data["oplDrums"]["tomTopFreq"],
            ), stream
        )   

# Extended sample data

    def __read_ex_sample_data(self, stream):
        self.data["sampleEx"] = []
        if read_as_single("b", stream) != 0:
            frequency = []
            sample = []
            for i in range(120):
                frequency.append( read_as_single("i", stream) )
            for i in range(120):
                sample.append( read_as_single("h", stream) )

            for i in range(120):
                self.data["sampleEx"].append(
                    ( frequency[i], sample[i] )
                )

    def __save_ex_sample_data(self, stream):
        if len(self.data["sampleEx"]) > 0:
            write_as("b", (1,), stream)
            for map in self.data["sampleEx"]:
                write_as("i", (map[0],), stream)
            for map in self.data["sampleEx"]:
                write_as("h", (map[1],), stream)
        else:
            write_as("b", (0,), stream)

# N163 data

    def __read_n163_data(self, stream):
        self.data["n163"] = {
            "waveInit": read_as_single("i", stream),
            "wavePos": read_as_single("b", stream),
            "waveLen": read_as_single("b", stream),
            "waveMode": read_as_single("b", stream),
        }
        stream.read(1)

    def __save_n163_data(self, stream):
        write_as("ibbbb",
            (
                self.data["n163"]["waveInit"],
                self.data["n163"]["wavePos"],
                self.data["n163"]["waveLen"],
                self.data["n163"]["waveMode"],
                0, # XXX reserved
            ), stream
        )

# Extended macros

    def __read_ex_macros(self, stream):
        ex_macros_length = {
            "leftPan": read_as_single("i", stream),
            "rightPan": read_as_single("i", stream),
            "phaseReset": read_as_single("i", stream),
            "x4": read_as_single("i", stream),
            "x5": read_as_single("i", stream),
            "x6": read_as_single("i", stream),
            "x7": read_as_single("i", stream),
            "x8": read_as_single("i", stream),
        }
        ex_macros_loop = {}
        ex_macros_release = {}
        for i in ex_macros_length:
            ex_macros_loop[i] = read_as_single("i", stream)
        for i in ex_macros_length:
            ex_macros_release[i] = read_as_single("i", stream)
        # XXX skip open
        stream.read(8)

        for i in ex_macros_length:
            self.data["macros"][i] = []
            for j in range( ex_macros_length[i] ):
                self.data["macros"][i].append( read_as_single("i", stream) )
            if ex_macros_loop[i] > -1:
                self.data["macros"][i].insert( ex_macros_loop[i], FurnaceMacroItem.LOOP )
            if ex_macros_release[i] > -1:
                self.data["macros"][i].insert( ex_macros_release[i], FurnaceMacroItem.RELEASE )

    def __save_ex_macros(self, stream):
        order = [\
            "leftPan","rightPan","phaseReset","x4","x5","x6","x7","x8"\
        ]
        # get raw macros
        raw_macros = {}
        for param in order:
            raw_macros[param] = [\
                x for x in filter( \
                    lambda x: isinstance(x, int), \
                    self.data["macros"][param] \
                )\
            ]
        
        # length
        for param in order:
            write_as("i", (len(self.data["macros"][param]),), stream)
        
        # loop
        for param in order:
            try:
                write_as("i", (self.data["macros"][param].index(FurnaceMacroItem.LOOP),), stream)
            except ValueError:
                write_as("i", (-1,), stream)
        
        # release
        for param in order:
            try:
                write_as("i", (self.data["macros"][param].index(FurnaceMacroItem.RELEASE),), stream)
            except ValueError:
                write_as("i", (-1,), stream)
        
        # open
        for param in order:
            write_as("b", (0,), stream)
        
        # data
        for param in order:
            write_as(\
                "b" * len(raw_macros[param]),
                raw_macros[param],
                stream
            )

# FDS data

    def __read_fds_data(self, stream):
        self.data["fds"] = {
            "modSpeed": read_as_single("i", stream),
            "modDepth": read_as_single("i", stream),
            "modInit": read_as_single("b", stream),
            "modTable": []
        }

        # XXX skip open
        stream.read(3)

        for i in range(32):
            self.data["fds"]["modTable"].append( read_as_single("b", stream) )

    def __save_fds_data(self, stream):
        write_as("iibbbb",
            (
                self.data["fds"]["modSpeed"],
                self.data["fds"]["modDepth"],
                self.data["fds"]["modInit"],
                0,0,0 # reserved
            ), stream
        )
        write_as("b" * len(self.data["fds"]["modTable"]),
            self.data["fds"]["modTable"],
            stream
        )
        

# OPZ data

    def __read_opz_data(self, stream):
        self.data["opz"] = {
            "fms2": read_as_single("b", stream),
            "ams2": read_as_single("b", stream),
        }

    def __save_opz_data(self, stream):
        write_as("bb",
            (
                self.data["opz"]["fms2"],
                self.data["opz"]["ams2"],
            ),
            stream
        )

# Wavesynth data

    def __read_wavesynth_data(self, stream):
        self.data["waveSynth"] = {
            "wave1": read_as_single("i", stream),
            "wave2": read_as_single("i", stream),
            "rateDiv": read_as_single("b", stream),
            "effect": read_as_single("b", stream),
            "enabled": read_as_single("b", stream),
            "global": read_as_single("b", stream),
            "speed": read_as_single("b", stream),
            "params": [
                read_as_single("b", stream),
                read_as_single("b", stream),
                read_as_single("b", stream),
                read_as_single("b", stream)
             ]
        }

    def __save_wavesynth_data(self, stream):
        write_as("iibbbbbbbbb",
            (
                self.data["waveSynth"]["wave1"],
                self.data["waveSynth"]["wave2"],
                self.data["waveSynth"]["rateDiv"],
                self.data["waveSynth"]["effect"],
                self.data["waveSynth"]["enabled"],
                self.data["waveSynth"]["global"],
                self.data["waveSynth"]["speed"],
                *self.data["waveSynth"]["params"],
            ),
            stream
        )
        stream.write(b"\x00" * 19) # XXX idk why this is here

# Header

    def __read_header(self, stream):
        if stream.read(4) != b"INST":
            raise Exception("Not an instrument?")

        stream.read(4) # reserved
        self.version = read_as_single("H", stream)
        self.type = FurnaceInstrumentType(stream.read(1)[0])
        stream.read(1) # reserved
        self.name = read_as("string", stream)

    def __save_header(self, stream):
        stream.write(b"INST")
        
        stream.write(b"\x00" * 4) # reserved
        
        stream.write( int.to_bytes(self.version, 2, "little") )
        stream.write( int.to_bytes(self.type.value, 1, "little") )
        
        stream.write(b"\x00") # reserved
        
        write_as("string", self.name, stream)

# FM

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

    def __save_fm(self, stream):
        write_as("bbbbb",
            (
                self.data["fm"]["alg"],
                self.data["fm"]["feedback"],
                self.data["fm"]["fms"],
                self.data["fm"]["ams"],
                self.data["fm"]["opCount"],
            ), stream
        )
        if self.version >= 60:
            write_as("b", (self.data["fm"]["opll"],), stream)
        else:
            write_as("b", (0,), stream) # reserved
        
        stream.write(b"\x00" * 2) # reserved
        
        for op in self.data["fm"]["ops"]:
            write_as("bbbbbbbbbbbbbbbbbbbb",
                (
                    op["am"],
                    op["ar"],
                    op["dr"],
                    op["mult"],
                    op["rr"],
                    op["sl"],
                    op["tl"],
                    op["dt2"],
                    op["rs"],
                    op["dt"],
                    op["d2r"],
                    op["ssgEnv"],
                    op["dam"],
                    op["dvb"],
                    op["egt"],
                    op["ksl"],
                    op["sus"],
                    op["vib"],
                    op["ws"],
                    op["ksr"],
                ), stream
            )
            stream.write(b"\x00" * 12) # reserved

# Gameboy

    def __read_gameboy(self, stream):
        self.data["gameboy"] = {}
        self.data["gameboy"]["volume"]       = read_as_single("B", stream)
        self.data["gameboy"]["direction"]    = read_as_single("B", stream)
        self.data["gameboy"]["length"]       = read_as_single("B", stream)
        self.data["gameboy"]["soundLength"]  = read_as_single("B", stream)

    def __save_gameboy(self, stream):
        write_as("bbbb",
            (
                self.data["gameboy"]["volume"],
                self.data["gameboy"]["direction"],
                self.data["gameboy"]["length"],
                self.data["gameboy"]["soundLength"],
            ), stream
        )

# C64

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

    def __save_c64(self, stream):
        write_as("bbbbbbbbhbbbbbbbbbbhbb",
            (
                self.data["c64"]["triangle"],
                self.data["c64"]["saw"],
                self.data["c64"]["pulse"],
                self.data["c64"]["noise"],
                *self.data["c64"]["adsr"],
                self.data["c64"]["duty"],
                self.data["c64"]["ringMod"],
                self.data["c64"]["oscSync"],
                self.data["c64"]["toFilter"],
                self.data["c64"]["initFilter"],
                self.data["c64"]["volMacroAsCutoff"],
                self.data["c64"]["resonance"],
                self.data["c64"]["lowPass"],
                self.data["c64"]["bandPass"],
                self.data["c64"]["highPass"],
                self.data["c64"]["ch3Off"],
                self.data["c64"]["cutoff"],
                self.data["c64"]["absDutyMacro"],
                self.data["c64"]["absFilterMacro"],
            ), stream
        )

# Amiga

    def __read_amiga(self, stream):
        self.data["amiga"] = {}
        self.data["amiga"]["sampleId"] = read_as_single("H", stream)
        if self.version >= 82:
            self.data["amiga"]["mode"] = read_as_single("b", stream)
            self.data["amiga"]["waveLength"] = read_as_single("b", stream)
            stream.read(12) # reserved
        else:
            stream.read(14) # reserved

    def __save_amiga(self, stream):
        write_as("h",
            (
                self.data["amiga"]["sampleId"],
            ), stream
        )
        if self.version >= 82:
            write_as("bb",
                (
                    self.data["amiga"]["mode"],
                    self.data["amiga"]["waveLength"],
                ), stream
            )
            stream.write(b"\x00" * 12) # reserved
        else:
            stream.write(b"\x00" * 14) # reserved

# Standard

    def __read_standard(self, stream):
        self.data["macros"] = {}

        std_macro_lengths = {
            "volume": read_as_single("i", stream),
            "arp": read_as_single("i", stream),
            "duty": read_as_single("i", stream),
            "wave": read_as_single("i", stream),
        }
        
        if self.version >= 17:
            std_macro_lengths["pitch"] = read_as_single("i", stream)
            std_macro_lengths["x1"]    = read_as_single("i", stream)
            std_macro_lengths["x2"]    = read_as_single("i", stream)
            std_macro_lengths["x3"]    = read_as_single("i", stream)
        
        std_macro_loops = {
            "volume": read_as_single("i", stream),
            "arp": read_as_single("i", stream),
            "duty": read_as_single("i", stream),
            "wave": read_as_single("i", stream),
        }
        
        if self.version >= 17:
            std_macro_loops["pitch"] = read_as_single("i", stream)
            std_macro_loops["x1"]    = read_as_single("i", stream)
            std_macro_loops["x2"]    = read_as_single("i", stream)
            std_macro_loops["x3"]    = read_as_single("i", stream)

        arp_macro_mode = read_as_single("b", stream)

        if self.version >= 17:
            stream.read(3)
        elif self.version >= 15:
            self.data["macros"]["heights"] = {
                "volume": read_as_single("b", stream),
                "duty": read_as_single("b", stream),
                "wave": read_as_single("b", stream),
            }
        else:
            stream.read(3)

        std_macros = {}

        for key in std_macro_lengths:
            std_macros[key] = []
            for i in range(std_macro_lengths[key]):
                value = read_as_single("i", stream)
                if key == "arp": # TODO: check this
                    if self.version < 31:
                        value -= 12
                std_macros[key].append( value )

        if self.version >= 29:
            std_macro_lengths = {
                "alg": read_as_single("i", stream),
                "feedback": read_as_single("i", stream),
                "fms": read_as_single("i", stream),
                "ams": read_as_single("i", stream),
            }
            std_macro_loops["alg"] = read_as_single("i", stream)
            std_macro_loops["feedback"] = read_as_single("i", stream)
            std_macro_loops["fms"] = read_as_single("i", stream)
            std_macro_loops["ams"] = read_as_single("i", stream)

            # XXX skip macro open for now
            stream.read(12)

            # reread new macros
            for key in std_macro_lengths:
                std_macros[key] = []
                for i in range(std_macro_lengths[key]):
                    value = read_as_single("i", stream)
                    std_macros[key].append( value )

        for i in std_macros:
            if std_macro_loops[i] > -1:
                std_macros[i].insert(std_macro_loops[i], FurnaceMacroItem.LOOP)

        self.data["macros"] = std_macros
        self.data["macros"]["arpMode"] = arp_macro_mode

    def __save_standard(self, stream):
        #  extract macros
        raw_macros = {
            "volume": [],
            "arp": [],
            "duty": [],
            "wave": []
        }
        
        if self.version >= 17:
            raw_macros["pitch"] = []
            raw_macros["x1"] = []
            raw_macros["x2"] = []
            raw_macros["x3"] = []
        
        if self.version >= 29:
            raw_macros["alg"] = []
            raw_macros["feedback"] = []
            raw_macros["ams"] = []
            raw_macros["fms"] = []
        
        for key in raw_macros:
            raw_macros[key] = [x for x in filter( lambda x: isinstance(x, int), self.data["macros"][key] )]
        
        loop_points = {
            "volume": -1,
            "arp": -1,
            "duty": -1,
            "wave": -1,
            "pitch": -1,
            "x1": -1,
            "x2": -1,
            "x3": -1,
            "alg": -1,
            "feedback": -1,
            "ams": -1,
            "fms": -1,
        }
        
        for key in raw_macros:
            try:
                loop_points[key] = self.data["macros"][key].index( FurnaceMacroItem.LOOP )
            except ValueError:
                loop_points[key] = -1
        
        # actually write macros
        macro_names = ["volume", "arp", "duty", "wave"]
        if self.version >= 17:
            macro_names += ["pitch", "x1", "x2", "x3"]
        
        write_as("i" * len(macro_names),
            [ \
                len(raw_macros[x]) for x in macro_names \
            ], stream
        )
        write_as("i" * len(macro_names),
            [ \
                loop_points[x] for x in macro_names \
            ], stream
        )
        write_as("b", (self.data["macros"]["arpMode"],), stream)
        
        if self.version >= 17:
            stream.write(b"\x00" * 3)
        elif self.version >= 15:
            write_as("bbb",
                (
                    self.data["macros"]["heights"]["volume"],
                    self.data["macros"]["heights"]["duty"],
                    self.data["macros"]["heights"]["wave"],
                ), stream
            )
        else:
            stream.write(b"\x00" * 3)
        
        # write macro sequences
        for macro in macro_names:
            if (self.version < 31) and (macro == "arp"):
                write_as("i" * len(raw_macros[macro]),
                    [x+12 for x in raw_macros[macro]], stream
                )
            else:
                write_as("i" * len(raw_macros[macro]),
                    raw_macros[macro], stream
                )
        
        if self.version >= 29:
            macro_names = ["alg", "feedback", "fms", "ams"]
            write_as("i" * len(macro_names),
                [ \
                    len(raw_macros[x]) for x in macro_names \
                ], stream
            )
            write_as("i" * len(macro_names),
                [ \
                    loop_points[x] for x in macro_names \
                ], stream
            )
            # XXX skip open
            stream.write(b"\x00" * 12)
            # write macro sequences
            for macro in macro_names:
                write_as("i" * len(raw_macros[macro]),
                    raw_macros[macro], stream
                )

    def __repr__(self):
        return "<Furnace %s instrument '%s'>" % (
            self.type, self.name)

