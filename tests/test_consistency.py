"""Cross-domain consistency: firmware <-> netlists <-> design files. Run: python3 -m pytest tests -q
(needs KiCad 9's kicad-cli on PATH and the generated hardware/*/reports/*.net from hardware/build.py)."""
import importlib.util
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {"WW": 0, "CW": 1, "R": 2, "G": 3, "B": 4}


def netlist(board):
    path = ROOT / "hardware" / board / "reports" / f"{board}.test.net"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(path),
                    str(ROOT / "hardware" / board / f"{board}.kicad_sch")], check=True, capture_output=True)
    text = path.read_text()
    path.unlink()
    nets = {}
    for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]+)"\)(.*?)\)\s*\)\s*(?=\(net |\)\s*\)\s*$)', text, re.S):
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2))
        nets[m.group(1)] = nodes
    return nets


def load_design(board):
    spec = importlib.util.spec_from_file_location(f"{board}_d", ROOT / "hardware" / board / "design.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def board_map():
    txt = (ROOT / "firmware" / "include" / "board_map.h").read_text()
    return [int(x) for x in re.search(r"OUT_GROUP\[16\] = \{([^}]*)\}", txt).group(1).split(",")]


def test_board_map_matches_led_netlist():
    d = load_design("led-board")
    nets = netlist("led-board")
    led_group = {ref: grp for ref, grp, _ in d.WHITE}
    rgb_pin = {"3": "R", "4": "G", "2": "B"}            # Device:LED_ABRG / Wurth 150141M173100
    rgb_refs = {ref for ref, _ in d.RGB}
    expect = [-1] * 16
    for out, pin in d.PIN_OF_OUT.items():
        for name, nodes in nets.items():
            if ("U1", pin) in nodes:
                others = [(r, p) for r, p in nodes if r != "U1"]
                for r, p in others:
                    if r in led_group and p == "1":
                        expect[out] = GROUPS[led_group[r]]
                    elif r in rgb_refs and p in rgb_pin:
                        expect[out] = GROUPS[rgb_pin[p]]
    assert board_map() == expect


def test_firmware_pins_match_main_board():
    d = load_design("main-board")
    mcu = next(p for p in d.parts() if p.ref == "U2").pins
    cfg = (ROOT / "firmware" / "include" / "config.h").read_text()
    soic = {"PA4": "2", "PA5": "3", "PA6": "4", "PB2": "9", "PB0": "11", "PB1": "10", "PA1": "17", "PA0": "16"}
    for macro, net in (("PIN_BTN_UP", "BTN_UP"), ("PIN_BTN_MAIN", "BTN_MAIN"), ("PIN_BTN_DN", "BTN_DN"),
                       ("PIN_LED_EN_N", "LED_EN_N")):
        port = re.search(rf"#define {macro}\s+PIN_(P[ABC]\d)", cfg).group(1)
        assert mcu[soic[port]] == net, (macro, port)
    assert mcu["11"] == "SCL" and mcu["10"] == "SDA" and mcu["16"] == "UPDI" and mcu["17"] == "TX"


def test_channel_current_constant_matches_rext():
    d = load_design("led-board")
    rext = next(p for p in d.parts() if p.ref == "R1")
    ohms = float(rext.value.split()[0])
    i_ma = 1.26 / ohms * 15 * 0.992 * 1000                 # TLC59116 DS eq. 3-5, CG at power-up
    core = (ROOT / "firmware" / "lib" / "core" / "lightcore.h").read_text()
    fw = float(re.search(r"#define I_CHANNEL_MA\s+([\d.]+)f", core).group(1))
    assert abs(fw - i_ma) < 0.2, (fw, i_ma)


def test_group_led_counts_match_firmware():
    d = load_design("led-board")
    core = (ROOT / "firmware" / "lib" / "core" / "lightcore.cpp").read_text()
    counts = [int(x) for x in re.search(r"GROUP_LEDS\[G_COUNT\] = \{([^}]*)\}", core).group(1).split(",")]
    ww = sum(1 for w in d.WHITE if w[1] == "WW")
    cw = sum(1 for w in d.WHITE if w[1] == "CW")
    n = len(d.RGB)
    assert counts == [ww, cw, n, n, n]
