#!/usr/bin/python

'''
Utility to convert DMF modules to Pokemon disassembly format music.
'''

import sys
from deflelib import DeflemaskModule
import re
import pprint

dmf = DeflemaskModule()
dmf.load_from_file(sys.argv[1])

RE_TITLE = re.compile(r'\w+')
TITLE = dmf.get_module_title()

CONST_NAME = '_'.join(re.findall(RE_TITLE, TITLE)).upper()
LABEL_NAME = ''.join(re.findall(RE_TITLE, TITLE))

CHANNELS = 4

CALL_CHANNEL_COMMAND = "sound_call {}"
NOTE_REST_COMMAND = "{} {}"
NOTE_TYPE_COMMAND = "note_type 12, {}, {}"
DUTY_COMMAND = "duty_cycle {}"
DSPEED_COMMAND = "drum_speed 12"
DRUM_COMMAND = f"drum_note {CONST_NAME}_DRUM_{{}}, {{}}"
SOUND_RET_COMMAND = f"sound_ret"

REST_NOTE = (999, 12)
GAP_NOTE = (777, 777)

def to_note(index):
	note_strings = ["C_", "C#", "D_", "D#", "E_", "F_", "F#",
			"G_", "G#", "A_", "A#", "B_" ]
	
	if index < 12:
		return f"note {note_strings[index]},"
	else:
		return f"rest"

def to_drum(note, inst, length):
	if note < 12:
		return DRUM_COMMAND.format(inst, length)
	else:
		return "rest {}".format(length)

if dmf.get_module_system() != "Game Boy":
	print("Not a Gameboy module")
	exit(1)

pp = pprint.PrettyPrinter(indent=4, sort_dicts=False)

lines = {}

def inst_to_squaretype(index):
	inst = dmf.get_module_instruments()[index]
	dmg = inst["dmg"]
	if dmg['env_length'] != 0:
		if dmg['env_direction'] == 1:
			release = 15 - dmg['env_length']
		else:
			release = dmg['env_length']
	else:
		release = 0
	return NOTE_TYPE_COMMAND.format(dmg['env_volume'], release)

