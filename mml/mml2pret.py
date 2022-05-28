# This script requires Python 3.10+
# TODO: Fix looping
# TODO: Fix noise
import re
import sys
import datetime

COMMANDS_RE = re.compile(
    # local looping
        r"\[(.+?)\](\d+)|" +
    
    # tempo and octave
        r"[to](\d+)|" +
        
    # duty, envelope, vibrato, tone, drum set
        r"@(duty|env|vib|tone|drum|vol)\((.+?)\)|"+
        
    # loop point
        r"@l|"+
        
    # raise or lower octave
        r"[<>]|"+
        
    # note data
        r"[cdefgabr][\+-]?(\d+\.?)?|"+
        
    # set note tie
        r"&|"+
        
    # set length
        r"l\d+\.?",
        
    re.DOTALL | re.IGNORECASE | re.MULTILINE
)

LENGTH_TABLE = { # ! means this is accurate

     1: (12, 16), # 1/1 !
     2: (12,  8), # 1/2 !
     3: ( 8,  8), # 1/3 !
     4: (12,  4), # 1/4 !
     5: (12,  3), # 1/5
     6: ( 8,  4), # 1/6 !
     7: ( 3,  9), # 1/7
     8: (12,  2), # 1/8 !
     9: ( 3,  7), # 1/9
    10: ( 6,  3), # 1/10
    11: ( 8,  2), # 1/11
    12: ( 8,  2), # 1/12 !
    13: ( 1, 14), # 1/13
    14: ( 1, 13), # 1/14
    15: (12,  1), # 1/15
    16: (12,  1), # 1/16 !
#    17:
#    18:
#    19:
    20: ( 1,  9), # 1/20
#    21:
#    22:
#    23:
    24: ( 8,  1), # 1/24 !
#    25:
#    26:
#    27:
#    28:
#    29:
#    30:
    31: ( 6,  1), # 1/31
    32: ( 6,  1), # 1/32 !
}

num_loop_points = 0

