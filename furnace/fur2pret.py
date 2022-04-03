import sys
from furnacelib import FurnaceModule, FurnaceChip, FurnaceNote

bpmify = lambda timebase, speedSum, hz: (120.0 * hz) / (timebase * 4 * speedSum)
to_tempo = lambda tempo: int(19296 / tempo)

def pattern2asm(pattern, instruments):
	data = pattern["data"]

	dummy_row = {
		"note": FurnaceNote.__, "octave": 0, "instrument": -1,
		"volume": -1, "effects": [(-1,-1) for x in data[0]["effects"]]
	}

	note_bin = [] # dump notes here
	command_bin = [] # convert from `note_bin`

	note_signature = None
	note = None # `note_signature` corresponding row
	note_length = None

	frame_cut_on = None # which row to cut on

	# preprocess pattern
	for i in range( len(data) ):
		# detect Dxx or Bxx, only supports xx == 00
		frame_cut = \
			(next(filter(lambda x: x[0] == 0xD, data[i]["effects"]), None) is not None) or \
			(next(filter(lambda x: x[0] == 0xB, data[i]["effects"]), None) is not None)
		if frame_cut:
			frame_cut_on = i
			# stop finding here, Bxx and Dxx cuts patterns short
			break

	# cut pattern if we have a match
	if frame_cut_on:
		data = data[:frame_cut_on+1]

	# convert rows to note and length
	for i in range( len(data) ):
		# grab row
		new_note_signature = "%s%d" % (data[i]["note"], data[i]["octave"])
		# note signature = string(note) + string(octave)
		new_note = data[i]
		if i == 0: # first row
			note_signature = new_note_signature
			note = new_note
			note_length = 1
		else:
			if (i == len(data)-1):
				if (new_note_signature == "__0"):
					note_length += 1
				else:
					note_bin.append( (note, note_length) ) # previous note
					note_signature = new_note_signature
					note = new_note
				note_bin.append( (note, note_length) )
			else:
				if (new_note_signature == "__0"):
					# blank row
					note_length += 1
				else:
					note_bin.append( (note, note_length) )
					note_signature = new_note_signature
					note = new_note
					note_length = 1

	# write the actual commands
	current_instrument_id = None
	current_volume		= None
	current_wave_id	   = 0
	current_octave		= None

	for i in note_bin:
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
		if pattern["channel"] == 2:
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
		if pattern["channel"] <= 1:
			has_duty_cycle = next(filter(lambda x: x[0] == 0x12, note["effects"]), None)

			if has_duty_cycle is not None:
				next_duty_cycle = has_duty_cycle[1] & 0b11
				command_bin.append("duty_cycle %d" % next_duty_cycle)

		# insert instrument commands
		if instrument_data_changed:
			# recalculate note_type
			if pattern["channel"] == 2:
				# wavetable channel has a special note_type
				if current_volume >= 12:
					calculated_volume = 1
				elif current_volume >= 8:
					calculated_volume = 2
				elif current_volume >= 4:
					calculated_volume = 3

				command_bin.append("note_type 12, %d, %d" % (calculated_volume, current_wave_id))
			elif pattern["channel"] == 3:
				# TODO: noise channel
				pass
			else:
				# calculate note_type based on the current instrument and vol.
				current_instrument = instruments[current_instrument_id].data["gameboy"]
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
		if (note["octave"] != 0) and (note["octave"] != current_octave):
			current_octave = note["octave"]
			command_bin.append("octave %d" % max(current_octave - 1, 0))

		# insert the actual notes
		if (note["note"] == FurnaceNote.OFF) or (note["note"] == FurnaceNote.__):
			command_bin.append("rest %d" % length)
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

	patterns = {
		0: filter(lambda x: x["channel"] == 0, module.patterns),
		1: filter(lambda x: x["channel"] == 1, module.patterns),
		2: filter(lambda x: x["channel"] == 2, module.patterns),
		3: filter(lambda x: x["channel"] == 3, module.patterns)
	}

	# g/s/c header
	# assume there's always 4 channels here
	print("Music_%s:\n\tchannel_count 4\n\tchannel 1, Music_%s_Ch1\n\tchannel 2, Music_%s_Ch2\n\tchannel 3, Music_%s_Ch3\n\tchannel 4, Music_%s_Ch4\n" % (
		song_name, song_name, song_name, song_name, song_name
	))

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

		# go through the module order in each channel
		for order_num in module.order[ch_order]:
			print("\tsound_call .pattern%d" % order_num)
		print("\tsound_ret\n")

		# fetch the relevant pattern
		for order_num in module.order[ch_order]:
			target_pattern = next(filter(lambda x: x["index"] == order_num, patterns[ch_order]), None)
			if target_pattern != None:
				print(".pattern%d" % order_num)
				# put each command
				for line in pattern2asm(target_pattern, module.instruments):
					print("\t%s" % line)
				# end the song (loops unsupported yet)
				print("\tsound_ret\n")
