#!/usr/bin/env python3

# This file is Copyright (c) 2019 Antti Lukats <antti.lukats@gmail.com>
# This file is Copyright (c) 2019 msloniewski <marcin.sloniewski@gmail.com>
# License: BSD

import argparse

from migen import *

from litex_boards.partner.platforms import max1000

from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *

from litex.soc.integration.builder import *

from litedram.modules import MT48LC4M16
from litedram.phy import GENSDRPHY

from litex.soc.cores import gpio
from litex.soc.cores.spi_flash import SpiFlash
from litex.soc.interconnect.csr import *
from litex.soc.interconnect import wishbone

from litevideo.terminal.core import Terminal

class ClassicLed(Module):
    def __init__(self, pads):
        gpio.GPIOOut.__init__(self, pads)

# CRG ----------------------------------------------------------------------------------------------
class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain()
        self.clock_domains.cd_vga = ClockDomain()
        self.clock_domains.cd_por = ClockDomain(reset_less=True)

        # # #

        self.cd_sys.clk.attr.add("keep")
        self.cd_sys_ps.clk.attr.add("keep")
        self.cd_por.clk.attr.add("keep")

        # clock input always available
        clk12 = platform.request("clk12")

        # power on rst
        rst_n = Signal()
        self.sync.por += rst_n.eq(1)
        self.comb += [
            self.cd_por.clk.eq(clk12),
            self.cd_sys.rst.eq(~rst_n),
            self.cd_sys_ps.rst.eq(~rst_n)
        ]

        clk_outs = Signal(5)

        self.comb += self.cd_sys.clk.eq(clk_outs[0]) # C0
        self.comb += self.cd_sys_ps.clk.eq(clk_outs[1]) # C1
        
        # 25 MHz for 640x480. VESA standard is 25.175 MHz, but allows 0.5% deviation, close enough.
        self.comb += self.cd_vga.clk.eq(clk_outs[2]) # C2

        #
        # PLL we need 2 clocks one system one for SDRAM phase shifter
        # 

        self.specials += \
            Instance("ALTPLL",
                p_BANDWIDTH_TYPE="AUTO",
                p_CLK0_DIVIDE_BY=6,
                p_CLK0_DUTY_CYCLE=50,
                p_CLK0_MULTIPLY_BY=25,
                p_CLK0_PHASE_SHIFT="0",
                p_CLK1_DIVIDE_BY=6,
                p_CLK1_DUTY_CYCLE=50,
                p_CLK1_MULTIPLY_BY=25, 
                p_CLK1_PHASE_SHIFT="-10000",
                p_CLK2_DIVIDE_BY=12,
                p_CLK2_DUTY_CYCLE=50,
                p_CLK2_MULTIPLY_BY=25, 
                p_CLK2_PHASE_SHIFT="0",
                p_COMPENSATE_CLOCK="CLK0",
                p_INCLK0_INPUT_FREQUENCY=83000,
                p_INTENDED_DEVICE_FAMILY="MAX 10",
                p_LPM_TYPE = "altpll",
                p_OPERATION_MODE = "NORMAL",
                i_INCLK=clk12,
                o_CLK=clk_outs, # we have total max 5 Cx clocks
                i_ARESET=~rst_n,
                i_CLKENA=0x3f,
                i_EXTCLKENA=0xf,
                i_FBIN=1,
                i_PFDENA=1,
                i_PLLENA=1,
            )
        self.comb += platform.request("sdram_clock").eq(self.cd_sys_ps.clk)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCSDRAM):
#class BaseSoC(SoCCore):
    csr_peripherals = (
        "leds"
    )
#    csr_map.update(SoCCore.csr_map, csr_peripherals)

    def __init__(self, device, sys_clk_freq=int(50e6), **kwargs):
        assert sys_clk_freq == int(50e6)

        platform = max1000.Platform(device)

#        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq,
#                          integrated_rom_size=0x8000,
#                          **kwargs)


#    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq,
            integrated_rom_size=0x6000,
#            integrated_main_ram_size=0x4000,
            **kwargs)
 
        self.mem_map['spiflash'] = 0x20000000
        spiflash_pads = platform.request('spiflash')
        self.add_memory_region(
            "spiflash", self.mem_map["spiflash"], 8*1024*1024)

        self.submodules.spiflash = SpiFlash(
                spiflash_pads,
                dummy=8,
                div=4,
                endianness=self.cpu.endianness)
        self.add_csr("spiflash")

        #self.spiflash.add_clk_primitive("xc7");    

        # 8 MB flash: W74M64FVSSIQ
        self.add_constant("SPIFLASH_PAGE_SIZE", 256)
        self.add_constant("SPIFLASH_SECTOR_SIZE", 4096)
        self.add_constant("FLASH_BOOT_ADDRESS", self.mem_map['spiflash'])

        # spi_flash.py supports max 16MB linear space
        self.add_wb_slave(mem_decoder(self.mem_map["spiflash"]), self.spiflash.bus)

        self.submodules.crg = crg = _CRG(platform)

        # create VGA terminal
        self.mem_map['terminal'] = 0x30000000
        self.submodules.terminal = terminal = Terminal()
        self.add_wb_slave(mem_decoder(self.mem_map["terminal"]), self.terminal.bus)
        self.add_memory_region("terminal", self.mem_map["terminal"], 0x10000)

        # connect VGA pins
        vga = platform.request('vga', 0)
        self.comb += [
            vga.vsync.eq(terminal.vsync),
            vga.hsync.eq(terminal.hsync),
            vga.red.eq(terminal.red[2:8]),
            vga.green.eq(terminal.green[2:8]),
            vga.blue.eq(terminal.blue[2:8])
        ]
 
#        self.submodules.leds = ClassicLed(Cat(platform.request("user_led", i) for i in range(7)))
        self.add_csr("leds", allow_user_defined=True)
        self.submodules.leds = ClassicLed(platform.request("user_led", 0))

#        self.add_csr("gpio_leds", allow_user_defined=True)
        self.add_csr("gpio_leds", allow_user_defined=True)
        self.submodules.gpio_leds = gpio.GPIOOut(platform.request("gpio_leds"))


# use micron device as winbond and ISSI not available

        if not self.integrated_main_ram_size:
            self.submodules.sdrphy = GENSDRPHY(platform.request("sdram"))
            sdram_module = MT48LC4M16(self.clk_freq, "1:1")
            self.register_sdram(self.sdrphy,
                                sdram_module.geom_settings,
                                sdram_module.timing_settings)

# Build --------------------------------------------------------------------------------------------

def testbench(dut):
    for i in range(100):
        yield dut.clk.eq(i & 1)
        yield
        print("text_addr:{} text_addr_start:{}".format((yield dut.terminal.text_addr_start), (yield dut.terminal.text_addr_start)))

        # current line within a character, 0 to 15
        #self.fline = fline = Signal(4)

        # current x position within a character, 0 to 7
        #self.fx = fx = Signal(3)

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on MAX1000")
    builder_args(parser)
    parser.add_argument("device", choices=['8', '16'], help='Cyclone device: "8" for 10M08SAU169C8G or "16" for 10M16SAU169C8G')

    soc_sdram_args(parser)
#    soc_core_args(parser)

    args = parser.parse_args()

    if args.device == '16':
        device = '10M16SAU169C8G'
    else:
        device = '10M08SAU169C8G'
    soc = BaseSoC(device, **soc_sdram_argdict(args))

#    cls = BaseSoC
#    soc = cls(**soc_core_argdict(args))

    # run_simulation(soc, testbench(soc))

    Builder(soc, **builder_argdict(args)).build()

if __name__ == "__main__":
    main()