def mml2commands(text, subroutine=False, is_drums=False):
    state={"length": "4", "octave": 4}
    command_bin = []
    
    def add_tempo(tempo):
        command_bin.append(
            (("T"), (int(tempo))) # tempo
        )
    
    def add_envelope(envelope_string):
        command_bin.append(
            (("E"), tuple([int(x) for x in envelope_string.split(" ")])) # envelope
        )
    
    def add_volume(vol_string):
        command_bin.append(
            (("VO"), tuple([int(x) for x in vol_string.split(" ")])) # volume
        )
    
    def add_vibrato(vibrato_string):
        command_bin.append(
            (("V"), tuple([int(x) for x in vibrato_string.split(" ")])) # vibrato
        )
    
    def add_tone(tone):
        command_bin.append(
            (("PS"), (int(tone))) # pitch_offset
        )
    
    def add_drum_set(dset):
        command_bin.append(
            (("DS"), (int(dset))) # toggle_noise
        )
    
    def add_duty(duty):
        command_bin.append(
            (("D"), (int(duty))) # duty
        )
    
    def add_octave(octave):
        command_bin.append(
            (("O"), (octave)) # octave
        )
    
    def add_raw_note(note, length_tuple):
        command_bin.append(
            (("N"), (note, length_tuple)) # note
        )
    
    def add_note(note, length_string):
        if length_string[-1] == ".":
            now_length = LENGTH_TABLE[ int(length_string[:-1]) ]
            next_length = LENGTH_TABLE[ int(length_string[:-1])*2 ]
            
            if now_length[0] == next_length[0]: # same note length
                rendered_length = now_length[1] + next_length[1]
                if rendered_length > 16:
                    _ = divmod(rendered_length, 16)
                    for i in range(_[0]):
                        add_raw_note(note, (now_length[0], 16))
                    add_raw_note(note, (now_length[0], _[1]))
                else:
                    add_raw_note(note, (now_length[0], rendered_length))
            else: # different
                # i'm not gonna bother with maths for now
                add_raw_note(note, now_length)
                add_raw_note(note, next_length)
        else:
            add_raw_note(note, LENGTH_TABLE[ int(length_string) ])
    
    def add_comment(text):
        command_bin.append(
            ((";"), (text)) # comment
        )
    
    def add_label(label):
        command_bin.append(
            ((":"), (label)) # label
        )
    
    def add_loop_label():
        global num_loop_points
        add_label(".loop%d" % num_loop_points)
        num_loop_points += 1
    
    def add_loop_command(num_loops, which_loop):
        command_bin.append(
            (("L"), (num_loops, ".loop%d" % which_loop)) # loop
        )
    
    def add_jump_command(which_jump):
        command_bin.append(
            (("J"), (which_jump)) # jump
        )
    
    def add_asm(asm):
        command_bin.append(
            (("A"), (asm)) # asm
        )
    
    jump_point = None
    
    commands = COMMANDS_RE.finditer(text)
    
    if not subroutine:
        if not is_drums:
            # initialize track
            add_octave(state["octave"])
            add_asm("note_type %d, 12, 0" % LENGTH_TABLE[ int(state["length"]) ][0] )
    
    for entry in commands:
        mml_command = entry.group().lower()
        first_chara = mml_command[0]
        
        # add_comment(mml_command)
        
        match first_chara:
            case "[":
                add_loop_label()
                for inner_command in mml2commands(entry.group(1), subroutine=True, is_drums=is_drums):
                    command_bin.append(inner_command)
                add_loop_command(
                    int(entry.group(2)), num_loop_points-1
                )
            case "@":
                if entry.group(4) is None:
                    if entry.group()[1] == "l":
                        jump_point = ".main_loop"
                        add_label(jump_point)
                else:
                    match entry.group(4):
                        case "duty":
                            add_duty(entry.group(5))
                        case "env":
                            add_envelope(entry.group(5))
                        case "vib":
                            add_vibrato(entry.group(5))
                        case "tone":
                            add_tone(entry.group(5))
                        case "drum":
                            add_drum_set(entry.group(5))
                        case "vol":
                            add_volume(entry.group(5))
            case "c"|"d"|"e"|"f"|"g"|"a"|"b"|"r":
                delta_octave = 0
                cur_note = first_chara.upper() + "_"
                
                if first_chara == "r":
                    cur_note = "__"
                else:
                    if len(mml_command) > 1:
                        match mml_command[1]:
                            case "+":
                                match first_chara:
                                    case "c"|"d"|"f"|"g"|"a":
                                        cur_note = cur_note[0] + "#"
                                    case "e":
                                        cur_note = "F_"
                                    case "b":
                                        delta_octave = 1
                                        cur_note = "C_"
                            case "-":
                                match first_chara:
                                    case "c":
                                        delta_octave = -1
                                        cur_note = "C_"
                                    case "d":
                                        cur_note = "C#"
                                    case "e":
                                        cur_note = "D#"
                                    case "f":
                                        cur_note = "E_"
                                    case "g":
                                        cur_note = "F#"
                                    case "a":
                                        cur_note = "G#"
                                    case "b":
                                        cur_note = "A#"
                
                if delta_octave:
                    if not is_drums:
                        state["octave"] += delta_octave
                        add_octave(state["octave"])
                
                if entry.group(6) is not None:
                    add_note(cur_note, entry.group(6))
                else:
                    add_note(cur_note, state["length"])
                
                if delta_octave:
                    if not is_drums:
                        state["octave"] -= delta_octave
                        add_octave(state["octave"])
            case "t":
                add_tempo(19200/int(entry.group(3)))
            case ">":
                if not is_drums:
                    state["octave"] += 1
                    add_octave(state["octave"])
            case "<":
                if not is_drums:
                    state["octave"] -= 1
                    add_octave(state["octave"])
            case "o":
                if not is_drums:
                    state["octave"] = int(entry.group(3))
                    add_octave(state["octave"])
            case "l":
                state["length"] = entry.group()[1:]
            case "&":
               add_comment("tied with previous note")
            case _:
                add_comment(mml_command)
                pass
    
    if jump_point:
        add_jump_command(jump_point)
    
    return command_bin

