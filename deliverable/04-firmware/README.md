# 04: Firmware (ATtiny3216, megaTinyCore 10 MHz)

Built from commit `299c015`. Instructions: `handoff-04-firmware.pdf`.

| Folder | File | Use |
|---|---|---|
| `release/` | `moon-light-attiny3216-v0.2-299c015.hex` | Flash this into the lamp. |
| `debug/` | `moon-light-attiny3216_debug-v0.2-299c015.hex` | Same, plus a 115200-baud log on J4 pin 3 (bring-up, VERIFY F-items). |
| `bench-only/fault-sensor-nack/` | `moon-light-bench_t_nack-v0.2-299c015.hex` | VERIFY T5a only: pretends the temperature sensor is dead. |
| `bench-only/fault-sensor-stuck/` | `moon-light-bench_t_stuck-v0.2-299c015.hex` | VERIFY T5b only: pretends the sensor reads 25 C forever. |
| `bench-only/thermostat-30C/` | `moon-light-bench_tstat_low-v0.2-299c015.hex` | VERIFY E17 only: hardware thermostat trips at 30 C, releases at 28 C. |

1. **Fuses first, once per chip:** `pio run -e attiny3216 -t fuses` from the firmware source. This sets BOD 2.6 V,
   EESAVE and the 10 MHz clock. Use PlatformIO for this step; don't type fuse bytes by hand, because a wrong
   SYSCFG0 value can lock out UPDI.
2. **Flash** with PlatformIO (`pio run -e attiny3216 -t upload`), or write the prebuilt hex with avrdude ≥ 7 and a
   3.3 V USB-UART as SerialUPDI:
   `avrdude -c serialupdi -p t3216 -P /dev/ttyUSB0 -b 230400 -U flash:w:release/moon-light-attiny3216-v0.2-299c015.hex:i`
3. Power the board from its own battery (slide switch ON). **Never from the programmer.** J4 pins: 1 VREF (sense
   only), 2 UPDI, 3 TX, 4 GND.

`source/firmware-source-*.zip` is the complete PlatformIO project: the portable core, 32 host tests and the mode
generator. Rebuild and test it with `pio test -e native && pio run`.
