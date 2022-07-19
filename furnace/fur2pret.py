import sys
from copy import deepcopy
from furnacelib import FurnaceModule, FurnaceChip, FurnaceNote
from furnacelib.tools import pattern2seq

bpmify = lambda timebase, speedSum, hz: (120.0 * hz) / (timebase * 4 * speedSum)
to_tempo = lambda tempo: int(19296 / tempo)

song_const_name = None
current_wave_id = 0
current_volume  = 15

def fetch_instrument_nos_in_pattern(pattern):
	"""
	Fetches the set of used instrument IDs.
	"""
	used_instruments = []
	data = pattern.data
	for i in range( len(data) ):
		if data[i]["instrument"] != -1:
			used_instruments.append(data[i]["instrument"])
	return set(used_instruments)

def pattern2asm(pattern, instruments):
	global song_const_name
	global current_wave_id
	global current_volume
	
	note_bin = pattern2seq(pattern)
	safe_note_bin = [] # note_bin, except all values are <= 16
	command_bin = [] # convert from `note_bin`
	
	for i in note_bin:
		if i[1] >= 16:
			# handle notes above the supported length
			# by cloning them
			note_mult, note_remain = divmod(i[1], 16)
			cur_note, cur_len = i
			# add cloned notes
			for j in range(note_mult):
				safe_note_bin.append( (cur_note, 16) )
			# then add the remainder
			if note_remain > 0:
				safe_note_bin.append( (cur_note, note_remain) )
		else:
			safe_note_bin.append(i)
	
	# write the actual commands
	current_instrument_id = None
	current_octave		= None

	for i in safe_note_bin:
		instrument_data_changed = False

		note   = i[0]
		length = i[1]

		# process effects before we write anything else
		if (note["instrument"] != current_instrument_id) and (note["instrument"] != -1):
			current_instrument_id = note["instrument"]
			instrument_data_changed = True

		if (note["volume"] != current_volume) and (note["volume"] != -1):
			current_volume = note["volume"]
			instrument_data_changed = True

		# change waveform ONLY through 10xx
		if pattern.channel == 2:
			has_next_wave = next(filter(lambda x: x[0] == 0x10, note["effects"]), None)
			if has_next_wave is not None:
				next_wave_number = max(has_next_wave[1], 0)
				if next_wave_number != current_wave_id:
					current_wave_id = next_wave_number
					instrument_data_changed = True

		# enable pitch offset
		has_pitch_offset = next(filter(lambda x: x[0] == 0xe5, note["effects"]), None)
		if has_pitch_offset is not None:
			next_pitch_offset = has_pitch_offset[1] - 0x80
			command_bin.append("pitch_offset %d" % next_pitch_offset)

		# change duty cycle ONLY through 12xx
		if pattern.channel <= 1:
			has_duty_cycle = next(filter(lambda x: x[0] == 0x12, note["effects"]), None)

			if has_duty_cycle is not None:
				next_duty_cycle = has_duty_cycle[1] & 0b11
				command_bin.append("duty_cycle %d" % next_duty_cycle)
		
		# apply any stereo effects
		has_stereo_panning = next(filter(lambda x: x[0] == 0x08, note["effects"]), None)
		
		if has_stereo_panning is not None:
			pan_value = hex(has_stereo_panning[1])[2:].zfill(2)
			pan_statements = ["FALSE", "FALSE"]
			# value of 0 will disable channel, otherwise enables it
			# left
			if pan_value[0] != "0":
				pan_statements[0] = "TRUE"
			# right
			if pan_value[1] != "0":
				pan_statements[1] = "TRUE"
			command_bin.append("stereo_panning %s, %s" % tuple(pan_statements))

		# insert instrument commands
		if instrument_data_changed:
			# recalculate note_type
			if pattern.channel == 2:
				# wavetable channel has a special note_type
				if not current_volume:
					calculated_volume = 1
				elif current_volume >= 12:
					calculated_volume = 1
				elif current_volume >= 8:
					calculated_volume = 2
				elif current_volume >= 4:
					calculated_volume = 3

				command_bin.append("note_type 12, %d, %d" % (calculated_volume, current_wave_id))
			elif pattern.channel == 3:
				# TODO: noise channel
				pass
			else:
				# calculate note_type based on the current instrument and vol.
				current_instrument = instruments[current_instrument_id].data["gameboy"]
				if not current_volume:
					current_volume = 0x0f
				calculated_volume = int(
					current_instrument["volume"] \
					* (current_volume / 0x0f)
				)
				calculated_env = (
					current_instrument["direction"] << 3 |
					(current_instrument["length"])
				)
				command_bin.append("note_type 12, %d, %d" % (calculated_volume, calculated_env))

		# insert any octave changes
		if \
		(note["octave"] != 0) and \
		(note["octave"] != current_octave) and \
		pattern.channel != 3:
			current_octave = note["octave"]
			command_bin.append("octave %d" % max(current_octave - 1, 0))

		# insert the actual notes
		if (note["note"] == FurnaceNote.OFF) or (note["note"] == FurnaceNote.__):
			command_bin.append("rest %d" % length)
		else:
			if pattern.channel == 3:
				drum_inst = hex(note["instrument"])[2:].zfill(2)
				command_bin.append("drum_note DRUM_%s_%s, %d" % (song_const_name, drum_inst, length))
			else:
				# XXX: Temporary solution
				note_name = note["note"].__str__().replace("s", "#")
				command_bin.append("note %s, %d" % (note_name, length))

	return command_bin