for c in range(CHANNELS):
	if c == 0: key = "Ch1"
	if c == 1: key = "Ch2"
	if c == 2: key = "Ch3"
	if c == 3: key = "Ch4"
	
	lines[key] = {}
	
	# deflemask stores every pattern as its own thing so I don't think we
	# even need this
	
	#matrix = []
	#for s in dmf.get_module_matrix()[c]:
	#	matrix.append(CALL_CHANNEL_COMMAND.format(f".patt{s}"))
	#lines[key]["matrix"] = matrix
	
	if c == 3: lines[key]["used_drums"] = []
	
	pattern = []
	channel_pat_obj = dmf.get_module_patterns()[c]['patterns']
	for p in channel_pat_obj:
		pattern.append(f";;;;;;;;;; PATTERN {p['number']} ;;;;;;;;;;;;;;")
		
		# get first row
		r = p['rows'][0]
		
		old_octave = 999
		
		if r['type'] == 'note':
			cur_octave, cur_note = (r['octave'], r['note'])
			if c != 3:
				pattern.append(f"octave {cur_octave-1}")
		else:
			cur_rest, cur_note = REST_NOTE
		
		if 'instrument' in r:
			cur_inst = r['instrument']
			if c == 3:
				if cur_inst not in lines[key]["used_drums"]:
					lines[key]["used_drums"].append(cur_inst)
		else:
			cur_inst = 0
		
		if 'effects' in r:
				for f in r['effects']:
					if f[0] == 18:	# duty cycle
						pattern.append(DUTY_COMMAND.format(f[1]))
		
		if c == 3:
			pattern.append(DSPEED_COMMAND)
		
		row_num = 0
		gap_count = 1
		
		# get the rest of the rows
		for r in p['rows'][1:]:
			row_num += 1
			
			if 'instrument' in r:
				old_inst = cur_inst
				cur_inst = r['instrument']
				if old_inst != cur_inst:
					if c != 3:
						pattern.append(inst_to_squaretype(old_inst))
					else:
						if cur_inst not in lines[key]["used_drums"]:
							lines[key]["used_drums"].append(cur_inst)
						
			
			if 'effects' in r:
				for f in r['effects']:
					if f[0] == 18:	# duty cycle
						pattern.append(DUTY_COMMAND.format(f[1]))\
			
			if r['type'] == 'gap':
				gap_count += 1
			
			if r['type'] == 'note':
				old_octave = cur_octave
				old_note = cur_note
				cur_octave, cur_note = (r['octave'], r['note'])
				
				# data insertion here
				if gap_count > 16:
					if c != 3:
						pattern.append(";-- " + NOTE_REST_COMMAND.format(to_note(old_note), gap_count) + " --;")
						tmp_counter = gap_count
						while tmp_counter - 16 > 0:
							pattern.append(NOTE_REST_COMMAND.format(to_note(old_note), 16))
							tmp_counter = tmp_counter - 16
						pattern.append(NOTE_REST_COMMAND.format(to_note(old_note), tmp_counter))
						pattern.append(";-- --;")
					else:
						pattern.append(";c xx;")
				else:
					if c != 3:
						pattern.append(NOTE_REST_COMMAND.format(to_note(old_note), gap_count))
					else:
						pattern.append(to_drum(old_note, old_inst, gap_count))
				
				if cur_octave != old_octave:
					if c != 3:
						pattern.append(f"octave {cur_octave-1}")
				
				gap_count = 1
			
			if r['type'] == 'rest':
				old_octave = cur_octave
				old_note = cur_note
				cur_rest, cur_note = REST_NOTE
				
				# data insertion here
				if gap_count > 16:
					if c != 3:
						pattern.append(";-- " + NOTE_REST_COMMAND.format(to_note(old_note), gap_count) + " --;")
						tmp_counter = gap_count
						while tmp_counter - 16 > 0:
							pattern.append(NOTE_REST_COMMAND.format(to_note(old_note), 16))
							tmp_counter = tmp_counter - 16
						pattern.append(NOTE_REST_COMMAND.format(to_note(old_note), tmp_counter))
						pattern.append(";-- --;")
					else:
						pattern.append(";c xx;")
				else:
					if c != 3:
						pattern.append(NOTE_REST_COMMAND.format(to_note(old_note), gap_count))
					else:
						pattern.append(to_drum(old_note, old_inst, gap_count))
				
				gap_count = 1
			
			# last row
			if row_num == dmf.get_module_rows_per_pattern() - 1:
				if gap_count > 16:
					if c != 3:
						pattern.append(";-- " + NOTE_REST_COMMAND.format(to_note(cur_note), gap_count) + " --;")
						tmp_counter = gap_count
						while tmp_counter - 16 > 0:
							pattern.append(NOTE_REST_COMMAND.format(to_note(cur_note), 16))
							tmp_counter = tmp_counter - 16
						pattern.append(NOTE_REST_COMMAND.format(to_note(cur_note), tmp_counter))
						pattern.append(";-- --;")
					else:
						pattern.append(";c xx;")
				else:
					if c != 3:
						pattern.append(NOTE_REST_COMMAND.format(to_note(cur_note), gap_count))
					else:
						pattern.append(to_drum(cur_note, cur_inst, gap_count))
		
		lines[key]["sequence"] = pattern
			
# consts
for drum in lines["Ch4"]["used_drums"]:
	print(f'{CONST_NAME}_DRUM_{drum}\tEQU\t{drum}')

# data
print()
for ch in lines.keys():
	print(f'Music_{LABEL_NAME}_{ch}::')
	for cmd in lines[ch]["sequence"]:
		print(f'\t{cmd}')
	print(f'\t{SOUND_RET_COMMAND}')

#pp.pprint(dmf.get_module_patterns()[2])
