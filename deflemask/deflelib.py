#!/usr/bin/python

'''
Library for manipulating DefleMask *.dmf files, aimed at
legacy modules made with < 1.0.0.

Only tested with GameBoy modules!!!
'''

import zlib
import io

DMF_STRING  = b'.DelekDefleMask.'

read_byte = lambda x, y: int.from_bytes(x.read(y), 'little')

def determine_system(system_id):
# in  : (int)   system_id
# out : (tuple) (system_string, num_channels)
	if system_id == 0x02:
		return ("Genesis", 10)
	if system_id == 0x42:
		return ("Genesis ext. ch3", 13)
	if system_id == 0x03:
		return ("SMS", 4)
	if system_id == 0x04:
		return ("Game Boy", 4)
	if system_id == 0x05:
		return ("PC Engine", 6)
	if system_id == 0x06:
		return ("NES", 5)
	if system_id == 0x07:
		return ("SID 8580", 3)
	if system_id == 0x47:
		return ("SID 6581", 3)
	if system_id == 0x08:
		return ("YM2151", 13)
	return ("", 0)

def determine_clock_speed(frames_mode, custom_flag):
# in  : (int) frames_mode, (int) custom_flag
# out : (str) clock_mode_string
	if custom_flag == 1:
		return "Custom"
	if frames_mode == 0:
		return "PAL"
	if frames_mode == 1:
		return "NTSC"
	return ""

