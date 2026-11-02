"""Generate the project symbol library hardware/lib/reading_light.kicad_sym (custom symbols only)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from kigen import symlib  # noqa: E402
from kigen.sexpr import QStr  # noqa: E402
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



def lm75bdp():
    """KiCad's Sensor_Temperature:LM75B (derived from LM75C) flattened into a stand-alone LM75BDP (NXP, TSSOP-8).

    Same pins (1 SDA, 2 SCL, 3 OS, 4 GND, 5 A2, 6 A1, 7 A0, 8 VCC). A project copy avoids ERC's lib_symbol_mismatch,
    which fires because KiCad flattens the derived library symbol differently from kigen's embedded copy."""
    sym = symlib.load("Sensor_Temperature:LM75B")
    sym[1] = QStr("LM75BDP")
    for item in sym[2:]:
        if isinstance(item, list) and item and item[0] == "symbol" and str(item[1]).startswith("LM75B_"):
            item[1] = QStr("LM75BDP_" + str(item[1])[len("LM75B_"):])
        if isinstance(item, list) and item and item[0] == "property":
            if item[1] == "Value":
                item[2] = QStr("LM75BDP")
            elif item[1] == "Footprint":
                item[2] = QStr("Package_SO:TSSOP-8_3x3mm_P0.65mm")
            elif item[1] == "Datasheet":
                item[2] = QStr("https://www.nxp.com/docs/en/data-sheet/LM75B.pdf")
            elif item[1] == "Description":
                item[2] = QStr("Digital temperature sensor and thermal watchdog, I2C, +/-2 C, 2.8-5.5 V, TSSOP-8 (NXP)")
            elif item[1] == "ki_fp_filters":
                item[2] = QStr("TSSOP*3x3mm*P0.65mm*")
    return sym


if __name__ == "__main__":
    write_lib(OUT, [tlc, lm75bdp()])
    print("wrote", OUT)
