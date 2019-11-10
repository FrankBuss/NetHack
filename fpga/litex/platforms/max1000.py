# This file is Copyright (c) 2019 Antti Lukats <antti.lukats@gmail.com>
# This file is Copyright (c) 2014-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

from litex.build.generic_platform import *
from litex.build.altera import AlteraPlatform
from litex.build.altera.programmer import USBBlaster

# IOs ----------------------------------------------------------------------------------------------

_io = [
    ("clk12", 0, Pins("H6"), IOStandard("3.3-V LVTTL")),    # 12MHz clock
    ("user_led", 0, Pins("C5"), IOStandard("3.3-V LVTTL")), # CONF Done, inverted polarity

    ("sw", 0, Pins("E6"), IOStandard("3.3-V LVTTL")),
    ("sw", 1, Pins("E7"), IOStandard("3.3-V LVTTL")), # nConfig

    ("serial", 0,
        Subsignal("tx", Pins("B4"), IOStandard("3.3-V LVTTL")),
        Subsignal("rx", Pins("A4"), IOStandard("3.3-V LVTTL"))
    ),

    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("B3")),
        Subsignal("clk", Pins("A3")),
        Subsignal("dq", Pins("A2", "B2", "B9", "C4")),
        IOStandard("3.3-V LVTTL")
    ),
    ("spiflash", 0,
        Subsignal("cs_n", Pins("B3")),
        Subsignal("clk", Pins("A3")),
        Subsignal("mosi", Pins("A2")),
        Subsignal("miso", Pins("B2")),
        Subsignal("wp", Pins("B9")),
        Subsignal("hold", Pins("C4")),
        IOStandard("3.3-V LVTTL"),
    ),

    ("vga", 0,
        Subsignal("red", Pins("K11", "J13", "J12", "L12", "N3", "N2")),
        Subsignal("green", Pins("K2", "K1", "J2", "J1", "H4", "H5")),
        Subsignal("blue", Pins("K10", "H8", "E4", "F1", "E3", "D1")),
        Subsignal("hsync", Pins("C2")),
        Subsignal("vsync", Pins("C1")),
        IOStandard("3.3-V LVTTL"),
    ),

    ("sdram_clock", 0, Pins("M9"), IOStandard("3.3-V LVTTL")),
    ("sdram", 0,
        Subsignal("a", Pins("K6 M5 N5 J8 N10 M11 N9 L10 M13 N8 N4 M10")), #0, 1, ...
        Subsignal("ba", Pins("N6 K8")),
        Subsignal("cs_n", Pins("M4")),
        Subsignal("cke", Pins("M8")),
        Subsignal("ras_n", Pins("M7")),
        Subsignal("cas_n", Pins("N7")),
        Subsignal("we_n", Pins("K7")),
        Subsignal("dq", Pins("D11 G10 F10 F9 E10 D9 G9 F8 F13 E12 E13 D12 C12 B12 B13 A12")),
        Subsignal("dm", Pins("E9 F12")),
        IOStandard("3.3-V LVTTL")
    ),

#    ("epcs", 0,
#        Subsignal("data0", Pins("H2")),
#        Subsignal("dclk", Pins("A3")),
#        Subsignal("ncs0", Pins("B3")),
#        Subsignal("asd0", Pins("C1")),
#        IOStandard("3.3-V LVTTL")
#    ),

#    ("i2c", 0,
#        Subsignal("sclk", Pins("F2")),
#        Subsignal("sdat", Pins("F1")),
#        IOStandard("3.3-V LVTTL")
#    ),

#    ("g_sensor", 0,
#        Subsignal("cs_n", Pins("G5")),
#        Subsignal("int", Pins("M2")),
#        IOStandard("3.3-V LVTTL")
#    ),

    ("gpio_leds", 0,
        Pins("D8 A8 A9 C9 A10 B10 A11 C10"),
        IOStandard("3.3-V LVTTL")
    ),

]

# Platform -----------------------------------------------------------------------------------------

class Platform(AlteraPlatform):
    default_clk_name = "clk12"
    default_clk_period = 83

    def __init__(self, device):
        AlteraPlatform.__init__(self, device, _io)
        self.add_platform_command("set_global_assignment -name FAMILY \"MAX 10\"")
        self.add_platform_command("set_global_assignment -name ENABLE_CONFIGURATION_PINS OFF")
        self.add_platform_command("set_global_assignment -name INTERNAL_FLASH_UPDATE_MODE \"SINGLE IMAGE WITH ERAM\"")

    def create_programmer(self):
        return USBBlaster()