class DeflemaskModule:
	def __init__(self):
		self.file_name = None
		self.module = {
			"meta":{
				"title": "",
				"author": "",
				"system": "",
				"version": 0,
				"highlight": [0, 0],
				"time": {
					"base": 0,
					"tick": [0, 0]
				},
				"clock_speed": {
					"type": "custom",
					"value": [0, 0, 0],
				}
			},
			"matrix": [
			],
			"instruments": [
			],
			"wavetables": [
			],
			"pattern_rows": 0,
			"pattern": [
			]
		}
	
	def load_from_stream(self, de_dmf):
		dmf_struct = self.module
		
		if de_dmf.read(16) != DMF_STRING:
			raise Exception("Not a DefleMask file!")
		
		# metadata
		version = read_byte(de_dmf, 1)
		dmf_struct["meta"]["version"] = version
		dmf_struct["meta"]["system"], num_channels = determine_system(read_byte(de_dmf, 1))
		
		num_string_bytes = read_byte(de_dmf, 1)
		dmf_struct["meta"]["title"] = de_dmf.read(num_string_bytes).decode("iso-8859-1")
		
		num_string_bytes = read_byte(de_dmf, 1)
		dmf_struct["meta"]["author"] = de_dmf.read(num_string_bytes).decode("iso-8859-1")
		
		dmf_struct["meta"]["highlight"][0] = read_byte(de_dmf, 1)
		dmf_struct["meta"]["highlight"][1] = read_byte(de_dmf, 1)
		
		dmf_struct["meta"]["time"]["base"] = read_byte(de_dmf, 1)
		dmf_struct["meta"]["time"]["tick"][0] = read_byte(de_dmf, 1)
		dmf_struct["meta"]["time"]["tick"][1] = read_byte(de_dmf, 1)
		
		dmf_struct["meta"]["clock_speed"]["type"] = determine_clock_speed(
								read_byte(de_dmf, 1),
								read_byte(de_dmf, 1)
								)
		
		dmf_struct["meta"]["clock_speed"]["value"] = [
								read_byte(de_dmf, 1),
								read_byte(de_dmf, 1),
								read_byte(de_dmf, 1)
							]
		
		# rows per pattern
		if version < 24:
			num_pattern_rows = read_byte(de_dmf, 1)
		else:
			num_pattern_rows = read_byte(de_dmf, 4)
		dmf_struct["pattern_rows"] = num_pattern_rows
		
		num_matrix_rows = read_byte(de_dmf, 1)
		
		# arp tick speed
		if version < 21:
			arp_tick_speed = read_byte(de_dmf, 1)
			dmf_struct["meta"]["arp_tick_speed"] = arp_tick_speed
		
		# matrix
		matrices = []
		for c in range(num_channels):
			matrix_row = []
			for m in range(num_matrix_rows):
				matrix_row.append(read_byte(de_dmf, 1))
			matrices.append(matrix_row)
		dmf_struct["matrix"] = matrices
		
		# instruments
		num_instruments = read_byte(de_dmf, 1)
		instruments = []
		for i in range(num_instruments):
			instrument = {}
			
			num_string_bytes = read_byte(de_dmf, 1)
			#instrument["number"] = i
			instrument["name"] = de_dmf.read(num_string_bytes).decode("iso-8859-1")
			
			mode = read_byte(de_dmf, 1)
			if mode == 1:
				instrument["mode"] = "FM"
				
				for o in range(4): # ym2612 and ym2151 has 4 ops.
					key_name = f"op{o+1}"
					instrument[key_name] = {}
					instrument[key_name]["am"] = read_byte(de_dmf, 1)
					instrument[key_name]["ar"] = read_byte(de_dmf, 1)
					instrument[key_name]["dr"] = read_byte(de_dmf, 1)
					instrument[key_name]["mult"] = read_byte(de_dmf, 1)
					instrument[key_name]["rr"] = read_byte(de_dmf, 1)
					instrument[key_name]["sl"] = read_byte(de_dmf, 1)
					instrument[key_name]["tl"] = read_byte(de_dmf, 1)
					instrument[key_name]["dt2"] = read_byte(de_dmf, 1)
					instrument[key_name]["rs"] = read_byte(de_dmf, 1)
					instrument[key_name]["dt"] = read_byte(de_dmf, 1)
					instrument[key_name]["d2r"] = read_byte(de_dmf, 1)
					instrument[key_name]["ssg"] = read_byte(de_dmf, 1)
					
			else:
				instrument["mode"] = "Standard"
				
				# Volume macro
				if dmf_struct["meta"]["system"] != "Game Boy":
					envelope_size = read_byte(de_dmf, 1)
					volume_envelope = []
					for ve in range(envelope_size):
						volume_envelope.append(read_byte(de_dmf, 4))
					
					instrument["volume"] = volume_envelope
					if envelope_size > 0:
						instrument["volume_loop"] = read_byte(de_dmf, 1)
				
				# Arpeggio macro
				arp_size = read_byte(de_dmf, 1)
				arp_envelope = []
				for ae in range(arp_size):
					arp_envelope.append(read_byte(de_dmf, 4))
				instrument["arpeggio"] = arp_envelope
				if arp_size > 0:
					instrument["arpeggio_loop"] = read_byte(de_dmf, 1)
				arp_mode = read_byte(de_dmf, 1)
				if arp_mode == 1:
					instrument["arpeggio_mode"] = "Fixed"
				else:
					instrument["arpeggio_mode"] = "Normal"
				
				# Duty/noise macro
				duty_size = read_byte(de_dmf, 1)
				duty_envelope = []
				for de in range(duty_size):
					duty_envelope.append(read_byte(de_dmf, 4))
				instrument["duty"] = duty_envelope
				if duty_size > 0:
					instrument["duty_loop"] = read_byte(de_dmf, 1)
				
				# Wavetable macro
				wave_size = read_byte(de_dmf, 1)
				wave_envelope = []
				for we in range(wave_size):
					wave_envelope.append(read_byte(de_dmf, 4))
				instrument["wave"] = wave_envelope
				if wave_size > 0:
					instrument["wave_loop"] = read_byte(de_dmf, 1)
				
				# C64 system data
				if dmf_struct["meta"]["system"].startswith("SID"):
					instrument_c64 = {}
					
					instrument_c64["tri"] = read_byte(de_dmf, 1)
					instrument_c64["saw"] = read_byte(de_dmf, 1)
					instrument_c64["pulse"] = read_byte(de_dmf, 1)
					instrument_c64["noise"] = read_byte(de_dmf, 1)
					
					instrument_c64["attack"] = read_byte(de_dmf, 1)
					instrument_c64["decay"] = read_byte(de_dmf, 1)
					instrument_c64["sustain"] = read_byte(de_dmf, 1)
					instrument_c64["release"] = read_byte(de_dmf, 1)
					
					instrument_c64["pulse_width"] = read_byte(de_dmf, 1)
					
					instrument_c64["ring_mod"] = read_byte(de_dmf, 1)
					instrument_c64["sync_mod"] = read_byte(de_dmf, 1)
					
					instrument_c64["to_filter"] = read_byte(de_dmf, 1)
					instrument_c64["volume_to_cutoff"] = read_byte(de_dmf, 1)
					instrument_c64["filter_from_instrument"] = read_byte(de_dmf, 1)
					
					instrument_c64["global_resonance"] = read_byte(de_dmf, 1)
					instrument_c64["global_cutoff"] = read_byte(de_dmf, 1)
					instrument_c64["global_hipass"] = read_byte(de_dmf, 1)
					instrument_c64["global_lopass"] = read_byte(de_dmf, 1)
					instrument_c64["global_ch2_off"] = read_byte(de_dmf, 1)
					
					instrument["c64"] = instrument_c64
				elif dmf_struct["meta"]["system"] == "Game Boy":
					instrument_dmg = {}
					instrument_dmg["env_volume"] = read_byte(de_dmf, 1)
					instrument_dmg["env_direction"] = read_byte(de_dmf, 1)
					instrument_dmg["env_length"] = read_byte(de_dmf, 1)
					instrument_dmg["sound_length"] = read_byte(de_dmf, 1)
					instrument["dmg"] = instrument_dmg
			instruments.append(instrument)
		dmf_struct["instruments"] = instruments
		
		# wavetable
		num_wavetables = read_byte(de_dmf, 1)
		
		wavetables = []
		for w in range(num_wavetables):
			wave_size = read_byte(de_dmf, 4)
			wavetable = []
			for ws in range(wave_size):
				wavetable.append(read_byte(de_dmf, 4))
			wavetables.append(wavetable)
		
		dmf_struct["wavetables"] = wavetables
		
		# pattern
		patterns = []
			
		for ch in range(num_channels):
			channel_struct = {
				"channel": ch,
				"patterns": []
			}
			channel_effects_columns = read_byte(de_dmf, 1)
			for mr in range(num_matrix_rows):
				pattern_struct = {
					"number": mr,
					"rows": []
				}
				for pr in range(num_pattern_rows):
					row_struct = {
					}
					note = read_byte(de_dmf, 2)
					octave = read_byte(de_dmf, 2)
					
					if (note == 100):
						row_struct["type"] = "rest"
					elif (note == 0) and (octave == 0):
						row_struct["type"] = "gap"
					else:
						row_struct["type"] = "note"
						row_struct["note"] = note
						row_struct["octave"] = octave
					
					volume = read_byte(de_dmf, 2)
					
					if volume != 65535:
						row_struct["volume"] = volume
					
					effects = []
					for cc in range(channel_effects_columns):
						e_code = (read_byte(de_dmf, 2))
						e_val  = (read_byte(de_dmf, 2))
						
						if (e_code != 65535) and (e_val != 65535):
							effects.append([e_code, e_val])
					
					if len(effects) > 0:
						row_struct["effects"] = effects
					
					instrument = read_byte(de_dmf, 2)
					if instrument != 65535:
						row_struct["instrument"] = instrument
					
					pattern_struct["rows"].append(row_struct)
						
				channel_struct["patterns"].append(pattern_struct)
			
			patterns.append(channel_struct)
		
		dmf_struct["pattern"] = patterns
		
		self.module = dmf_struct
	
	def load_from_bytes(self, bytes):
		de_dmf = io.BytesIO(bytes)
		return self.load_from_stream(de_dmf)
	
	def load_from_file(self, file_name):
		self.file_name = file_name
		with open(file_name, "rb") as dmf_in:
			return self.load_from_bytes(zlib.decompress(dmf_in.read()))
	
	def decompress_to_file(self, in_file, out_file):
		with open(in_file, "rb") as dmf_in:
			with open(out_file, "wb") as dmf_out:
				dmf_out.write(zlib.decompress(dmf_in.read()))
	
	# shortcuts
	def get_module_version(self): return self.module["meta"]["version"]
	def get_module_title(self):   return self.module["meta"]["title"]
	def get_module_system(self):  return self.module["meta"]["system"]
	def get_module_time_base(self):  return self.module["meta"]["time"]["base"]
	def get_module_time_ticks(self):
		return (
			self.module["meta"]["time"]["tick"][0],
			self.module["meta"]["time"]["tick"][1]
			)
	def get_module_clock_type(self):  return self.module["meta"]["clock_speed"]["type"]
	
	def get_module_matrix(self):  return self.module["matrix"]
	def get_module_instruments(self):  return self.module["instruments"]
	def get_module_wavetables(self):  return self.module["wavetables"]
	def get_module_rows_per_pattern(self):  return self.module["pattern_rows"]
	def get_module_patterns(self):  return self.module["pattern"]
