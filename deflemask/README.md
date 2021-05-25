# DefleMask stuff

## deflelib.py
General library for viewing DefleMask (.dmf)
modules.

## dmf2pret.py
Converts .dmf modules to .asm files suitable for use with the Pokemon
disassembly projects ([Red/Blue][1], [Gold/Silver][2], [Crystal][3]).
**Resulting file may need editing!**

[1]: https://github.com/pret/pokered
[2]: https://github.com/pret/pokegold
[3]: https://github.com/pret/pokecrystal

Depends on the above library, so both of these files **must** be in the
same folder!

Usage: `python dmf2pret.py your.dmf > your.asm`
