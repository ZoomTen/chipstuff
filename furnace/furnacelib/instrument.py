import zlib
import io
from .util import read_as, read_as_single, write_as
from .types import FurnaceChip, FurnaceNote, FurnaceInstrumentType, FurnaceMacroItem

class FurnaceInstrument:
    # TODO: make it read .fui files
    def __init__(self, file_name=None, stream=None):
        self.data = {}
        self.version = None
        self.type = None
        self.name = None
        self.wavetables = []
        self.samples = []

        if type(file_name) is str:
            self.load_from_file(file_name)
        elif stream is not None:
            self.load_from_stream(stream)

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

    def __read_opl_drums(self, stream):
        self.data["oplDrums"] = {}
        self.data["oplDrums"]["fixedFreq"] = read_as_single("b", stream)
        stream.read(1) # reserved
        self.data["oplDrums"]["kickFreq"] = read_as_single("h", stream)
        self.data["oplDrums"]["snareHiFreq"] = read_as_single("h", stream)
        self.data["oplDrums"]["tomTopFreq"] = read_as_single("h", stream)

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

    def __read_n163_data(self, stream):
        self.data["n163"] = {
            "waveInit": read_as_single("i", stream),
            "wavePos": read_as_single("b", stream),
            "waveLen": read_as_single("b", stream),
            "waveMode": read_as_single("b", stream),
        }
        stream.read(1)

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
            self.data["macros"][i].insert( ex_macros_loop[i], FurnaceMacroItem.LOOP )
            self.data["macros"][i].insert( ex_macros_release[i], FurnaceMacroItem.RELEASE )

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

    def __read_opz_data(self, stream):
        self.data["opz"] = {
            "fms2": read_as_single("b", stream),
            "ams2": read_as_single("b", stream),
        }

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
        if self.version >= 82:
            self.data["amiga"]["mode"] = read_as_single("b", stream)
            self.data["amiga"]["waveLength"] = read_as_single("b", stream)
            stream.read(12) # reserved
        else:
            stream.read(14) # reserved

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

    def __repr__(self):
        return "<Furnace %s instrument '%s'>" % (
            self.type, self.name)

