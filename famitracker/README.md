# FamiTracker stuff

## ftmlib.py
General library for viewing FamiTracker (.ftm; .0cc)
modules.

## ftm2pret.py
Converts .ftm modules to .asm files suitable for use with the Pokemon
disassembly projects ([Red/Blue][1], [Gold/Silver][2], [Crystal][3]).
**Resulting file may need editing!**

[1]: https://github.com/pret/pokered
[2]: https://github.com/pret/pokegold
[3]: https://github.com/pret/pokecrystal

Depends on the above library, so both of these files **must** be in the
same folder!

Usage: `python ftm2pret.py your.ftm > your.asm`

Additional notes:
```
You define volume envelopes on ch1 and ch2 using the Axy command
Or rather, only A0x or Ax0, these will automatically be turned into the right envelope command

Use the volume column to set the volume of each note, the converter handles these so it doesn't make a bunch of duplicated commands

Use the Vxx effect to define the duty cycle

For the wave channel you only need to use the Triangle channel for now, I think you can use Axy to set which wave instrument it's using but I forgot if I already implemented it yet

For the noise channel, it's sensitive to instruments, not notes
The idea is that you mock up using a bunch of noise instruments with fixed arpeggios for kicks, drums, etc.
It doesn't matter which note you used but if the note is played using instrument 01 for example it'll get turned into a constant MY_SONG_DRUM_1
That way you can use it to define which instruments map to which drum in the drumset
The volume and effects columns should be unused here.
```
