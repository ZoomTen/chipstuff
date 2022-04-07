# Furnace stuff

## furnacelib
General library for viewing Furnace (.fur) modules. Although Furnace supports Deflemask (.dmf) modules, please see `../deflemask` for those tools.

**WORK IN PROGRESS**

## fur2pret

Tool to convert .fur modules to .asm files for the [pret](https://github.com/pret) Pokemon GBC disassembles.

Depends on `furnacelib`.

## vgm2fui_OPM

Standalone tool to (try and) extract OPM (YM2151) instruments from .vgm and .vgz files to .fui instruments.

The tool can extract *some* instruments out of *some* VGM, there's no guarantee that your specific VGM will work.
