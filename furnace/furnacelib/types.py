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

class FurnaceMacroItem(EnumShowNameOnly):
    """
    Special values used only in this parser
    """
    LOOP    = 0
    RELEASE = 1

class FurnaceMacroCode(EnumShowNameOnly):
    """
    Used in FurnaceInstrumentDX
    """
    VOL = 0
    ARP = 1
    DUTY = 2
    WAVE = 3
    PITCH = 4
    EX1 = 5
    EX2 = 6
    EX3 = 7
    ALG = 8
    FB = 9
    FMS = 10
    AMS = 11
    PAN_L = 12
    PAN_R = 13
    PHASE_RESET = 14
    EX4 = 15
    EX5 = 16
    EX6 = 17
    EX7 = 18
    EX8 = 19
    STOP = 255

class FurnaceMacroType(EnumShowNameOnly):
    """
    Used in FurnaceInstrumentDX
    """
    SEQUENCE = 0
    ADSR = 1
    LFO = 2

class FurnaceMacroSize(EnumShowNameOnly):
    """
    Used in FurnaceInstrumentDX
    """
    UINT8 = (0, 1)
    INT8 = (1, 1)
    INT16 = (2, 2)
    INT32 = (3, 4)

    def __new__(cls, id, num_bytes):
        member = object.__new__(cls)

        member._value_ = id
        member.num_bytes = num_bytes
        return member

class FurnaceSampleType(EnumShowNameOnly):
    """
    Sample types used in Furnace
    """
    ZX_DRUM      = 0
    NES_DPCM     = 1
    QSOUND_ADPCM = 4
    ADPCM_A      = 5
    ADPCM_B      = 6
    X68K_ADPCM   = 7
    PCM_8        = 8
    SNES_BRR     = 9
    VOX          = 10
    PCM_16       = 16

class FurnaceInstrumentType(EnumShowNameOnly):
    """
    Instrument types currently available as of dev127
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
    VRC6_SAW    = 26
    ES5506      = 27
    MULTIPCM    = 28
    SNES        = 29
    TSU         = 30
    NAMCO_WSG   = 31
    OPL_DRUMS   = 32
    FM_OPM      = 33
    NES         = 34
    MSM6258     = 35
    MSM6295     = 36
    ADPCM_A     = 37
    ADPCM_B     = 38
    SEGAPCM     = 39
    QSOUND      = 40
    YMZ280B     = 41
    RF5C68      = 42
    MSM5232     = 43
    T6W28       = 44

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
    OPL4              = (0xae, 42)
    OPL4_DRUMS        = (0xaf, 44)
    SETA              = (0xb0, 16) # Allumer X1-010
    ES5506            = (0xb1, 32)
    Y8950             = (0xb2, 10)
    Y8950_DRUMS       = (0xb3, 12)
    SCC_PLUS          = (0xb4, 5)
    YM2610B_EX        = (0xde, 19)
    QSOUND            = (0xe0, 19)
    PONG              = (0xfc, 1)
    DUMMY             = (0xfd, 1)
    RESERVED_1        = (0xfe, 1)
    RESERVED_2        = (0xff, 1)

    def __new__(cls, id, channels):
        member = object.__new__(cls)

        member._value_ = id
        member.channels = channels
        return member
