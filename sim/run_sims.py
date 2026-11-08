#!/usr/bin/env python3
"""Run every SPICE case for the moon reading light, check the results against their limits, and write the report.

    python3 sim/run_sims.py            # needs ngspice (42 tested), numpy, matplotlib, schemdraw

Outputs: docs/verification/spice-report_main-v<rev>_led-v<rev>_rev<N>.md + .pdf (board revisions from
hardware/*/design.py, report revision REPORT_REV in report.py) + docs/verification/spice/*.png (committed), sim/out/ (netlists as run,
ngspice logs, raw data, results.json, report.html; not committed). Predictions, not evidence: every PROVISIONAL
model value is listed in the report, and the bench measurements in docs/verification/VERIFY.md replace them.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SIM = Path(__file__).resolve().parent
sys.path.insert(0, str(SIM))
import spice  # noqa: E402
import numpy as np  # noqa: E402

# case -> [(variant, label, params, die)]
CASES: dict[str, list[tuple[str, str, dict, str]]] = {
    "model_check": [("base", "datasheet points", {}, "typ")],
    "poweron": [("full", "cell 4.18 V", {"soc0": 1.0}, "typ"),
                ("low", "cell 3.49 V", {"soc0": 0.055}, "typ"),
                ("full_bulk47", "cell 4.18 V, + 47 uF on VSYS", {"soc0": 1.0, "cbulk": "47u"}, "typ")],
    "q4_softstart": [("low", "cell 3.49 V", {"soc0": 0.055}, "typ"),
                     ("full", "cell 4.18 V", {"soc0": 1.0}, "typ"),
                     ("low_vth05", "3.49 V, VGS(th) -0.5 V", {"soc0": 0.055, "vto": -0.5}, "typ"),
                     ("low_vth09", "3.49 V, VGS(th) -0.9 V", {"soc0": 0.055, "vto": -0.9}, "typ")],
    "j3_hotplug": [("full", "cell 4.18 V", {"soc0": 1.0}, "typ"),
                   ("low", "cell 3.49 V", {"soc0": 0.055}, "typ"),
                   ("low_bulk47", "cell 3.49 V, + 47 uF on VSYS", {"soc0": 0.055, "cbulk": "47u"}, "typ")],
    "usb_hotplug": [("r01", "5.25 V, cable 0.1 Ohm", {"rusb": 0.1}, "typ"),
                    ("r03", "5.25 V, cable 0.3 Ohm", {"rusb": 0.3}, "typ"),
                    ("lm_r01", "5.25 V, 0.1 Ohm, LM66100 (re-plug while it is on)", {"rusb": 0.1, "q1gd": 4},
                     "typ"),
                    ("dual_r01", "5.25 V, 0.1 Ohm, ideal diodes for Q1 and D3", {"rusb": 0.1, "q1gd": 3, "vdet": 3.9,
                                                                               "usbid": 1}, "typ")],
    "usb_unplug": [("r5_10k", "R5 10k (as built)", {"r5": "10k"}, "typ"),
                   ("r5_4k7", "R5 4.7k (E12 remedy)", {"r5": "4.7k"}, "typ"),
                   ("r5_1k", "R5 1k", {"r5": "1k"}, "typ"),
                   # handover redesign options (not on the v0.1 board): see the D1 decision
                   ("gd", "gate diode + 100k pull-down", {"q1gd": 1}, "typ"),
                   ("sch", "Schottky across Q1", {"sch": 1}, "typ"),
                   ("det43", "4.3 V detector drives Q1's gate", {"q1gd": 2}, "typ"),
                   ("idd", "ideal diode replaces Q1", {"q1gd": 3, "vdet": 3.9}, "typ"),
                   ("dual", "ideal diodes for Q1 and D3", {"q1gd": 3, "vdet": 3.9, "usbid": 1}, "typ"),
                   ("lm", "LM66100, CE on VBUS, R5 10k", {"q1gd": 4}, "typ"),
                   ("lm_r5_4k7", "LM66100, CE on VBUS, R5 4.7k", {"q1gd": 4, "r5": "4.7k"}, "typ"),
                   ("lm_r5_1k", "LM66100, CE on VBUS, R5 1k", {"q1gd": 4, "r5": "1k"}, "typ")],
    "charge": [("lamp", "4000 K full on, USB 5.0 V", {"lamp": 1}, "typ"),
               ("dark", "lamp off, USB 5.0 V", {"lamp": 0}, "typ"),
               ("lamp_weak", "lamp on, USB 4.75 V, PTC 0.2 Ohm (cold max)", {"lamp": 1, "vusb": 4.75, "rptc": 0.2}, "typ"),
               # source-voltage sweep (D3) and the handover options on a weak source (D1)
               ("v45", "lamp on, USB 4.5 V", {"lamp": 1, "vusb": 4.5, "rptc": 0.2}, "typ"),
               ("v44", "lamp on, USB 4.4 V", {"lamp": 1, "vusb": 4.4, "rptc": 0.2}, "typ"),
               ("v44_dark", "lamp off, USB 4.4 V", {"lamp": 0, "vusb": 4.4, "rptc": 0.2}, "typ"),
               ("weak_sch", "4.75 V, Schottky across Q1", {"lamp": 1, "vusb": 4.75, "rptc": 0.2, "sch": 1}, "typ"),
               ("weak_det43", "4.75 V, 4.3 V detector", {"lamp": 1, "vusb": 4.75, "rptc": 0.2, "q1gd": 2}, "typ"),
               ("weak_idd", "4.75 V, ideal diode", {"lamp": 1, "vusb": 4.75, "rptc": 0.2, "q1gd": 3, "vdet": 3.9}, "typ"),
               ("v44_idd", "4.4 V, ideal diode", {"lamp": 1, "vusb": 4.4, "rptc": 0.2, "q1gd": 3, "vdet": 3.9}, "typ"),
               ("v44_idd435", "4.4 V, ideal diode enabled below 4.35 V", {"lamp": 1, "vusb": 4.4, "rptc": 0.2, "q1gd": 3}, "typ"),
               ("lm_weak", "4.75 V, LM66100", {"lamp": 1, "vusb": 4.75, "rptc": 0.2, "q1gd": 4}, "typ"),
               ("lm_44", "4.4 V, LM66100", {"lamp": 1, "vusb": 4.4, "rptc": 0.2, "q1gd": 4}, "typ"),
               ("dual_5", "5.0 V, ideal diodes for Q1 and D3", {"lamp": 1, "q1gd": 3, "vdet": 3.9, "usbid": 1}, "typ"),
               ("dual_44", "4.4 V, ideal diodes for Q1 and D3", {"lamp": 1, "vusb": 4.4, "rptc": 0.2, "q1gd": 3,
                                                                  "vdet": 3.9, "usbid": 1}, "typ")],
    "runtime": [("4000k", "4000 K full", {"dwv": 0.8875, "drv": 0, "iqv": "6.8m", "tstop": 30000, "tmax": 20}, "typ"),
                ("soft10", "soft white level 10", {"dwv": 0.095, "drv": 0, "iqv": "6.8m", "tstop": 250000,
                                                   "tmax": 60}, "typ"),
                ("night", "red night level 4", {"dwv": 0, "drv": 0.016, "iqv": "6.8m", "tstop": 700000,
                                               "tmax": 120}, "typ"),
                ("night_lo", "red night, electronics 7 mA", {"dwv": 0, "drv": 0.016, "iqv": "4.3m",
                                                             "tstop": 700000, "tmax": 120}, "typ"),
                ("night_hi", "red night, electronics 12 mA", {"dwv": 0, "drv": 0.016, "iqv": "9.3m",
                                                              "tstop": 700000, "tmax": 120}, "typ")],
    "headroom": [("white_typ", "8 whites, typical dies, VSAT 0.30 V", {"dwv": 1, "dgv": 0, "vsat": 0.30}, "typ"),
                 ("white_max", "8 whites, max-VF dies, VSAT 0.45 V", {"dwv": 1, "dgv": 0, "vsat": 0.45}, "max"),
                 ("green_typ", "Green mode, typical die, VSAT 0.30 V", {"dwv": 0, "dgv": 1, "vsat": 0.30}, "typ"),
                 ("green_max", "Green mode, max-VF die, VSAT 0.45 V", {"dwv": 0, "dgv": 1, "vsat": 0.45}, "max")],
    "pwm_ripple": [("d50", "50 % duty", {"duty": 0.5}, "typ"),
                   ("d89", "88.75 % duty (4000 K full)", {"duty": 0.8875}, "typ")],
    "i2c_rise": [("c60", "60 pF", {"cbus": "60p"}, "typ"), ("c100", "100 pF", {"cbus": "100p"}, "typ"),
                 ("c150", "150 pF", {"cbus": "150p"}, "typ")],
}


def run_all() -> dict:
    jobs = [(c, v, lab, p, die) for c, vs in CASES.items() for (v, lab, p, die) in vs]

    def one(j):
        c, v, lab, p, die = j
        return (c, v, lab), spice.run(c, v, p, die)

    with ThreadPoolExecutor(max_workers=8) as ex:
        res = dict(ex.map(one, jobs))
    R = {(c, v): (lab, r) for (c, v, lab), r in res.items()}
    derive(R)
    return R


def derive(R):
    """Threshold-crossing times, computed from the waveforms (a .meas WHEN inside .control does not evaluate
    {param} expressions, so levels are set here from the measured final value)."""
    for (c, v), (_, r) in R.items():
        if c == "poweron":
            y, fin = r.col("v(vsys)"), r.meas["vsys_end"]
            r.meas["t10"], r.meas["t90"] = (spice.cross(r.x, y, k * fin, 1e-3) for k in (0.1, 0.9))
        elif c == "q4_softstart":
            y, fin = r.col("v(vledb)"), r.meas["vled_end"]
            r.meas["t10"], r.meas["t90"] = (spice.cross(r.x, y, k * fin, 1e-3) for k in (0.1, 0.9))
        elif c == "usb_unplug":
            t, y, i = r.x, r.col("v(vsys)"), r.col("iled")
            after = t > 5e-3
            deep = after & (y < r.meas["vsys_bat"] - 0.3)
            dim = after & (i < 0.9 * r.meas["iled_usb"])
            r.meas["dip"] = r.meas["vsys_bat"] - r.meas["vsys_min"]
            r.meas["vbus_usb"] = float(np.interp(4.9e-3, t, r.col("v(vbus)")))
            r.meas["iled_max_after"] = float(i[after].max())
            r.meas["t_deep_ms"] = float(np.ptp(t[deep]) * 1e3) if deep.any() else 0.0
            r.meas["t_dim_ms"] = float(np.ptp(t[dim]) * 1e3) if dim.any() else 0.0
        elif c == "usb_hotplug":
            t, ic = r.x, r.col("icell_in")
            hi = (t > 100e-6) & (ic > 0.3)
            r.meas["t_icell_hi_us"] = float(np.ptp(t[hi]) * 1e6) if hi.any() else 0.0
        elif c == "charge":
            t, v, iu = r.x, r.col("v(vsys)"), r.col("iusb")
            r.meas["h_below_345"] = float(np.ptp(t[v < 3.45]) / 3600) if (v < 3.45).any() else 0.0
            r.meas["n_usb_over_05"] = float((iu > 0.5).sum())
            r.meas["ichg_4h"] = float(np.interp(4 * 3600, t, r.col("ichg")))
        elif c == "i2c_rise":
            y = r.col("v(sda)")
            r.meas["t30"], r.meas["t70"] = (spice.cross(r.x, y, k * 4.2, 10e-6) for k in (0.3, 0.7))
            rc = 3.3e3 * {"c60": 60e-12, "c100": 100e-12, "c150": 150e-12}[v]
            tr = r.meas["t70"] - r.meas["t30"]
            # sanity bound: an RC edge has tr(30-70 %) = ln(7/3) RC = 0.847 RC
            assert abs(tr / (0.847 * rc) - 1) < 0.05, f"i2c {v}: tr {tr} vs 0.847RC {0.847 * rc}"


# --------------------------------------------------------------------------------------------- checks
def verdict(ok: bool, margin_ok: bool = True) -> str:
    return "PASS" if ok and margin_ok else ("MARGINAL" if ok else "FAIL")


def checks(R) -> list[dict]:
    m = lambda c, v: R[(c, v)][1].meas  # noqa: E731
    out = []

    def add(cid, area, what, value, limit, v, source, note=""):
        out.append(dict(id=cid, area=area, what=what, value=value, limit=limit, verdict=v, source=source, note=note))

    # power-on
    for v in ("full", "low", "full_bulk47"):
        p = m("poweron", v)
        add(f"P1-{v}", "Power-on (SW1)", f"Cell inrush peak, {R[('poweron', v)][0]}", f"{p['ipk']:.2f} A",
            "< ~3 A (typical DW01-class PCM over-current trip, PROVISIONAL); Q2 IDM 15 A",
            verdict(p["ipk"] < 3.0, p["ipk"] < 2.0), "KEYSPECS DMG2305UX; cell PCM not documented",
            "Round 1 note predicted 0.7-1.3 A into 14-21 uF; now ~8 uF nominal on VSYS")
    p = m("poweron", "full")
    add("P2", "Power-on (SW1)", "VSYS rise 10-90 % and overshoot", f"{(p['t90'] - p['t10']) * 1e6:.0f} us, "
        f"overshoot {max(0, p['vsys_max'] - p['vsys_end']) * 1e3:.0f} mV", "monotonic, no overshoot",
        verdict(p["vsys_max"] - p["vsys_end"] < 0.05), "design intent (electronics.md 1)",
        "C5 sits gate-source, so the edge is set by the FET threshold, not a Miller ramp")
    # Q4
    q = m("q4_softstart", "low")
    rise = (q["t90"] - q["t10"]) * 1e3
    add("Q1", "Q4 soft turn-on", "VLED ramp at the LED board (10-90 %), cell 3.49 V", f"{rise:.2f} ms, "
        f"{q['dvdt_max'] / 1e3:.2f} V/ms max", "ramps over ~1-2 ms (E13); 2.5 V/ms design", verdict(0.8 <= rise <= 2.5),
        "VERIFY E13; electronics.md 1")
    worst = min(m("q4_softstart", v)["vsys_min"] - m("q4_softstart", v)["vsys0"] for v in
                ("low", "full", "low_vth05", "low_vth09"))
    add("Q2", "Q4 soft turn-on", "VSYS dip, worst of 4 corners", f"{-worst * 1e3:.0f} mV", "<= 200 mV (E13)",
        verdict(-worst <= 0.2), "VERIFY E13")
    ipk = max(m("q4_softstart", v)["ipk"] for v in ("low", "full", "low_vth05", "low_vth09"))
    add("Q3", "Q4 soft turn-on", "Peak LED-board charging current, worst corner", f"{ipk * 1e3:.0f} mA",
        "design note says 15-25 mA", "INFO", "electronics.md 1",
        "Higher than the note: at low bias the MLCCs are near their 11 uF nominal, not the ~4-6 uF biased value")
    # J3 hot-plug
    for v in ("full", "low", "low_bulk47"):
        j = m("j3_hotplug", v)
        add(f"J1-{v}", "J3 hot-plug", f"VSYS minimum, {R[('j3_hotplug', v)][0]}", f"{j['vsys_min']:.2f} V",
            "> 2.6 V (ATtiny BOD level, fuses: bod = 2.6v)", verdict(j["vsys_min"] > 2.6, j["vsys_min"] > 2.8),
            "VERIFY E13; firmware/platformio.ini", "Not a user action: the cable is inside the gooseneck")
    j = m("j3_hotplug", "full")
    add("J2", "J3 hot-plug", "Peak cable current / LED-board peak voltage", f"{j['ipk']:.1f} A / {j['vledb_max']:.2f} V",
        "LED board <= 6 V abs max (LP5012, MCP9800)", verdict(j["vledb_max"] < 6.0), "KEYSPECS LP5012",
        "~1.5 us wide spike; JST-SH contacts are rated 1 A continuous")
    # USB hot-plug
    for v in ("r01", "r03"):
        u = m("usb_hotplug", v)
        add(f"U1-{v}", "USB plug-in", f"VBUS peak, {R[('usb_hotplug', v)][0]}", f"{u['vbus_max']:.2f} V",
            "< 7.0 V (MCP73831 abs max); TVS VBR 6.4 V min", verdict(u["vbus_max"] < 7.0, u["vbus_max"] < 6.4),
            "KEYSPECS MCP73831; SMF5.0A")
        add(f"U2-{v}", "USB plug-in", f"VSYS / LED-board peak, {R[('usb_hotplug', v)][0]}",
            f"{u['vsys_max']:.2f} / {u['vledb_max']:.2f} V", "< 6.0 V (ATtiny3216, LP5012 abs max)",
            verdict(max(u["vsys_max"], u["vledb_max"]) < 6.0, max(u["vsys_max"], u["vledb_max"]) < 5.5),
            "KEYSPECS")
    u = m("usb_hotplug", "r01")
    add("U3", "USB plug-in", "Attach inrush peak from the charger", f"{u['iusb_pk']:.1f} A", "USB 2.0: <= 10 uF at "
        "attach without inrush limiting", "INFO", "USB 2.0 spec 7.2.4.1",
        "C1 is 10 uF nominal; D3 also charges C3/C4 when VSYS_RAW < VBUS - 0.85 V")
    # USB unplug
    for v in ("r5_10k", "r5_4k7", "r5_1k"):
        h = m("usb_unplug", v)
        dip = h["vsys_bat"] - h["vsys_min"]
        dur = (h.get("t_over", 0.005) - 0.005) * 1e3
        add(f"H1-{v}", "USB unplug", f"VSYS dip below battery level, {R[('usb_unplug', v)][0]}",
            f"{dip:.2f} V for {max(dur, 0):.0f} ms (>0.3 V); min {h['vsys_min']:.2f} V",
            "<= 0.3 V, no reset (E12); BOD 2.6 V", verdict(dip <= 0.3) if h["vsys_min"] > 2.6 else "FAIL",
            "VERIFY E12", "The dip is Q1's body diode carrying the load until R5 discharges VBUS")
    h = m("usb_unplug", "r5_10k")
    add("H2", "USB unplug", "LED current during the handover (4000 K full)",
        f"{h['iled_usb'] * 1e3:.0f} mA -> {h['iled_min'] * 1e3:.0f} mA", "no visible step (no spec)", "INFO",
        "", "A brief dimming at unplug; the whites need ~3.1 V at the board")
    # charge
    c = m("charge", "lamp")
    add("C1", "Charge + load share", "Charger terminates with the lamp on (R18)",
        f"I_bat falls to 31 mA at {c['t_term'] / 3600:.2f} h; Q1 body diode max {c['vq1_max']:.2f} V forward",
        "termination reached; Q1 body diode < 0.4 V (not conducting)", verdict(c["vq1_max"] < 0.4 and c["t_term"] > 0),
        "PLAN R18; KEYSPECS MCP73831")
    cw = m("charge", "lamp_weak")
    add("C2", "Charge + load share", "Same, weak USB (4.75 V, PTC 0.2 Ohm cold max, cable 0.2 Ohm)",
        f"Q1 body diode {cw['vq1_max']:.2f} V forward, {cw['idq1_max'] * 1e3:.2f} mA from the cell into VSYS; "
        f"terminates at {cw['t_term'] / 3600:.2f} h", "body-diode current < 3.1 mA (10 % of the 31 mA termination)",
        verdict(cw["idq1_max"] < 3.1e-3, cw["idq1_max"] < 1e-3), "PLAN R18",
        "The charger would see the cell current minus this leak; termination still happens")
    add("C3", "Charge + load share", "Peak USB current, charging + 4000 K full", f"{c['iusb_max']:.3f} A",
        "<= ~0.8 A (F1 hold at 60 C); E11 expects 0.5-0.6 A", verdict(c["iusb_max"] < 0.8, c["iusb_max"] < 0.65),
        "VERIFY E11, E14; electronics.md 1")
    add("C4", "Charge + load share", "VSYS on USB (minimum over the charge)",
        f"{c['vsys_min']:.2f} V (5.0 V USB); {cw['vsys_min']:.2f} V (4.75 V, PTC 0.2 Ohm)"
        " (both with a 0.2 Ohm cable)", ">= 3.9 V (E15)",
        verdict(c["vsys_min"] >= 3.9, cw["vsys_min"] >= 3.9), "VERIFY E15")
    add("C5", "Charge + load share", "MCP73831 dissipation, peak", f"{max(c['pchg_max'], cw['pchg_max']):.2f} W",
        "<= 0.69 W design worst case (thermal regulation above)", verdict(max(c['pchg_max'], cw['pchg_max']) <= 0.69),
        "electronics.md 1")
    # runtime
    est = {"4000k": (6.5, 6.5), "soft10": (45, 45), "night": (100, 150)}
    for v in ("4000k", "soft10", "night"):
        r = m("runtime", v)
        hrs = r["t_empty"] / 3600
        lo, hi = est[v]
        add(f"R1-{v}", "Runtime", f"Battery life, {R[('runtime', v)][0]}", f"{hrs:.1f} h to the empty cut "
            f"({r['wh'] / 3600:.2f} Wh delivered; brightness cap after {r['t_low'] / 3600:.1f} h)",
            f"estimate {lo:g}{'' if lo == hi else f'-{hi:g}'} h (electronics.md 3)",
            "INFO", "electronics.md 3", "OCV curve and cell resistance PROVISIONAL; derating not modelled")
    # headroom
    w = m("headroom", "white_typ")
    wm = m("headroom", "white_max")
    add("D1", "LED headroom", "Whites stay regulated down to the low-battery cut (8 on together)",
        f"95 % point at VSYS {w['vsys_w95']:.2f} V / cell OCV {w['ocv_w95']:.2f} V (typ); VSYS {wm['vsys_w95']:.2f} V"
        f" / OCV {wm['ocv_w95']:.2f} V (max-VF dies, VSAT 0.45 V)",
        "VSYS edge < 3.45 V (VBAT_LOW is measured on VSYS under load)",
        verdict(wm["vsys_w95"] < 3.45, wm["vsys_w95"] < 3.35),
        "electronics.md 2")
    g = m("headroom", "green_typ")
    gm = m("headroom", "green_max")
    gtyp = g.get("vledb_g95", float("nan"))
    gmax = gm.get("vledb_g95", float("nan"))
    add("D2", "LED headroom", "Green/blue regulation edge (VLED at the board)",
        f"typ die {gtyp:.2f} V; max-VF die {gmax:.2f} V" if not math.isnan(gmax) else
        f"typ die {gtyp:.2f} V; max-VF die never regulated (< 95 % at 4.3 V)",
        "design: ~3.65 V typ, ~4.05-4.15 V max die (round3 R3-E3)", "INFO", "electronics.md 2; VERIFY E9")
    # PWM ripple
    for v in ("d50", "d89"):
        p = m("pwm_ripple", v)
        add(f"W1-{v}", "PWM ripple", f"Ripple, all whites in phase, {R[('pwm_ripple', v)][0]}",
            f"VLED {1e3 * (p['vledb_max'] - p['vledb_min']):.0f} mV p-p (min {p['vledb_min']:.2f} V); "
            f"VSYS {1e3 * (p['vsys_max'] - p['vsys_min']):.0f} mV p-p",
            "LP5012 VCC >= 2.7 V; VSYS > 2.6 V", verdict(p["vledb_min"] > 2.7 and p["vsys_min"] > 2.6), "KEYSPECS LP5012")
    # I2C
    for v in ("c60", "c100", "c150"):
        i = m("i2c_rise", v)
        tr = (i["t70"] - i["t30"]) * 1e9
        add(f"I1-{v}", "I2C", f"Rise time 30-70 %, {R[('i2c_rise', v)][0]}", f"{tr:.0f} ns",
            "<= 1000 ns (standard mode, 100 kHz)", verdict(tr <= 1000, tr <= 300), "I2C spec; electronics.md 4")
    return out


MODEL_POINTS = [  # (meas, what, datasheet value, source)
    ("rds45", "DMG2305UX R_DS(on) @ VGS -4.5 V (Ohm)", "0.040 typ / 0.052 max", "KEYSPECS"),
    ("rds25", "DMG2305UX R_DS(on) @ VGS -2.5 V (Ohm)", "0.052 typ / 0.100 max", "KEYSPECS"),
    ("vsd", "DMG2305UX body diode @ 0.1 A (V)", "~0.65 (PROVISIONAL)", "typical silicon"),
    ("vw10", "Thrive 2835 white VF @ 10 mA (V)", "~2.70", "DS312 Fig. 9"),
    ("vw25", "Thrive 2835 white VF @ 25 mA (V)", "~2.75", "DS312 Fig. 9"),
    ("vw50", "Thrive 2835 white VF @ 50 mA (V)", "~2.85", "DS312 Fig. 9"),
    ("vwm25", "Thrive white max-VF die @ 25 mA (V)", "~2.92", "electronics.md 2"),
    ("vr20", "Wurth red VF @ 20 mA (V)", "2.0 typ", "Wurth p2"),
    ("vrm20", "Wurth red max die @ 20 mA (V)", "2.4 max", "Wurth p2"),
    ("vg20", "Wurth green/blue VF @ 20 mA (V)", "3.2 typ", "Wurth p2"),
    ("vgm20", "Wurth green/blue max die @ 20 mA (V)", "3.6 max", "Wurth p2"),
    ("vg25d", "Wurth G/B VF rise 20 -> 25 mA (V)", "~+0.09", "Wurth p3"),
    ("vs1j02", "S1J VF @ 0.2 A (V)", "~0.85", "PLAN / Vishay curve"),
    ("vs1j1", "S1J VF @ 1 A (V)", "~0.95 typ (1.1 max)", "Vishay"),
    ("isat", "LP5012 sink current at VSAT (fraction of ISET)", "0.95 (definition of VSAT)", "SLVSEH2B"),
]


def main() -> int:
    ver = subprocess.run(["ngspice", "-v"], capture_output=True, text=True).stdout
    ver = next((ln.strip("* ").split(":")[0].strip() for ln in ver.splitlines() if "ngspice-" in ln), "ngspice")
    R = run_all()
    bad = {k: r.errors for k, (_, r) in R.items() if any("trouble" in e or "aborted" in e for e in r.errors)}
    if bad:
        for k, e in bad.items():
            print("SIMULATION FAILED", k, e[:3])
        return 1
    ch = checks(R)
    (spice.OUT / "results.json").write_text(json.dumps(
        {"ngspice": ver, "results": {f"{c}/{v}": {"label": lab, "meas": r.meas} for (c, v), (lab, r) in R.items()},
         "checks": ch}, indent=1))
    import plots
    import report
    import schematics
    figs = plots.make_all(R)
    sch = schematics.make_all()
    report.write(R, ch, figs, sch, MODEL_POINTS, CASES, ver)
    n = {k: sum(c["verdict"] == k for c in ch) for k in ("PASS", "MARGINAL", "FAIL", "INFO")}
    print(f"{len(R)} runs, {len(ch)} checks: " + ", ".join(f"{v} {k}" for k, v in n.items()))
    for c in ch:
        if c["verdict"] in ("FAIL", "MARGINAL"):
            print(f"  {c['verdict']:8} {c['id']:10} {c['what']}: {c['value']} (limit {c['limit']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
