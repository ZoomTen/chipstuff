#!/usr/bin/python

'''
Library for manipulating FamiTracker *.ftm files, aimed at
modules created with current stable 0.4.6.
'''

import io, os

FTM_MAGIC  = b'FamiTracker Module'

read_bytes = lambda x, y: int.from_bytes(x.read(y), 'little')
read_big = lambda x, y: int.from_bytes(x.read(y), 'big')

class FamitrackerPattern:
	def __init__(self):
		self.channel = 0
		self.index = 0
		self.content = []
	
	def add_row(self, stream):
		row_struct = {
			"position": 0,
			"note": None,
			"octave": None,
			"instrument": None,
			"volume": None,
			"effects": []
		}
		
		row_struct["position"] = read_bytes(stream, 4)
		
		note2rep = [None, "C_", "C#", "D_", "D#", "E_", "F_", "F#",
		            "G_", "G#", "A_", "A#", "B_", "==", "--"]
		note_val = read_bytes(stream, 1)
		try:
			row_struct["note"] = note2rep[note_val]
		except:
			row_struct["note"] = note_val
		
		oct_val = read_bytes(stream, 1)
		if 0 < note_val < 0xd:
			row_struct["octave"] = oct_val
		
		ins_val = read_bytes(stream, 1)
		if ins_val < 0x40:
			row_struct["instrument"] = ins_val
		
		vol_val = read_bytes(stream, 1)
		if vol_val < 0x10:
			row_struct["volume"] = vol_val
		
		while True:
			eff_type = stream.read(1)
			if eff_type == b'':
				break
			eff_type = int.from_bytes(eff_type, 'little')
			eff_val = read_bytes(stream, 1)
			row_struct["effects"].append((eff_type, eff_val))
		
		# remove blank effects
		new_eff = []
		for effect in row_struct["effects"]:
			if effect != (0, 0):
				new_eff.append(effect)
		row_struct["effects"] = new_eff
		
		self.content.append(row_struct)
		
	
	def add_row_from_bytes(self, bytes):
		block_bytes = io.BytesIO(bytes)
		return self.add_row(block_bytes)
	
	def __repr__(self):
		return f'<FamiTracker pattern, channel {self.channel} index {hex(self.index)}>'

# -- handle module block --

class FamitrackerModuleBlock:
	def __init__(self):
		self.data = None
		self.name = b''
		self.version = 0
	
	def load_from_stream(self, stream):
		self.name = stream.read(16).decode('ascii').strip('\x00')
		self.version = read_bytes(stream, 4)
		size = read_bytes(stream, 4)
		self.data = io.BytesIO(stream.read(size))
		return self
	
	def load_from_bytes(self, bytes):
		block_bytes = io.BytesIO(bytes)
		return self.load_from_stream(block_bytes)
	
	def __repr__(self):
		return f'<FamiTracker block "{self.name}", version {self.version}>'

# -- handle module file --

