
def pattern2seq(pattern):
	"""
	Converts Furnace pattern data to sequence data in the <note, length> format
	such as used in MIDI and in a lot of retro sound engines.
	
	Does not suport EDxx effects
	"""
	
	data = pattern.data

	note_bin = [] # dump notes here

	note_signature = None
	note = None # `note_signature` corresponding row
	note_length = None

	frame_cut_on = None # which row to cut on

	# preprocess pattern
	for i in range( len(data) ):
		# detect Dxx or Bxx, only supports xx == 00
		frame_cut = \
			(next(filter(lambda x: x[0] == 0xD, data[i]["effects"]), None) is not None) or \
			(next(filter(lambda x: x[0] == 0xB, data[i]["effects"]), None) is not None) or \
			(next(filter(lambda x: x[0] == 0xFF, data[i]["effects"]), None) is not None)
		if frame_cut:
			frame_cut_on = i
			# stop finding here, 0Bxx / 0Dxx / FFxx cuts patterns short
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

	return note_bin