if __name__ == "__main__":
	if len(sys.argv) == 2:
		FILE = sys.argv[1]
	else:
		print("fur2pret.py [fur file] > [asm file]")
		print()
		print("Converts Furnace .fur modules into .asm files")
		print("suitable for use with the GB/GBC Pokemon disassemblies")
		print()
		print("- Module must ONLY contain a single GB chip")
		exit(0)
	
	module = FurnaceModule(file_name=sys.argv[1])

	if module.chips["list"] != [FurnaceChip.GB]:
		raise Exception("Module must only contain a GB chip")

	song_name = module.meta["name"].title().replace(" ","")
	asm_name  = "%s.asm" % module.meta["name"].lower().replace(" ","_")
	song_const_name = module.meta["name"].upper().replace(" ", "_")

	patterns = {
		0: filter(lambda x: x.channel == 0, module.patterns),
		1: filter(lambda x: x.channel == 1, module.patterns),
		2: filter(lambda x: x.channel == 2, module.patterns),
		3: filter(lambda x: x.channel == 3, module.patterns)
	}

	# g/s/c header
	# assume there's always 4 channels here
	print("Music_%s:\n\tchannel_count 4\n\tchannel 1, Music_%s_Ch1\n\tchannel 2, Music_%s_Ch2\n\tchannel 3, Music_%s_Ch3\n\tchannel 4, Music_%s_Ch4\n" % (
		song_name, song_name, song_name, song_name, song_name
	))
	
	# populate drum list
	drum_patterns = deepcopy(patterns[3]) # so we don't use up our patterns bucket early
	drum_instruments = set()
	drum_channel_pattern = next(drum_patterns, None)
	while drum_channel_pattern:
		drum_instruments = drum_instruments | fetch_instrument_nos_in_pattern(drum_channel_pattern)
		drum_channel_pattern = next(drum_patterns, None)
	
	# insert constants
	print("; Drum constants, replace with the proper values")
	for i in drum_instruments:
		print("DRUM_%s_%s\tEQU\t%d" % (song_const_name, hex(i)[2:].zfill(2), 0))
		
	print("\n; Drumset to use, replace with the proper value")
	print("DRUMSET_%s\tEQU\t%d" % (song_const_name, 0))
	print()

	# go through all the channels
	for ch_order in module.order:
		print("Music_%s_Ch%d:" % (song_name, ch_order+1))

		if ch_order == 0:
			# ch 1
			tempo = to_tempo(bpmify(
				module.timing["timebase"]+1,
				module.timing["speed"][0] + module.timing["speed"][1],
				module.timing["clockSpeed"]
			))
			print("\ttempo %d\n\tvolume 7, 7" % tempo)
		elif ch_order == 3:
			# noise ch
			print("\ttoggle_noise DRUMSET_%s" % (song_const_name))
			print("\tdrum_speed 12")
		
		# prevent rests at start from breaking
		if ch_order != 3:
			print("\tnote_type 12, 15, 0")

		# go through the module order in each channel
		for order_num in module.order[ch_order]:
			print("\tsound_call .pattern%d" % order_num)
		print("\tsound_ret\n")

		cur_patterns = list(patterns[ch_order])
		
		# fetch the relevant pattern
		for order_num in list(set(module.order[ch_order])):
			target_pattern = None
			for patt in cur_patterns:
				if patt.index == order_num:
					target_pattern = patt
			if target_pattern != None:
				print(".pattern%d" % order_num)
				# put each command
				for line in pattern2asm(target_pattern, module.instruments):
					print("\t%s" % line)
				# end the song (loops unsupported yet)
				print("\tsound_ret\n")
