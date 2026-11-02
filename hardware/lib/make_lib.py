"""Generate the project symbol library hardware/lib/reading_light.kicad_sym (custom symbols only)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from kigen.symgen import ic_symbol, write_lib  # noqa: E402

OUT = Path(__file__).with_name("reading_light.kicad_sym")

tlc = ic_symbol(
    "TLC59116IPW", "U",
    left=[("28", "VCC", "power_in"), ("27", "SDA", "bidirectional"), ("26", "SCL", "input"),
          ("25", "~{RESET}", "input"), None, ("1", "REXT", "passive"), None,
          ("2", "A0", "input"), ("3", "A1", "input"), ("4", "A2", "input"), ("5", "A3", "input"), None,
          ("10", "GND", "power_in"), ("19", "GND", "power_in"), ("24", "GND", "power_in")],
    right=[("6", "OUT0", "open_collector"), ("7", "OUT1", "open_collector"), ("8", "OUT2", "open_collector"),
           ("9", "OUT3", "open_collector"), ("11", "OUT4", "open_collector"), ("12", "OUT5", "open_collector"),
           ("13", "OUT6", "open_collector"), ("14", "OUT7", "open_collector"), ("15", "OUT8", "open_collector"),
           ("16", "OUT9", "open_collector"), ("17", "OUT10", "open_collector"), ("18", "OUT11", "open_collector"),
           ("20", "OUT12", "open_collector"), ("21", "OUT13", "open_collector"), ("22", "OUT14", "open_collector"),
           ("23", "OUT15", "open_collector")],
    width=17.78,
    desc="16-channel I2C constant-current LED sink driver, 5-120 mA, 97 kHz 8-bit PWM per channel, TSSOP-28",
    footprint="Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm",
    datasheet="https://www.ti.com/lit/ds/symlink/tlc59116.pdf", keywords="LED driver I2C constant current")

if __name__ == "__main__":
    write_lib(OUT, [tlc])
    print("wrote", OUT)