def commands2asm(commands):
    current_note_type = 12
    asm_bin = []
    envelope_type = (12, 0)
    envelope_changed = False
    
    for command in commands:
        match command[0]:
            case "T":
                asm_bin.append("\ttempo %d" % command[1])
            case "O":
                asm_bin.append("\toctave %d" % command[1])
            case "N":
                if command[1][1][0] != current_note_type:
                    current_note_type = command[1][1][0]
                    asm_bin.append("\tnote_type %d, %d, %d" % (current_note_type, *envelope_type))
                
                if envelope_changed:
                    asm_bin.append("\tnote_type %d, %d, %d" % (current_note_type, *envelope_type))
                    envelope_changed = False
                
                if command[1][0] == "__":
                    asm_bin.append("\trest %d" % command[1][1][1])
                else:
                    asm_bin.append("\tnote %s, %d" % (command[1][0], command[1][1][1]))
            case ";":
                asm_bin.append("\t; %s" % command[1])
            case ":":
                asm_bin.append("%s:" % command[1])
            case "L":
                asm_bin.append("\tsound_loop %d, %s" % command[1])
            case "J":
                asm_bin.append("\tsound_jump %s" % command[1])
            case "E":
                if envelope_type != command[1]:
                    envelope_changed = True
                    envelope_type = command[1]
            case "D":
                asm_bin.append("\tduty_cycle %d" % command[1])
            case "V":
                asm_bin.append("\tvibrato %d, %d, %d" % command[1])
            case "VO":
                asm_bin.append("\tvolume %d, %d" % command[1])
            case "PS":
                asm_bin.append("\tpitch_offset %d" % command[1])
            case "DS":
                asm_bin.append("\ttoggle_noise %d" % command[1])
            case "A":
                asm_bin.append("\t%s" % command[1])
            case _:
                asm_bin.append("; " + command.__str__())
    
    return asm_bin

with open(sys.argv[1], "r") as mml_file:
    song_name = "Untitled"
    author_name = None
    
    mml = mml_file.read()
    
    # preprocess mml
    get_preprocessors = re.finditer(r"#(title|author)\s+(.+)$", mml, re.MULTILINE | re.IGNORECASE)
    
    for i in get_preprocessors:
        match i.group(1):
            case "title":
                song_name = i.group(2)
            case "author":
                author_name = i.group(2)
    
    print("; %s" % song_name)
    if author_name:
        print("; by %s" % author_name)
    print("; generated by mml2pret.py on %s\n" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    song_name = song_name.title().replace(" ","")
    channels = {}
    
    # extract channels
    found_channels = re.finditer(r"(\w+)\s*{(.+?)}", mml, re.DOTALL | re.IGNORECASE | re.MULTILINE)
    
    for i in found_channels:
        channels[i.group(1)] = i.group(2)
    
    for i in channels:
        # get rid of all the whitespace
        channels[i] = re.sub(r"//[^\n]+$|/\*.+?\*/", "", channels[i], 0, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        channels[i] = re.sub(r"\n|^\s*|\s*$", "", channels[i], 0, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        pass
    
    for i in channels:
        channels[i] = "\n".join(commands2asm(mml2commands(channels[i], is_drums=(i.lower() == "d"))))
    
    print("Music_%s:" % song_name)
    print("; G/S/C header")
    print("\tchannel_count %d" % len(channels))
    channel = 0
    for i in channels:
        match i.lower():
            case "a":
                print("\tchannel 1, Music_%s_Ch1" % song_name)
            case "b":
                print("\tchannel 2, Music_%s_Ch2" % song_name)
            case "c":
                print("\tchannel 3, Music_%s_Ch3" % song_name)
            case "d":
                print("\tchannel 4, Music_%s_Ch4" % song_name)
            case _:
                raise Exception("Valid channels are A, B, C, D")
    for i in channels:
        print()
        match i.lower():
            case "a":
                print("Music_%s_Ch1:" % song_name)
                print(channels[i])
                print("\tsound_ret")
            case "b":
                print("Music_%s_Ch2:" % song_name)
                print(channels[i])
                print("\tsound_ret")
            case "c":
                print("Music_%s_Ch3:" % song_name)
                print(channels[i])
                print("\tsound_ret")
            case "d":
                print("Music_%s_Ch4:" % song_name)
                print(channels[i])
                print("\tsound_ret")
            case _:
                raise Exception("Valid channels are A, B, C, D")
    