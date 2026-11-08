"""Schematic images of the SPICE circuits as simulated (schemdraw). Reference designators follow the boards."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import schemdraw  # noqa: E402
import schemdraw.elements as e  # noqa: E402

FIG = Path(__file__).resolve().parents[1] / "docs" / "verification" / "spice"
NOTE = "#52514e"
ACC = "#2a78d6"


def _d():
    d = schemdraw.Drawing(show=False)
    d.config(fontsize=10, unit=2.2, lw=1.1, bgcolor="#fcfcfb")
    return d


def _fet(d, x, y, src_left=True, gate_up=True, label=""):
    """Horizontal P-FET with its source or drain at (x, y); returns (source, drain, gate) points."""
    for rev in (False, True):
        el = e.PMos().theta(90 if src_left else -90)
        if rev:
            el = el.reverse()
        el = el.at((x, y)).anchor("source" if src_left else "drain")
        tmp = schemdraw.Drawing(show=False)
        tmp += el
        gy = el.absanchors["gate"][1]
        if (gy > y) == gate_up:
            d += el.label(label, loc="bottom" if gate_up else "top", ofst=0.15, fontsize=10)
            A = el.absanchors
            return tuple(A["source"]), tuple(A["drain"]), tuple(A["gate"])
    raise RuntimeError("fet orientation")


def _drop(d, x, y0, el, label, y1=-2.4, gnd=True, lab_loc="bottom"):
    d += el.at((x, y0)).down().length(y0 - y1).label(label, loc=lab_loc, fontsize=9)
    if gnd:
        d += e.Ground().at((x, y1))


def power_path(path):
    d = _d()
    # ---- cell model (rail y = 0)
    d += e.SourceV().at((0, -2.4)).up().length(2.4).label("OCV(SoC)", loc="bottom", fontsize=9)
    d += e.Ground().at((0, -2.4))
    d += e.Resistor().at((0, 0)).to((1.8, 0)).label("Rint 0.2 Ω", loc="bottom", fontsize=9)
    d += e.Inductor2(loops=2).at((1.8, 0)).to((3.4, 0)).label("lead 150 nH", loc="bottom", fontsize=9)
    d += e.Line().at((3.4, 0)).to((4.0, 0))
    d += e.Dot().at((4.0, 0)).label("BAT_RAW", loc="top", fontsize=8)
    s3, d3, g3 = _fet(d, 4.0, 0, src_left=False, gate_up=False, label="Q3")
    d += e.Line().at(g3).to((g3[0], -1.2))
    d += e.Resistor().at((g3[0], -1.2)).to((g3[0], -3.0)).label("R10 10k", loc="bottom", fontsize=9)
    d += e.Ground().at((g3[0], -3.0))
    d += e.Line().at(s3).to((6.6, 0))
    d += e.Dot().at((6.17, 0)).label("BAT", loc="bottom", fontsize=8)
    s1, d1, g1 = _fet(d, 6.6, 0, src_left=False, gate_up=True, label="Q1")
    d += e.Line().at(s1).to((9.8, 0))
    d += e.Dot().at((9.0, 0))
    d += e.Label().at((8.7, -0.45)).label("VSYS_RAW", fontsize=8)
    # Q2 + soft-start network below the rail
    s2, d2, g2 = _fet(d, 9.8, 0, src_left=True, gate_up=False, label="")
    d += e.Label().at((10.6, 0.7)).label("Q2", fontsize=10)
    d += e.Line().at(g2).to((g2[0], -2.0))
    d += e.Dot().at((g2[0], -2.0)).label("SW_GATE", loc="right", fontsize=8)
    d += e.Dot().at((9.3, 0))
    d += e.Capacitor().at((9.3, 0)).to((9.3, -2.0)).label("C5 100n\n∥ R6 1M", loc="top", fontsize=9)
    d += e.Line().at((9.3, -2.0)).to((g2[0], -2.0))
    d += e.Resistor().at((g2[0], -2.0)).to((g2[0], -3.6)).label("R7 10k", loc="bottom", fontsize=9)
    d += e.Switch().at((g2[0], -3.6)).to((g2[0], -5.0)).label("SW1 (ON = COM to GND)", loc="bottom",
                                                               fontsize=9)
    d += e.Ground().at((g2[0], -5.0))
    d += e.Line().at(d2).to((17.0, 0))
    d += e.Dot().at((12.2, 0)).label("VSYS", loc="top", fontsize=9)
    for x, el, lab in ((12.6, e.Capacitor(), "C4 10µ*"), (14.3, e.Capacitor(), "C7 1µ* ∥\nC6 100n"),
                       (16.5, e.SourceI(), "MCU\n2.5 mA")):
        d += e.Dot().at((x, 0))
        _drop(d, x, 0, el, lab)
    d += e.Arrow().at((17.0, 0)).to((18.2, 0)).label("to Q4 → VLED", loc="top", fontsize=9)
    # ---- USB rail (y = 5)
    Y = 5.0
    d += e.SourceV().at((0, 2.6)).up().length(Y - 2.6).label("USB 4.75-5.25 V", loc="bottom", fontsize=9)
    d += e.Ground().at((0, 2.6))
    d += e.Resistor().at((0, Y)).to((1.6, Y)).label("cable 0.1-0.3 Ω", loc="top", fontsize=9)
    d += e.Inductor2(loops=2).at((1.6, Y)).to((2.8, Y)).label("1 µH", loc="top", fontsize=9)
    d += e.Fuse().at((2.8, Y)).to((4.2, Y)).label("F1 PTC\n0.06-0.2 Ω", loc="top", fontsize=9)
    d += e.Line().at((4.2, Y)).to((9.0, Y))
    d += e.Label().at((8.0, Y + 0.35)).label("VBUS", fontsize=9)
    d += e.Dot().at((4.6, Y))
    d += e.DiodeTVS().at((4.6, Y)).to((4.6, 3.0)).label("D1\nSMF5.0A", loc="top", fontsize=8)
    d += e.Ground().at((4.6, 3.0))
    d += e.Dot().at((5.4, Y))
    d += e.Capacitor().at((5.4, Y)).to((5.4, 3.0)).label("C1 10µ*\n∥ R5 10k", loc="bottom", fontsize=8)
    d += e.Ground().at((5.4, 3.0))
    # charger block between VBUS and BAT
    d += e.Dot().at((6.17, Y))
    d += e.Line().at((6.17, Y)).to((6.17, 3.0)).color(ACC)
    for a_, b_ in (((5.95, 1.4), (7.05, 1.4)), ((7.05, 1.4), (7.05, 3.0)), ((7.05, 3.0), (5.95, 3.0)),
                   ((5.95, 3.0), (5.95, 1.4))):
        d += e.Line().at(a_).to(b_).color(ACC)
    d += e.Label().at((6.5, 2.2)).label("U1", fontsize=9, color=ACC)
    d += e.Line().at((6.17, 1.4)).to((6.17, 0)).color(ACC)
    d += e.Label().at((7.2, 2.2)).label("MCP73831 (behavioural)\nCC 256 mA, CV 4.20 V", fontsize=8, color=ACC,
                                        halign="left")
    d += e.Line().at(g1).to((g1[0], Y))
    d += e.Dot().at((g1[0], Y))
    d += e.Dot().at((9.0, Y))
    d += e.Diode().at((9.0, Y)).to((9.0, 0)).label("D3 S1J", loc="bottom", fontsize=9)
    d += e.Label().at((11.0, 4.2)).label("* MLCC: bias-dependent model\n  (10 µF 0805 ≈ 6.3 µF at 4.2 V)",
                                         fontsize=8, color=NOTE, halign="left")
    d.save(str(path), dpi=130)


def led_path(path):
    d = _d()
    d += e.Dot(open=True).at((-1.6, 0)).label("VSYS", loc="left", fontsize=9)
    d += e.Line().at((-1.6, 0)).to((0, 0))
    s4, d4, g4 = _fet(d, 0, 0, src_left=True, gate_up=True, label="Q4")
    d += e.Line().at((-1.6, 0)).to((-1.6, 2.2))
    d += e.Resistor().at((-1.6, 2.2)).to((g4[0], 2.2)).label("R12 100k", loc="top", fontsize=9)
    d += e.Line().at(g4).to((g4[0], 2.2))
    d += e.Dot().at((g4[0], 2.2)).label("Q4_G", loc="right", fontsize=8, ofst=(0.1, 0.25))
    d += e.Resistor().at((g4[0], 2.2)).to((g4[0], 4.2)).label("R13 10k", loc="bottom", fontsize=9)
    d += e.Dot(open=True).at((g4[0], 4.2)).label("PB2: VSYS → 0 V", loc="right", fontsize=9)
    d += e.Line().at((g4[0], 2.2)).to((1.4, 2.2))
    d += e.Capacitor().at((1.4, 2.2)).to((3.0, 2.2)).label("C8 100n", loc="top", fontsize=9)
    d += e.Line().at((3.0, 2.2)).to((3.0, 0))
    d += e.Line().at(d4).to((3.4, 0))
    d += e.Dot().at((3.0, 0)).label("VLED", loc="bottom", fontsize=9)
    # cable (both conductors)
    d += e.Resistor().at((3.4, 0)).to((4.9, 0)).label("63 mΩ", loc="top", fontsize=9)
    d += e.Inductor2(loops=2).at((4.9, 0)).to((6.2, 0)).label("75 nH", loc="top", fontsize=9)
    d += e.Label().at((4.8, -0.8)).label("neck cable: J3 + 2 × 200 mm 28 AWG", fontsize=8, color=NOTE)
    d += e.Line().at((6.2, 0)).to((16.4, 0))
    d += e.Label().at((7.0, 0.35)).label("VLED at the LED board", fontsize=8, halign="left")
    yb = -5.0
    cols = ((7.2, e.Capacitor(), "C2 10µ\n0603*"), (9.2, e.Capacitor(), "C1 1µ*\nC3 100n"),
            (11.2, e.SourceI(), "LP5012 VCC\n4-10 mA,\nMCP9800"))
    for x, el, lab in cols:
        d += e.Dot().at((x, 0))
        d += el.at((x, 0)).down().length(2.2).label(lab, loc="bottom", fontsize=8)
        d += e.Line().at((x, -2.2)).to((x, yb))
    for x, lab, slab in ((13.6, "8 × white\n(D1-D8)", "LP5012 sinks\n25 mA × duty"), (16.4, "RGB D9\nR, G, B",
                                                                                         "3 sinks")):
        d += e.Dot().at((x, 0)) if x < 16 else e.Line().at((x, 0)).to((x, 0))
        d += e.Diode().at((x, 0)).to((x, -2.2)).label(lab, loc="bottom", fontsize=8)
        d += e.SourceI().at((x, -2.2)).down().length(2.2).label(slab, loc="bottom", fontsize=8)
        d += e.Line().at((x, -4.4)).to((x, yb))
    d += e.Line().at((16.4, yb)).to((6.2, yb))
    d += e.Inductor2(loops=2).at((6.2, yb)).to((4.9, yb)).label("75 nH", loc="bottom", fontsize=9)
    d += e.Resistor().at((4.9, yb)).to((3.4, yb)).label("63 mΩ", loc="bottom", fontsize=9)
    d += e.Line().at((3.4, yb)).to((3.0, yb))
    d += e.Ground().at((3.0, yb))
    d.save(str(path), dpi=130)


def models(path):
    d = _d()
    T = lambda x, y, t, **k: e.Label().at((x, y)).label(t, fontsize=k.pop("fs", 9), halign=k.pop("ha", "left"),
                                                        **k)  # noqa: E731
    # (1) cell
    d += e.SourceV().at((0, -2.4)).up().length(2.4)
    d += e.Ground().at((0, -2.4))
    d += T(0.9, -1.2, "OCV = pwl(SoC)")
    d += e.Resistor().at((0, 0)).to((2.2, 0)).label("Rint 0.2 Ω", loc="top", fontsize=9)
    d += e.Inductor2(loops=2).at((2.2, 0)).to((4.0, 0)).label("150 nH", loc="top", fontsize=9)
    d += e.Dot(open=True).at((4.0, 0))
    d += T(4.2, 0, "cell +")
    d += T(0, -3.6, "Cell: SoC = SoC0 − ∫ I dt / (1.2 Ah)", color=NOTE)
    # (2) LP5012 channel
    x = 8.0
    d += e.Dot(open=True).at((x, 1.2))
    d += T(x + 0.3, 1.2, "VLED")
    d += e.Diode().at((x, 1.2)).down().length(2.2)
    d += T(x + 0.6, 0.1, "LED, VF fitted to\nthe datasheet points")
    d += e.SourceI().at((x, -1.0)).down().length(2.2)
    d += T(x + 0.6, -2.1, "I = 25 mA × duty\n× tanh(Vout / (VSAT / 1.83))")
    d += e.Ground().at((x, -3.2))
    d += T(x - 0.4, -4.3, "LP5012 channel (Vout = VSAT gives 95 %)", color=NOTE)
    # (3) MLCC
    x = 16.0
    d += e.Dot(open=True).at((x, 1.6))
    d += e.Resistor().at((x, 1.6)).down().length(1.4)
    d += T(x - 1.6, 0.9, "ESR")
    d += e.Dot().at((x, 0.2))
    d += e.Capacitor().at((x, 0.2)).down().length(2.2)
    d += T(x - 2.3, -0.9, "Cfloor =\nC(6 V)")
    d += e.Line().at((x, 0.2)).to((x + 2.2, 0.2))
    d += e.SourceControlledI().at((x + 2.2, 0.2)).down().length(2.2)
    d += T(x + 2.8, -0.9, "i = (C(v) − Cfloor)\n× i_ref / 1 µF")
    d += e.Line().at((x + 2.2, -2.0)).to((x, -2.0))
    d += e.Ground().at((x, -2.0))
    d += T(x - 2.3, -3.3, "MLCC: C(v) = C0 / (1 + (v / V0)^n);\ni_ref from a 1 µF capacitor\nthat sees a copy of v",
           color=NOTE)
    d.save(str(path), dpi=130)


def i2c(path):
    d = _d()
    d += e.Vdd().label("VLED 4.2 V")
    d += e.Resistor().down().label("R8 3.3k", loc="right")
    d += (n := e.Dot().label("SDA", loc="right"))
    d += e.Capacitor().down().label("Cbus 60-150 pF", loc="right")
    d += e.Ground()
    d += e.Line().at(n.center).left(2.5)
    d += e.Switch().down().label("open-drain\nreleases at 10 µs", loc="left")
    d += e.Ground()
    d.save(str(path), dpi=130)


def make_all() -> dict[str, str]:
    FIG.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, fn in (("sch_power_path", power_path), ("sch_led_path", led_path), ("sch_models", models),
                     ("sch_i2c", i2c)):
        fn(FIG / f"{name}.png")
        out[name] = f"spice/{name}.png"
    return out


if __name__ == "__main__":
    print(make_all())