class FamitrackerModule:
	def __init__(self):
		self.file_name = None
		self.module = {
			"meta":{
				"author": '',
				"copyright": '',
				"title": '',
				"version": 'N/A'
			},
			"songs": [],
			"sequences": [
			],
			"instruments": [
			],
		}
	
	def load_from_stream(self, ftm):
		struct = self.module
		
		# check for magic number
		if ftm.read(len(FTM_MAGIC)) != FTM_MAGIC:
			raise Exception("Not a valid FamiTracker module!")
		
		# check for EOF
		ftm.seek(-3, os.SEEK_END)
		if ftm.read() != b'END':
			raise Exception("Not a valid FamiTracker module!")
		
		ftm.seek(len(FTM_MAGIC))
		
		# determine version
		ver_identifier = read_bytes(ftm, 2)
		if ver_identifier == 0x200:
			struct['meta']['version'] = '0.2.2'
		elif ver_identifier == 0x201:
			struct['meta']['version'] = '0.2.4'
		elif ver_identifier == 0x203:
			struct['meta']['version'] = '0.2.5 - 0.2.6'
		elif ver_identifier == 0x300:
			struct['meta']['version'] = '0.2.7 - 0.3.0.0'
		elif ver_identifier == 0x410:
			struct['meta']['version'] = '0.3.0.1'
		elif ver_identifier == 0x420:
			struct['meta']['version'] = '0.3.5 - 0.3.8'
		elif ver_identifier == 0x430:
			struct['meta']['version'] = '0.4.0 - 0.4.1'
		elif ver_identifier == 0x440:
			struct['meta']['version'] = '0.4.2 - 0.4.6'
		else:
			struct['meta']['version'] = 'N/A'
		
		# skip zeroes
		ftm.read(2)
		
		# add blocks
		blocks = {}
		while True:
			block = FamitrackerModuleBlock().load_from_stream(ftm)
			# stop loading blocks when reached EOF or invalid block
			if (block.name == 'END') or (block.name == ''):
				break
			blocks[block.name] = block
		
		# parse blocks
		for block_name, block in blocks.items():
			if block_name == 'PARAMS':
				# TODO
				pass
			
			elif block_name == 'INFO':
				struct['meta']['title'] = block.data.read(32).decode('ascii').strip('\x00')
				struct['meta']['author'] = block.data.read(32).decode('ascii').strip('\x00')
				struct['meta']['copyright'] = block.data.read(32).decode('ascii').strip('\x00')
			
			elif block_name == 'HEADER':
				num_songs = read_bytes(block.data, 1) + 1
				
				# add songs
				for i in range(num_songs):
					song_name = b''
					while True:
						str_byte = block.data.read(1)
						if str_byte == b'\x00':
							break
						song_name += str_byte
					
					song = {
						"name": song_name.decode('ascii'),
						"speed": 6,
						"tempo": 150,
						"rows": 64,
						"fx_columns": [0, 0, 0, 0, 0], # XXX: assumed 2a03!
						"patterns": [],
						"frames": []
					}
					struct['songs'].append(song)
				
				# XXX: assumed 2a03!
				for i in range(5):
					ch_id = read_bytes(block.data, 1)
					for j in range(num_songs):
						num_columns = read_bytes(block.data, 1)
						struct['songs'][j]['fx_columns'][i] = num_columns
				pass
			
			elif block_name == 'INSTRUMENTS':
				# TODO
				pass
			
			elif block_name == 'SEQUENCES':
				# TODO
				pass
			
			elif block_name == 'FRAMES':
				for i in range(len(struct['songs'])):
					song = struct['songs'][i]
					num_frames = read_bytes(block.data, 4)
					song['speed'] = read_bytes(block.data, 4)
					song['tempo'] = read_bytes(block.data, 4)
					song['rows'] = read_bytes(block.data, 4)
					
					# XXX: assumed 2a03!
					song['frames'] = []
					frame = []
					for frame_ in range(num_frames):
						for channel in range(5):
							frame.append(read_bytes(block.data, 1))
						song['frames'].append(frame)
						frame = []
				pass
			
			elif block_name == 'PATTERNS':
				while True:
					song_num = block.data.read(4)
					if song_num == b'':
						break
					
					song_num = int.from_bytes(song_num, 'little')
					pattern_struct = struct['songs'][song_num]['patterns']
					
					pattern = FamitrackerPattern()
					pattern.channel = read_bytes(block.data, 4)
					pattern.index = read_bytes(block.data, 4)
					
					num_rows = read_bytes(block.data, 4)
					num_eff_col = struct['songs'][song_num]["fx_columns"][pattern.channel] + 1
					for row in range(num_rows):
						pattern.add_row_from_bytes(block.data.read(8 + (2*num_eff_col)))
					pattern_struct.append(pattern)
				pass
			
			elif block_name == 'DPCM SAMPLES':
				# TODO
				pass
			
			elif block_name == 'COMMENTS':
				struct['meta']['comments'] = {
					"enabled": read_bytes(block.data, 4),
					"content": ""
				}
				comment = ''
				while True:
					char = block.data.read(1)
					if char == '\x00':
						break
					comment += char.decode('ascii')
				struct['meta']['comments']['content'] = comment
				pass
	
	def load_from_bytes(self, bytes):
		ftm_bytes = io.BytesIO(bytes)
		return self.load_from_stream(ftm_bytes)
	
	def load_from_file(self, file_name):
		self.file_name = file_name
		with open(file_name, "rb") as ftm_in:
			return self.load_from_bytes(ftm_in.read())
	
	# shortcuts
	def get_version(self): return self.module["meta"]["version"] or 'N/A'
	def get_title(self):   return self.module["meta"]["title"] or ''
	def get_author(self):   return self.module["meta"]["author"] or ''
	def get_copyright(self):   return self.module["meta"]["copyright"] or ''
	def get_songs(self):   return self.module["songs"]
	def get_sequences(self):   return self.module["sequences"]
	def get_instruments(self):   return self.module["instruments"]
	
	# representation
	def __repr__(self):
		return f'<FamiTracker version {self.get_version()} module, {len(self.get_songs())} songs>'
