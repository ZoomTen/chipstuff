#!/usr/bin/env python3

import struct
import re
from io import BytesIO
import sys

if __name__ == "__main__":
	if len(sys.argv) == 2:
		FILE = sys.argv[1]
	else:
		print("vgm2fui_OPM.py [vgm file]")
		print()
		print("Extracts YM2151 (OPM) preset data from a .vgm file")
		print("and saves it in their own .fui files (.fui version 27+)")
		print()
		print("- The VGM file must be uncompressed")
		print("- Instruments will be saved in the working directory")
		exit(0)
	
	# base template
	FILE_TEMPLATE = b'-Furnace instr.-\x1b\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00INST\x00\x00\x00\x00\x1b\x00\x01\x00Instrument 0\x00\x00\x04\x00\x00\x04\x00\x00\x00\x00\x1f\x08\x05\x03\x0f*\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1f\x04\x01\x01\x0b0\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1f\n\x01\x04\x0f\x12\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1f\t\x01\t\x0f\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0f\x00\x02@\x00\x01\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00'

	# virtual YM2151
	STATES = []
	INSTRUMENTS = []
	REGISTER_STATE = {
		0: {"alg": None, "feedback": None, "ops": {}},
		1: {"alg": None, "feedback": None, "ops": {}},
		2: {"alg": None, "feedback": None, "ops": {}},
		3: {"alg": None, "feedback": None, "ops": {}},
		4: {"alg": None, "feedback": None, "ops": {}},
		5: {"alg": None, "feedback": None, "ops": {}},
		6: {"alg": None, "feedback": None, "ops": {}},
		7: {"alg": None, "feedback": None, "ops": {}},
	}

	# add operators to channels
	for i in REGISTER_STATE:
		new_ops = {1: None, 2: None, 3: None, 4: None}
		for j in new_ops:
			new_ops[j] = {
				"dt": None,
				"ml": None,
				"tl": None,
				"rs": None,
				"a": None,
				"am": None,
				"d": None,
				"dt2": None,
				"d2": None,
				"s": None,
				"r": None,
			}
		REGISTER_STATE[i]["ops"] = new_ops

	def print_matches(sub):
	# process YM2151 register reads
		global REGISTER_STATE
		global INSTRUMENTS
		
		# extract values
		reg = int.from_bytes(sub.group(1), 'little')
		val = int.from_bytes(sub.group(2), 'little')
		
		# values in binary, stringify to extract the necessary values
		v_ = bin(val)[2:].zfill(8)
		channel = (int(hex(reg % 8)[-1]))
		
		# process VGM commands individually
		if (reg >= 0x20) and (reg <= 0x27):
			REGISTER_STATE[channel]["feedback"] = int(v_[2:4+1],2)
			REGISTER_STATE[channel]["alg"] = int(v_[5:7+1],2)
		
		elif (reg == 0x08):
			STATES.append(REGISTER_STATE)
		
		# DT1 (dt) / MUL (ml)
		elif (reg >= 0x40) and (reg <= 0x47):
			dt = int(v_[1:3+1],2)
			if (dt > 4):
				dt = -dt
				dt += 4
			REGISTER_STATE[channel]["ops"][1]["dt"] = dt
			REGISTER_STATE[channel]["ops"][1]["ml"] = int(v_[4:7+1],2)
		elif (reg >= 0x48) and (reg <= 0x4F):
			dt = int(v_[1:3+1],2)
			if (dt > 4):
				dt = -dt
				dt += 4
			REGISTER_STATE[channel]["ops"][3]["dt"] = dt
			REGISTER_STATE[channel]["ops"][3]["ml"] = int(v_[4:7+1],2)
		elif (reg >= 0x50) and (reg <= 0x57):
			dt = int(v_[1:3+1],2)
			if (dt > 4):
				dt = -dt
				dt += 4
			REGISTER_STATE[channel]["ops"][2]["dt"] = dt
			REGISTER_STATE[channel]["ops"][2]["ml"] = int(v_[4:7+1],2)
		elif (reg >= 0x58) and (reg <= 0x5F):
			dt = int(v_[1:3+1],2)
			if (dt > 4):
				dt = -dt
				dt += 4
			REGISTER_STATE[channel]["ops"][4]["dt"] = dt
			REGISTER_STATE[channel]["ops"][4]["ml"] = int(v_[4:7+1],2)
		
		# TL (tl)
		elif (reg >= 0x60) and (reg <= 0x67):
			REGISTER_STATE[channel]["ops"][1]["tl"] = int(v_[1:],2)
		elif (reg >= 0x68) and (reg <= 0x6F):
			REGISTER_STATE[channel]["ops"][3]["tl"] = int(v_[1:],2)
		elif (reg >= 0x70) and (reg <= 0x77):
			REGISTER_STATE[channel]["ops"][2]["tl"] = int(v_[1:],2)
		elif (reg >= 0x78) and (reg <= 0x7F):
			REGISTER_STATE[channel]["ops"][4]["tl"] = int(v_[1:],2)
		
		# KS (rs) / AR (a)
		elif (reg >= 0x80) and (reg <= 0x87):
			REGISTER_STATE[channel]["ops"][1]["rs"] = int(v_[0:1+1],2)
			REGISTER_STATE[channel]["ops"][1]["a"] = int(v_[3:7+1],2)
		elif (reg >= 0x88) and (reg <= 0x8F):
			REGISTER_STATE[channel]["ops"][3]["rs"] = int(v_[0:1+1],2)
			REGISTER_STATE[channel]["ops"][3]["a"] = int(v_[3:7+1],2)
		elif (reg >= 0x90) and (reg <= 0x97):
			REGISTER_STATE[channel]["ops"][2]["rs"] = int(v_[0:1+1],2)
			REGISTER_STATE[channel]["ops"][2]["a"] = int(v_[3:7+1],2)
		elif (reg >= 0x98) and (reg <= 0x9F):
			REGISTER_STATE[channel]["ops"][4]["rs"] = int(v_[0:1+1],2)
			REGISTER_STATE[channel]["ops"][4]["a"] = int(v_[3:7+1],2)
		
		# AME (am) / D1R (d)
		elif (reg >= 0xA0) and (reg <= 0xA7):
			REGISTER_STATE[channel]["ops"][1]["am"] = int(v_[0],2)
			REGISTER_STATE[channel]["ops"][1]["d"] = int(v_[3:7+1],2)
		elif (reg >= 0xA8) and (reg <= 0xAF):
			REGISTER_STATE[channel]["ops"][3]["am"] = int(v_[0],2)
			REGISTER_STATE[channel]["ops"][3]["d"] = int(v_[3:7+1],2)
		elif (reg >= 0xB0) and (reg <= 0xB7):
			REGISTER_STATE[channel]["ops"][2]["am"] = int(v_[0],2)
			REGISTER_STATE[channel]["ops"][2]["d"] = int(v_[3:7+1],2)
		elif (reg >= 0xB8) and (reg <= 0xBF):
			REGISTER_STATE[channel]["ops"][4]["am"] = int(v_[0],2)
			REGISTER_STATE[channel]["ops"][4]["d"] = int(v_[3:7+1],2)
		
		# DT2 (dt2) / D2R (d2)
		elif (reg >= 0xC0) and (reg <= 0xC7):
			REGISTER_STATE[channel]["ops"][1]["dt2"] = int(v_[0:1+1],2)
			REGISTER_STATE[channel]["ops"][1]["d2"] = int(v_[3:7+1],2)
		elif (reg >= 0xC8) and (reg <= 0xCF):
			REGISTER_STATE[channel]["ops"][3]["dt2"] = int(v_[0:1+1],2)
			REGISTER_STATE[channel]["ops"][3]["d2"] = int(v_[3:7+1],2)
		elif (reg >= 0xD0) and (reg <= 0xD7):
			REGISTER_STATE[channel]["ops"][2]["dt2"] = int(v_[0:1+1],2)
			REGISTER_STATE[channel]["ops"][2]["d2"] = int(v_[3:7+1],2)
		elif (reg >= 0xD8) and (reg <= 0xDF):
			REGISTER_STATE[channel]["ops"][4]["dt2"] = int(v_[0:1+1],2)
			REGISTER_STATE[channel]["ops"][4]["d2"] = int(v_[3:7+1],2)
		
		# D1L (s) / RR (r?)
		elif (reg >= 0xE0) and (reg <= 0xE7):
			REGISTER_STATE[channel]["ops"][1]["s"] = int(v_[0:3+1],2)
			REGISTER_STATE[channel]["ops"][1]["r"] = int(v_[4:7+1],2)
		elif (reg >= 0xE8) and (reg <= 0xEF):
			REGISTER_STATE[channel]["ops"][3]["s"] = int(v_[0:3+1],2)
			REGISTER_STATE[channel]["ops"][3]["r"] = int(v_[4:7+1],2)
		elif (reg >= 0xF0) and (reg <= 0xF7):
			REGISTER_STATE[channel]["ops"][2]["s"] = int(v_[0:3+1],2)
			REGISTER_STATE[channel]["ops"][2]["r"] = int(v_[4:7+1],2)
		elif (reg >= 0xF8) and (reg <= 0xFF):
			REGISTER_STATE[channel]["ops"][4]["s"] = int(v_[0:3+1],2)
			REGISTER_STATE[channel]["ops"][4]["r"] = int(v_[4:7+1],2)
		return sub.group(0)

	with open(FILE, "rb") as vgm_file:
		# goto offset
		vgm_file.seek(0x34)
		offset = int.from_bytes(vgm_file.read(4), 'little')
		vgm_file.seek(vgm_file.tell() + offset - 4)
		
		# read ym2151 commands
		YM_RE = re.compile(b'\\x54(.)(.)', re.DOTALL)
		YM_RE.sub(print_matches, vgm_file.read())

	# prevent duplicated instrument data
	for state in STATES:
		for channel in state:
			if state[channel] in INSTRUMENTS:
				continue
			elif state[channel]['alg'] is None:
				# skip empty data
				continue
			else:
				INSTRUMENTS.append(state[channel])

	# save instruments
	i = 0
	template = BytesIO(FILE_TEMPLATE)
	for INSTRUMENT in INSTRUMENTS:
		with open("inst_%d.fui" % i, "wb") as instrument_file:
			template.seek(0x39)
			template.write(INSTRUMENT["alg"].to_bytes(1, 'little'))
			template.write(INSTRUMENT["feedback"].to_bytes(1, 'little'))
			template.seek(0x41)
			for op in [1, 3, 2, 4]:
				template.write(INSTRUMENT["ops"][op]["am"].to_bytes(1, 'little'))
				
				template.write(INSTRUMENT["ops"][op]["a"].to_bytes(1, 'little'))
				template.write(INSTRUMENT["ops"][op]["d"].to_bytes(1, 'little'))
				template.write(INSTRUMENT["ops"][op]["ml"].to_bytes(1, 'little'))
				template.write(INSTRUMENT["ops"][op]["r"].to_bytes(1, 'little'))
				template.write(INSTRUMENT["ops"][op]["s"].to_bytes(1, 'little'))
				template.write(INSTRUMENT["ops"][op]["tl"].to_bytes(1, 'little'))
				template.write(INSTRUMENT["ops"][op]["dt2"].to_bytes(1, 'little'))
				template.write(INSTRUMENT["ops"][op]["rs"].to_bytes(1, 'little'))
				
				dt = INSTRUMENT["ops"][op]["dt"]
				dt += 3
				template.write(dt.to_bytes(1, 'little'))
				template.write(INSTRUMENT["ops"][op]["d2"].to_bytes(1, 'little'))
				
				template.read(0x15)
			template.seek(0)
			instrument_file.write(template.read())
			print("exported inst_%d.fui" % i)
		i += 1
