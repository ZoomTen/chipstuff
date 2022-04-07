#!/usr/bin/python3
"""
Types defined for FurnaceTracker files.
"""

from enum import Enum

class EnumShowNameOnly(Enum):
    """
    Just an Enum, except if you `print` 'em it'll just show the
    name of the enum and not also its class.
    """
    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()

class FurnaceNote(EnumShowNameOnly):
    """
    All notes registered in Furnace
    """
    __  = 0
    Cs  = 1
    D_  = 2
    Ds  = 3
    E_  = 4
    F_  = 5
    Fs  = 6
    G_  = 7
    Gs  = 8
    A_  = 9
    As  = 10
    B_  = 11
    C_  = 12
    OFF     = 100
    OFF_REL = 101
    REL     = 102

class FurnaceInstrumentType(EnumShowNameOnly):
    """
    Instrument types currently available as of dev70
    """
    STANDARD    = 0
    FM_4OP      = 1
    GB          = 2
    C64         = 3
    AMIGA       = 4
    PCE         = 5
    SSG         = 6
    AY8930      = 7
    TIA         = 8
    SAA1099     = 9
    VIC         = 10
    PET         = 11
    VRC6        = 12
    FM_OPLL     = 13
    FM_OPL      = 14
    FDS         = 15
    VB          = 16
    N163        = 17
    KONAMI_SCC  = 18
    FM_OPZ      = 19
    POKEY       = 20
    PC_BEEPER   = 21
    WONDERSWAN  = 22
    LYNX        = 23
    VERA        = 24
    X1010       = 25

class FurnaceChip(EnumShowNameOnly):
    """
    FurnaceTracker planned and implemented chip database.
    Contains console name, ID and number of channels.
    """
    YMU759            = (0x01, 17)
    GENESIS           = (0x02, 10) # YM2612 + SN76489
    SMS               = (0x03,  4) # SN76489
    GB                = (0x04,  4) # LR53902
    PCE               = (0x05,  6) # HuC6280
    NES               = (0x06,  5) # RP2A03
    C64_8580          = (0x07,  4) # SID r8580
    SEGA_ARCADE       = (0x08, 13) # YM2151 + SegaPCM
    NEO_GEO_CD        = (0x09, 13)
    GENESIS_EX        = (0x42, 13) # YM2612 + SN76489
    SMS_JP            = (0x43, 13) # SN76489 + YM2413
    NES_VRC7          = (0x46, 11) # RP2A03 + YM2413
    C64_6581          = (0x47,  3) # SID r6581
    NEO_GEO_CD_EX     = (0x49, 16)
    AY38910           = (0x80,  3)
    AMIGA             = (0x81,  4) # Paula
    YM2151            = (0x82,  8)
    YM2612            = (0x83,  6)
    TIA               = (0x84,  2)
    VIC20             = (0x85,  4)
    PET               = (0x86,  1)
    SNES              = (0x87,  8) # SPC700
    VRC6              = (0x88,  3)
    OPLL              = (0x89,  9) # YM2413
    FDS               = (0x8a,  1)
    MMC5              = (0x8b,  3)
    N163              = (0x8c,  8)
    OPN               = (0x8d,  6) # YM2203
    PC98              = (0x8e, 16) # YM2608
    OPL               = (0x8f,  9) # YM3526
    OPL2              = (0x90,  9) # YM3812
    OPL3              = (0x91, 18) # YMF262
    MULTIPCM          = (0x92, 24)
    PC_SPEAKER        = (0x93,  1) # Intel 8253
    POKEY             = (0x94,  4)
    RF5C68            = (0x95,  8)
    WONDERSWAN        = (0x96,  4)
    SAA1099           = (0x97,  6)
    OPZ               = (0x98,  8)
    POKEMON_MINI      = (0x99,  1)
    AY8930            = (0x9a,  3)
    SEGAPCM           = (0x9b, 16)
    VIRTUAL_BOY       = (0x9c,  6)
    VRC7              = (0x9d,  6)
    YM2610B           = (0x9e, 16)
    ZX_BEEPER         = (0x9f,  6)
    YM2612_EX         = (0xa0,  9)
    SCC               = (0xa1,  5)
    OPL_DRUMS         = (0xa2, 11)
    OPL2_DRUMS        = (0xa3, 11)
    OPL3_DRUMS        = (0xa4, 20)
    NEO_GEO           = (0xa5, 14)
    NEO_GEO_EX        = (0xa6, 17)
    OPLL_DRUMS        = (0xa7, 11)
    LYNX              = (0xa8,  4)
    SEGAPCM_DMF       = (0xa9,  5)
    MSM6295           = (0xaa,  4)
    MSM6258           = (0xab,  1)
    COMMANDER_X16     = (0xac, 17)  # VERA
    BUBBLE_SYSTEM_WSG = (0xad,  2)
    SETA              = (0xae, 16)
    YM2610B_EX        = (0xaf, 19)
    QSOUND            = (0xe0, 19)

    def __new__(cls, id, channels):
        member = object.__new__(cls)
        member._value_ = id
        member.channels = channels
        return member
