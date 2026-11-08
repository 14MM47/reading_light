"""Write the SPICE report: docs/verification/spice-report.md (committed) and sim/out/report.html (self-contained)."""
from __future__ import annotations

import base64
import datetime as dt
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "verification"
OUT = Path(__file__).resolve().parent / "out"
BADGE = {"PASS": "pass", "MARGINAL": "marg", "FAIL": "fail", "INFO": "info"}


def board_revs() -> dict[str, str]:
    """REV from each board's design.py (the source of truth; also in the KiCad title block and fab/<board>/v<rev>)."""
    out = {}
    for b in ("main-board", "led-board"):
        mo = re.search(r'^REV = "([^"]+)"', (ROOT / "hardware" / b / "design.py").read_text(), re.M)
        if not mo:
            raise SystemExit(f"no REV in hardware/{b}/design.py")
        out[b] = mo.group(1)
    return out


def report_stem() -> str:
    r = board_revs()
    return f"spice-report_main-v{r['main-board']}_led-v{r['led-board']}"


def kicad_refs() -> dict[str, str]:
    """Export the real board schematics (reference appendix). Optional: needs kicad-cli + pdftoppm."""
    out: dict[str, str] = {}
    if not (shutil.which("kicad-cli") and shutil.which("pdftoppm")):
        return out
    for b in ("main-board", "led-board"):
        pdf = OUT / f"{b}.pdf"
        subprocess.run(["kicad-cli", "sch", "export", "pdf", "-o", str(pdf),
                        str(ROOT / "hardware" / b / f"{b}.kicad_sch")], capture_output=True)
        if pdf.exists():
            subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile", str(pdf),
                            str(DOCS / "spice" / f"kicad_{b}")], capture_output=True)
            out[b] = f"spice/kicad_{b}.png"
    return out


def write(R, checks, figs, sch, model_points, cases, ngspice_ver):
    m = lambda c, v: R[(c, v)][1].meas  # noqa: E731
    kic = kicad_refs()
    n = {k: sum(c["verdict"] == k for c in checks) for k in ("PASS", "MARGINAL", "FAIL", "INFO")}
    today = dt.date.today().isoformat()
    po, pol, pob = m("poweron", "full"), m("poweron", "low"), m("poweron", "full_bulk47")
    q4l = m("q4_softstart", "low")
    j3f, j3l, j3b = m("j3_hotplug", "full"), m("j3_hotplug", "low"), m("j3_hotplug", "low_bulk47")
    u1, u3 = m("usb_hotplug", "r01"), m("usb_hotplug", "r03")
    h10, h47, h1 = m("usb_unplug", "r5_10k"), m("usb_unplug", "r5_4k7"), m("usb_unplug", "r5_1k")
    dip = h10["vsys_bat"] - h10["vsys_min"]
    dur = lambda h: (h["t_over"] - 0.005) * 1e3  # noqa: E731
    ch, chd, chw = m("charge", "lamp"), m("charge", "dark"), m("charge", "lamp_weak")
    rt = {v: m("runtime", v) for v in ("4000k", "soft10", "night", "night_lo", "night_hi")}
    hw, hwm, hg, hgm = (m("headroom", v) for v in ("white_typ", "white_max", "green_typ", "green_max"))
    w50 = m("pwm_ripple", "d50")
    tr = {v: (m("i2c_rise", v)["t70"] - m("i2c_rise", v)["t30"]) * 1e9 for v in ("c60", "c100", "c150")}
    h = lambda s: s / 3600  # noqa: E731
    nruns = len(R)

    L = []
    a = L.append
    revs = board_revs()
    vtag = f"main board v{revs['main-board']} · LED board v{revs['led-board']}"
    a(f"# SPICE simulation report: moon reading light ({vtag})")
    a("")
    a(f"**Board versions:** main board **v{revs['main-board']}**, LED board **v{revs['led-board']}** (`REV` in "
      f"`hardware/*/design.py`, the KiCad title blocks and `fab/<board>/v<rev>/`). Report file: `{report_stem()}`.")
    a("")
    a(f"Generated {today} by `python3 sim/run_sims.py` "
      f"({ngspice_ver}, {nruns} runs over {len(cases) - 1} circuits plus a model check). **These are predictions, not "
      "evidence**: every value nobody has measured is listed under *Assumptions* with the VERIFY item that replaces it.")
    a("")
    a("## Summary")
    a("")
    a(f"**{n['PASS']} pass, {n['MARGINAL']} marginal, {n['FAIL']} fail, {n['INFO']} for information** "
      f"({len(checks)} checks against datasheet limits and the pass criteria in `docs/verification/VERIFY.md`). "
      "The FAIL rows are two issues: the USB-unplug dip (as built, plus the two R5 values tried as remedies) and "
      "the J3 hot-plug at a low battery.")
    a("")
    a("What needs a decision:")
    a("")
    a(f"1. **USB unplug dips VSYS by {dip:.2f} V for about {dur(h10):.0f} ms** (VERIFY E12 allows 0.3 V). Q1's body "
      f"diode carries the lamp until R5 has pulled VBUS down far enough to turn Q1's channel on. The MCU stays up "
      f"(minimum {h10['vsys_min']:.2f} V against the 2.6 V BOD), but the LED-board current drops from "
      f"{h10['iled_usb'] * 1e3:.0f} mA to about 130 mA for that time, which may show as a blink. E12's own remedy "
      f"(R5 4.7k) only shortens it ({dur(h47):.0f} ms; {dur(h1):.1f} ms with 1k): the depth is the body diode's "
      "drop and no R5 value changes it. Options: accept and re-word E12 to \"no reset\"; R5 1k (costs 5 mA from USB "
      "while plugged in); or drive Q1's gate actively in the next revision.")
    a(f"2. **Hot-plugging the LED-board cable resets the MCU at a low battery** (VSYS falls to {j3l['vsys_min']:.2f} V "
      f"at 3.49 V; {j3f['vsys_min']:.2f} V on a full cell, just above the 2.6 V BOD). The cable is inside the gooseneck, "
      f"so this is a bench situation, but VERIFY E13 asks for it. E13's remedy (47 µF on VSYS) brings the low-battery "
      f"case to {j3b['vsys_min']:.2f} V and raises the power-on inrush from {po['ipk']:.2f} A to {pob['ipk']:.2f} A. "
      "Simplest: drop the hot-plug step from E13 (plug J3 with the switch off).")
    a(f"3. **On a weak USB source VSYS falls below E15's 3.9 V**: {chw['vsys_min']:.2f} V at 4.75 V USB through a "
      f"0.2 Ω cable with F1 at its 0.2 Ω maximum (about 3.80 V without the cable). Q1's body diode then sees {chw['vq1_max']:.2f} V forward and leaks "
      f"{chw['idq1_max'] * 1e3:.1f} mA from the cell, too little to upset the charge termination. At 5.0 V "
      f"VSYS is {ch['vsys_min']:.2f} V. E15 should name the source voltage (5.0 V nominal).")
    a("")
    a("What the simulation confirms:")
    a("")
    a(f"- Q4's soft turn-on works as designed: VLED ramps 10-90 % in {(q4l['t90'] - q4l['t10']) * 1e3:.1f} ms at "
      f"{q4l['dvdt_max'] / 1e3:.1f} V/ms, and VSYS moves by {1e3 * (q4l['vsys0'] - q4l['vsys_min']):.0f} mV.")
    a(f"- Power-on through Q2 draws {po['ipk']:.2f} A peak from a full cell ({pol['ipk']:.2f} A at 3.49 V), with no "
      "overshoot on VSYS.")
    a(f"- Plugging USB in peaks at {u1['vbus_max']:.2f} V on VBUS and {u1['vsys_max']:.2f} V on VSYS (abs max 7 V / "
      "6 V), even with a short, low-resistance cable.")
    a(f"- Load sharing (R18): with the lamp on, the cell still charges at 256 mA and tapers to the 31 mA termination "
      f"after {h(ch['t_term']):.1f} h; USB draw peaks at {ch['iusb_max']:.2f} A.")
    a(f"- Battery life to the firmware's empty cut: {h(rt['4000k']['t_empty']):.1f} h at 4000 K full, "
      f"{h(rt['soft10']['t_empty']):.0f} h at soft white level 10, {h(rt['night']['t_empty']):.0f} h in red night "
      f"light ({h(rt['night_hi']['t_empty']):.0f}-{h(rt['night_lo']['t_empty']):.0f} h for 12-7 mA of electronics). "
      "Close to the estimates in `docs/design/electronics.md` §3 (6.5 h, 45 h, 100-150 h).")
    a(f"- The whites stay regulated down to VSYS {hw['vsys_w95']:.2f} V (typical dies) and {hwm['vsys_w95']:.2f} V "
      f"(max-VF dies with the worst VSAT), below the 3.45 V low-battery cap. Green/blue need {hg['vledb_g95']:.2f} V "
      f"(typical) and {hgm['vledb_g95']:.2f} V (max die) at the board, matching the round-3 figures.")
    a("")
    decisions(a, dict(h10=h10, h47=h47, h1=h1, dur=dur, dip=dip, j3l=j3l, j3f=j3f, j3b=j3b, po=po, pob=pob,
                      ch=ch, chw=chw, hw=hw, hwm=hwm, tr=tr, q4max=max(m("q4_softstart", v)["ipk"] for v in
                                                                       ("low", "full", "low_vth05", "low_vth09"))),
              revs)
    a("## All checks")
    a("")
    a("| ID | Area | Check | Simulated | Limit | Verdict |")
    a("|---|---|---|---|---|---|")
    for c in checks:
        a(f"| {c['id']} | {c['area']} | {c['what']} | {c['value']} | {c['limit']} | **{c['verdict']}** |")
    a("")
    a("MARGINAL means inside the limit with less margin than this report's own rule of thumb (stated per check in "
      "`sim/run_sims.py`). INFO rows have no hard limit.")
    a("")
    a("## The circuits as simulated")
    a("")
    a("SPICE subcircuits in `sim/boards.inc` follow the reference designators of the two boards. Device models are "
      "in `sim/models.inc`; each is fitted to datasheet points (checked in the *Model check* table below).")
    a("")
    a(f"![Main-board power path as simulated]({sch['sch_power_path']})")
    a("")
    a("*Main-board power path: cell model, reverse-battery FET Q3, load-share FET Q1 (gate on VBUS), D3 from USB, "
      "the slide-switch FET Q2 with its R7/C5 soft start, and the VSYS loads. The charger is a behavioural CC/CV "
      "source.*")
    a("")
    a(f"![LED-board path as simulated]({sch['sch_led_path']})")
    a("")
    a("*Q4 with its Miller soft start (R13 into C8), the neck cable (both conductors), and the LED board: bulk and "
      "bypass MLCCs, LP5012 supply current, and the LED channels as LED + LP5012 sink.*")
    a("")
    a(f"![Behavioural models]({sch['sch_models']})")
    a("")
    a("*Behavioural models: the cell (open-circuit voltage from the state of charge), one LP5012 channel, and the "
      "bias-dependent MLCC.*")
    a("")

    def case(title, fig, body):
        a(f"## {title}")
        a("")
        for p in body:
            a(p)
            a("")
        a(f"![{title}]({fig})")
        a("")

    case("1. Power-on inrush (slide switch, Q2)", figs["poweron"], [
        "SW1 pulls Q2's gate down through R7 10k; C5 (100 nF) sits gate-to-source, so the gate voltage falls with a "
        "1 ms time constant and Q2 turns on hard once it passes its threshold. The VSYS capacitors (C4 10 µF, C7 1 µF, "
        "C6 100 nF; about 7 µF at 4 V) then charge through the cell, Q3, Q1 and Q2.",
        f"Peak cell current {po['ipk']:.2f} A (full cell) and {pol['ipk']:.2f} A (3.49 V); VSYS rises 10-90 % in "
        f"{(po['t90'] - po['t10']) * 1e6:.0f} µs with no overshoot. Round 1 had predicted 0.7-1.3 A into 14-21 µF; the "
        "LED board now sits behind Q4, so Q2 sees less capacitance. With 47 µF added on VSYS (the E13 remedy) the peak "
        f"rises to {pob['ipk']:.2f} A, still well below the FET's 15 A pulse rating but closer to the cell PCM's "
        "over-current trip (typically ~3 A on DW01-class protectors; not documented for this cell)."])
    case("2. Q4 soft turn-on of the LED board", figs["q4_softstart"], [
        "PB2 drives Q4's gate through R13 10k with C8 100 nF from gate to drain: the Miller plateau holds the gate while "
        "C8 charges, so VLED rises at about (VSYS − |VGS(plateau)|) / (R13 · C8). The LED board is in standby (LEDs "
        "off), so it loads VLED with its MLCCs only. Four corners: cell 3.49 V / 4.18 V and Q4 threshold −0.5 / −0.9 V.",
        f"At 3.49 V (the E13 condition) VLED takes {(q4l['t90'] - q4l['t10']) * 1e3:.2f} ms from 10 to 90 %, peak "
        f"{q4l['dvdt_max'] / 1e3:.2f} V/ms, and the charging current peaks at {q4l['ipk'] * 1e3:.0f} mA "
        f"({max(m('q4_softstart', v)['ipk'] for v in ('low', 'full', 'low_vth05', 'low_vth09')) * 1e3:.0f} mA worst "
        f"corner). VSYS moves by {1e3 * (q4l['vsys0'] - q4l['vsys_min']):.0f} mV. The current is higher than the "
        "design note's 15-25 mA because the MLCCs start at their unbiased value (about 11 µF at 0 V, falling to "
        "about 4.5 µF at 3.5 V); it is still harmless."])
    case("3. Hot-plugging the LED-board cable", figs["j3_hotplug"], [
        "With Q4 on, plugging the cable connects the LED board's empty MLCCs straight to VSYS. The main board has no "
        "bulk capacitance on VLED, so C4 shares its charge with them within about 2 µs; the cell, behind its "
        "resistance and lead inductance, brings VSYS back over the next ~50 µs.",
        f"The cable current peaks at {j3f['ipk']:.0f} A in a pulse about 1.5 µs wide. VSYS falls to "
        f"{j3f['vsys_min']:.2f} V on a full cell and to {j3l['vsys_min']:.2f} V at 3.49 V, below the ATtiny's 2.6 V "
        f"BOD level, so expect a reset. With 47 µF on VSYS the 3.49 V case bottoms at {j3b['vsys_min']:.2f} V. "
        "The BOD's response time to a dip of a few microseconds is not modelled; a short dip may not trip it, so "
        "treat this as the worst case. The LED board never exceeds VSYS (no overshoot)."])
    case("4. Plugging in USB while the lamp runs", figs["usb_hotplug"], [
        "A 5.25 V source (top of the USB tolerance) through a 1 µH cable is connected while the lamp runs at 4000 K "
        "from a 3.74 V cell. The cable rings with C1, and D3 also charges VSYS_RAW/VSYS up from the battery level.",
        f"With a 0.1 Ω cable, VBUS peaks at {u1['vbus_max']:.2f} V (MCP73831 abs max 7 V; the TVS does not conduct) "
        f"and VSYS at {u1['vsys_max']:.2f} V (ATtiny and LP5012 abs max 6 V). With 0.3 Ω the peaks are "
        f"{u3['vbus_max']:.2f} V / {u3['vsys_max']:.2f} V. The charger supplies a {u1['iusb_pk']:.0f} A peak for a few "
        "microseconds; USB 2.0 asks a device to present no more than 10 µF at attach, and C1 is 10 µF nominal, but D3 "
        "adds C3/C4 while VSYS_RAW sits below VBUS − 0.85 V. Most chargers ride through it; no action proposed."])
    case("5. Unplugging USB (handover to the battery)", figs["usb_unplug"], [
        "On USB, VSYS comes through D3 and Q1 is held off because its gate sits on VBUS. When USB is pulled, the lamp "
        "first drains C1 through D3, then Q1's body diode takes the load (cell → VSYS_RAW, about 0.65 V drop). Q1's "
        "channel turns on only when R5 has discharged VBUS below VSYS_RAW − |VGS(th)|. Cell 3.6 V, lamp 4000 K full "
        "(the E12 condition).",
        f"VSYS falls from {h10['vsys_usb']:.2f} V to {h10['vsys_min']:.2f} V, {dip:.2f} V below the "
        f"{h10['vsys_bat']:.2f} V it settles at on the battery, for {dur(h10):.0f} ms with R5 10k. R5 4.7k and 1k "
        f"shorten this to {dur(h47):.0f} ms and {dur(h1):.1f} ms but do not reduce the depth. The MCU stays above its "
        "BOD; the whites lose headroom and the LED-board current drops by about 30 % for that time."])
    case("6. Charging with the lamp on (load sharing)", figs["charge"], [
        "A full charge from an empty cell (3.0 V) on a 5.0 V source, with the lamp at 4000 K full for the whole charge, "
        "with it off, and on a weak source (4.75 V, PTC at its 0.2 Ω maximum); all through a 0.2 Ω USB cable. The MCP73831 model is CC 256 mA / "
        "CV 4.20 V; the 31 mA termination point is read off the cell current.",
        f"The cell current is the same with and without the lamp: the lamp is fed from D3, so the charger sees only "
        f"the cell and reaches its 31 mA termination after {h(ch['t_term']):.1f} h either way (R18). Peak USB current "
        f"{ch['iusb_max']:.2f} A (lamp on) and {chd['iusb_max']:.2f} A (off); charger dissipation peaks at "
        f"{ch['pchg_max']:.2f} W. VSYS stays at {ch['vsys_min']:.2f} V or more on the 5.0 V source but drops to "
        f"{chw['vsys_min']:.2f} V on the weak one."])
    case("7. Battery life per mode", figs["runtime"], [
        "Discharge from full at a fixed mode until VSYS (which the firmware measures under load) falls to 3.30 V. "
        "Below 3.45 V the firmware caps brightness to 35 %, modelled as a latch. LED drive is the average PWM duty "
        "on the LP5012 sinks; electronics are MCU 2.5 mA + LP5012 6.8 mA + MCP9800 0.2 mA. Thermal derating is not "
        "modelled, so the 4000 K figure is an upper bound once the head warms.",
        f"4000 K full: {h(rt['4000k']['t_empty']):.1f} h (brightness cap after {h(rt['4000k']['t_low']):.1f} h; estimate "
        f"6.5 h). Soft white level 10: {h(rt['soft10']['t_empty']):.0f} h (estimate 45 h). Red night level 4: "
        f"{h(rt['night']['t_empty']):.0f} h (estimate 100-150 h; {h(rt['night_hi']['t_empty']):.0f}-"
        f"{h(rt['night_lo']['t_empty']):.0f} h for 12-7 mA of electronics, which dominate at this level). Every mode "
        f"delivers about {rt['4000k']['wh'] / 3600:.2f} Wh before the cut."])
    case("8. LED channel headroom", figs["headroom"], [
        "DC sweep of the cell's open-circuit voltage with 0.2 Ω cell resistance and the full path (Q3, Q1, Q2, Q4, "
        "cable). Left: all eight whites on at once, the instantaneous peak of 4000 K full (200 mA). Right: the Green "
        "mode. Typical dies with VSAT 0.30 V, and maximum-VF dies with VSAT 0.45 V (VSAT at 25 mA is not specified).",
        f"The whites hold 95 % of 25 mA down to VSYS {hw['vsys_w95']:.2f} V (typical) and {hwm['vsys_w95']:.2f} V "
        f"(worst case), so they are regulated wherever the firmware runs at full brightness. Green needs VLED "
        f"{hg['vledb_g95']:.2f} V at the board with a typical die (design note: ~3.65 V) and {hgm['vledb_g95']:.2f} V "
        f"with a maximum-VF die (design note: 4.05-4.15 V). A worst-case die reaches only "
        f"{hgm['ig_37'] * 1e3:.0f} mA at a 3.7 V cell. VERIFY E9 measures the received dies."])
    case("9. PWM ripple at 29 kHz", figs["pwm_ripple"], [
        "All eight whites switching together at the LP5012's 29 kHz, which is the worst case: the datasheet extract "
        "does not say whether the LP5012 staggers its outputs. 50 % duty gives the largest ripple; 88.75 % is 4000 K "
        "full.",
        f"At 50 % duty, VLED at the LP5012 swings {1e3 * (w50['vledb_max'] - w50['vledb_min']):.0f} mV p-p (minimum "
        f"{w50['vledb_min']:.2f} V) and VSYS {1e3 * (w50['vsys_max'] - w50['vsys_min']):.0f} mV p-p. Far from the "
        "LP5012's 2.7 V minimum and the MCU's BOD; the ATtiny's ADC reading of VDD will see this ripple, which the "
        "firmware averages."])
    case("10. I²C rise time", figs["i2c_rise"], [
        "R8/R9 3.3 kΩ to VLED against the bus capacitance (MCU pin, 200 mm cable, LP5012, MCP9800): 60-100 pF "
        "estimated, 150 pF as margin.",
        f"Rise time (30-70 %): {tr['c60']:.0f} / {tr['c100']:.0f} / {tr['c150']:.0f} ns for 60 / 100 / 150 pF, "
        "against 1000 ns for standard mode, where the firmware runs the bus (100 kHz). Fast mode (400 kHz, 300 ns) "
        "would pass at 60 pF only, so the bus should stay at 100 kHz."])
    a(f"![I2C pull-up as simulated]({sch['sch_i2c']})")
    a("")
    a("*I²C test circuit: an open-drain pin releases SDA at 10 µs.*")
    a("")
    a("## Model check")
    a("")
    a("Each device model at the operating points it was fitted to (`sim/cases/model_check.cir`).")
    a("")
    a("| Quantity | Model | Datasheet / design | Source |")
    a("|---|---|---|---|")
    mc = m("model_check", "base")
    for k, what, ds, src in model_points:
        a(f"| {what} | {mc[k]:.3f} | {ds} | {src} |")
    a("")
    a("## Assumptions (PROVISIONAL until measured)")
    a("")
    a("| Value | Used | Replaced by |")
    a("|---|---|---|")
    for row in (
        ("Cell open-circuit voltage vs charge", "generic LiCoO2 pouch curve (3.0-4.18 V)", "a discharge log of the "
         "received cell (bench supply as a load, or F4's run)"),
        ("Cell + PCM resistance", "0.20 Ω; lead 150 nH", "the cell's voltage step at a known load"),
        ("Cell PCM over-current trip", "~3 A (DW01-class)", "the cell supplier's data"),
        ("10 µF 0805 16 V DC bias", "6.3 µF at 4.2 V", "VERIFY E5"),
        ("1 µF 0402 / 0603 DC bias", "0.56 / 0.72 µF at 4.2 V", "manufacturer curves"),
        ("DMG2305UX Crss and body diode", "100 pF; 0.65 V at 0.1 A", "datasheet curves"),
        ("LP5012 VSAT at 25 mA", "0.30 V typ, 0.45 V max", "VERIFY E9"),
        ("LED forward voltage bins", "typical and maximum dies", "VERIFY E9 (received dies)"),
        ("LP5012 + MCP9800 supply", "6.8 mA active, 10 µA standby", "VERIFY E7"),
        ("MCU supply", "2.5 mA", "VERIFY E3"),
        ("Neck cable", "63 mΩ and 75 nH per conductor", "a 4-wire resistance measurement"),
        ("USB cable", "0.1-0.3 Ω, 1 µH", "the charger and cable in use"),
        ("VSYS bulk option", "47 µF, 0.1 Ω ESR", "the part chosen, if any"),
    ):
        a("| " + " | ".join(row) + " |")
    a("")
    a("## Not simulated")
    a("")
    for s in (
        "Thermal behaviour: the firmware's 45-58 °C derating, the MCP9800 thermostat and F1's trip are thermal "
        "(seconds to minutes) and need the T-series bench tests.",
        "The MCP73831's control loop, thermal regulation, precharge timer and termination logic (behavioural CC/CV "
        "only).",
        "The ATtiny's BOD response time and the LP5012's start-up sequence (UVLO only).",
        "ESD on USB-C and the buttons, and the TVS's dynamic resistance beyond its datasheet clamp point.",
        "Whether the LP5012 staggers its PWM edges (the ripple case assumes it does not).",
        "Layout parasitics: copper resistance and inductance on both boards are not included.",
    ):
        a(f"- {s}")
    a("")
    a("## Reproduce")
    a("")
    a("```")
    a("python3 sim/run_sims.py      # ngspice 42, numpy, matplotlib, schemdraw; ~30 s")
    a("```")
    a("")
    a("Netlists as run, ngspice logs and raw waveforms land in `sim/out/<case>/<variant>/`. To test a design change, "
      "edit `sim/boards.inc` (or add a variant in `sim/run_sims.py`) and re-run; replace PROVISIONAL values in "
      "`sim/models.inc` as bench measurements come in.")
    a("")
    if kic:
        a("## Appendix: board schematics (reference)")
        a("")
        a("Exported from the generated KiCad schematics for comparison with the simulated circuits above.")
        a("")
        for b, p in kic.items():
            a(f"![{b} schematic]({p})")
            a("")
    md = "\n".join(L)
    stem = report_stem()
    for old in DOCS.glob("spice-report*.md"):
        if old.name != f"{stem}.md":
            old.unlink()
    (DOCS / f"{stem}.md").write_text(md)
    _html(md, vtag, today, stem)
    return md


def _html(md: str, vtag: str, today: str, stem: str):
    import markdown

    body = markdown.markdown(md, extensions=["tables", "fenced_code"])

    def inline(mo):
        p = DOCS / mo.group(1)
        return f'src="data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"'

    body = re.sub(r'src="(spice/[^"]+\.png)"', inline, body)
    body = re.sub(r"<strong>(PASS|MARGINAL|FAIL|INFO)</strong>",
                  lambda mo: f'<span class="v {BADGE[mo.group(1)]}">{mo.group(1)}</span>', body)
    body = body.replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")
    body = re.sub(r"<p>(<img [^>]+>)</p>\s*<p><em>(.*?)</em></p>", r"<figure>\1<figcaption>\2</figcaption></figure>",
                  body, flags=re.S)
    body = re.sub(r"<p>(<img [^>]+>)</p>", r"<figure>\1</figure>", body)
    (OUT / "report.html").write_text(TEMPLATE.replace("{{BODY}}", body))
    _pdf(body, vtag, today, stem)


def _pdf(body: str, vtag: str, today: str, stem: str):
    """A4 PDF of the same body (WeasyPrint), light theme, versions and page numbers in the footer."""
    try:
        import weasyprint
    except ImportError:
        print("weasyprint not installed: PDF skipped")
        return
    for old in DOCS.glob("spice-report*.pdf"):
        if old.name != f"{stem}.pdf":
            old.unlink()
    css = PRINT_CSS.replace("{{FOOT}}", f"Moon reading light · SPICE report · {vtag} · {today}")
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>SPICE report ({vtag})</title>" \
           f"<style>{css}</style></head><body>{body}</body></html>"
    weasyprint.HTML(string=html, base_url=str(DOCS)).write_pdf(DOCS / f"{stem}.pdf")


TEMPLATE = """<title>Reading Light SPICE Report</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,600&display=swap">
<style>
/* Layout: one reading column (~72ch) for prose; figures and tables run to 1040px; lunar-grey neutrals, one cool accent */
:root {
  --bg: #f6f6f3; --paper: #fcfcfb; --fg: #17181a; --muted: #5a5c60; --rule: #dcdcd6; --accent: #2a5fa8;
  --pass: #0a7d0a; --marg: #9a6400; --fail: #b62f2f; --info: #4f5b6b;
  --pass-bg: #e3f3e3; --marg-bg: #fbefd6; --fail-bg: #f9e1e1; --info-bg: #e8ecf1;
  --display: "Fraunces", Georgia, serif; --body: "IBM Plex Sans", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #121315; --paper: #1b1c1f; --fg: #e9e9e4; --muted: #a6a8ab; --rule: #34363a; --accent: #8ab4f0;
  --pass: #7bd67b; --marg: #f0be5a; --fail: #f08a8a; --info: #b8c3d1;
  --pass-bg: #1d3320; --marg-bg: #3a2e14; --fail-bg: #3d1e1e; --info-bg: #252c35; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #121315; --paper: #1b1c1f; --fg: #e9e9e4; --muted: #a6a8ab; --rule: #34363a; --accent: #8ab4f0;
  --pass: #7bd67b; --marg: #f0be5a; --fail: #f08a8a; --info: #b8c3d1;
  --pass-bg: #1d3320; --marg-bg: #3a2e14; --fail-bg: #3d1e1e; --info-bg: #252c35; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font: 15px/1.6 var(--body); }
main { max-width: 1040px; margin: 0 auto; padding-block: 40px 80px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
main > p, main > ul, main > ol, main > h2, main > h1 { max-width: 72ch; }
h1 { font: 600 clamp(28px, 4vw, 40px)/1.15 var(--display); margin: 0 0 12px; text-wrap: balance; }
h2 { font: 600 22px/1.3 var(--display); margin: 56px 0 12px; padding-top: 16px; border-top: 1px solid var(--rule);
  text-wrap: balance; }
p, li { color: var(--fg); }
ol li, ul li { margin-bottom: 8px; }
code { font: 0.88em var(--mono); background: var(--paper); border: 1px solid var(--rule); border-radius: 4px;
  padding: 1px 4px; }
pre { background: var(--paper); border: 1px solid var(--rule); border-radius: 6px; padding: 12px 14px; overflow-x: auto; }
pre code { border: 0; padding: 0; }
figure { margin: 20px 0 28px; }
figure img { display: block; width: 100%; height: auto; border-radius: 6px; border: 1px solid var(--rule);
  background: #fcfcfb; }
figcaption { color: var(--muted); font-size: 13.5px; margin-top: 8px; max-width: 80ch; }
.tw { overflow-x: auto; margin: 12px 0 20px; border: 1px solid var(--rule); border-radius: 6px; background: var(--paper); }
table { border-collapse: collapse; width: 100%; font-size: 13px; font-variant-numeric: tabular-nums; }
th, td { text-align: left; vertical-align: top; padding: 7px 10px; border-bottom: 1px solid var(--rule); }
th { font-weight: 600; color: var(--muted); font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.05em;
  background: var(--bg); }
tr:last-child td { border-bottom: 0; }
td:first-child { font-family: var(--mono); font-size: 12px; white-space: nowrap; }
.v { display: inline-block; font: 600 11px/1 var(--mono); letter-spacing: 0.04em; padding: 4px 7px; border-radius: 4px; }
.v.pass { color: var(--pass); background: var(--pass-bg); } .v.marg { color: var(--marg); background: var(--marg-bg); }
.v.fail { color: var(--fail); background: var(--fail-bg); } .v.info { color: var(--info); background: var(--info-bg); }
a { color: var(--accent); }
</style>
<main>
{{BODY}}
</main>
"""


PRINT_CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm;
  @bottom-left { content: "{{FOOT}}"; font: 7.5pt "DejaVu Sans", sans-serif; color: #666; }
  @bottom-right { content: "page " counter(page) " / " counter(pages); font: 7.5pt "DejaVu Sans", sans-serif;
    color: #666; } }
body { font: 9.5pt/1.45 "DejaVu Sans", "Liberation Sans", sans-serif; color: #17181a; }
h1 { font-size: 18pt; line-height: 1.2; margin: 0 0 8pt; }
h2 { font-size: 13pt; margin: 18pt 0 6pt; padding-top: 6pt; border-top: 0.6pt solid #ccc; break-after: avoid; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
code { font: 8.5pt "DejaVu Sans Mono", monospace; background: #f1f1ee; padding: 0 2pt; }
pre { background: #f1f1ee; padding: 6pt; font-size: 8pt; }
figure { margin: 8pt 0 12pt; break-inside: avoid; }
figure img, p img { width: 100%; border: 0.5pt solid #ddd; }
figcaption { font-size: 8.5pt; color: #555; margin-top: 3pt; }
.tw { margin: 6pt 0 10pt; }
table { border-collapse: collapse; width: 100%; font-size: 7.6pt; }
th, td { border-bottom: 0.4pt solid #ccc; padding: 3pt 4pt; text-align: left; vertical-align: top; }
th { background: #f1f1ee; font-size: 7pt; text-transform: uppercase; letter-spacing: 0.03em; }
tr { break-inside: avoid; }
.v { font: bold 7pt "DejaVu Sans Mono", monospace; padding: 1.5pt 3pt; border-radius: 2pt; }
.v.pass { color: #0a6d0a; background: #e3f3e3; } .v.marg { color: #8a5a00; background: #fbefd6; }
.v.fail { color: #a62929; background: #f9e1e1; } .v.info { color: #4f5b6b; background: #e8ecf1; }
"""


def decisions(a, d, revs):
    """Findings mapped to the decisions they need: evidence, options with their simulated effect, recommendation."""
    h10, h47, h1, dur = d["h10"], d["h47"], d["h1"], d["dur"]
    j3l, j3f, j3b, po, pob = d["j3l"], d["j3f"], d["j3b"], d["po"], d["pob"]
    ch, chw, hw, hwm, tr = d["ch"], d["chw"], d["hw"], d["hwm"], d["tr"]
    a("## Findings and decisions to make")
    a("")
    a(f"Each finding below is for main board v{revs['main-board']} / LED board v{revs['led-board']}. The options give "
      "the simulated effect where it was simulated; \"not simulated\" marks an engineering estimate. Nothing has been "
      "changed in the design: every option is Matt's call. *If no decision* says what happens by default.")
    a("")
    a("| # | Finding | Severity | Decision needed | Recommendation |")
    a("|---|---|---|---|---|")
    a(f"| D1 | USB unplug: VSYS dips {d['dip']:.2f} V for {dur(h10):.0f} ms | **FAIL** (E12) | accept, change R5, or "
      "redesign the handover | accept for v0.1, re-word E12; R5 1k if the blink is visible |")
    a(f"| D2 | J3 hot-plug at 3.5 V: VSYS {j3l['vsys_min']:.2f} V, below BOD | **FAIL** (E13 step) | change the test "
      "or add bulk capacitance | change the test (plug J3 with SW1 off) |")
    a(f"| D3 | VSYS {chw['vsys_min']:.2f} V on a weak USB source | **MARGINAL** (E15) | define the E15 source | "
      "E15 on a 5.0 V source; no hardware change |")
    a(f"| D4 | Max-VF white dies lose regulation at VSYS {hwm['vsys_w95']:.2f} V | **MARGINAL** | RIREF / LED bin "
      "(already open as VERIFY E9) | decide after E9 |")
    a(f"| D5 | I²C {tr['c150']:.0f} ns at 150 pF | **MARGINAL** for fast mode only | bus speed | keep 100 kHz (no change) |")
    a(f"| D6 | Q4 charging current {d['q4max'] * 1e3:.0f} mA vs the 15-25 mA in the design note | INFO | documentation "
      "| correct the note in `electronics.md` §1 |")
    a("")

    a("### D1. USB unplug handover (VERIFY E12)")
    a("")
    a(f"**Finding.** Pulling USB with the lamp at 4000 K full drops VSYS from {h10['vsys_usb']:.2f} V to "
      f"{h10['vsys_min']:.2f} V, {d['dip']:.2f} V below the {h10['vsys_bat']:.2f} V it settles at on the battery, for "
      f"{dur(h10):.0f} ms. The LED-board current falls from {h10['iled_usb'] * 1e3:.0f} mA to about 130 mA for that "
      "time. The MCU stays above its 2.6 V BOD. Figure: section 5.")
    a("")
    a("**Cause.** Q1's gate sits on VBUS. After the unplug the lamp runs through Q1's body diode (about 0.65 V) until "
      "R5 has discharged VBUS below VSYS_RAW − |VGS(th)|. R5 sets how long that takes, not how deep the dip is.")
    a("")
    a("| Option | Simulated effect | Cost / risk |")
    a("|---|---|---|")
    a(f"| A. Accept; re-word E12 to \"no reset, dip ≤ 0.7 V for ≤ 25 ms\" | as built: {dur(h10):.0f} ms dip | a "
      "possible visible dim at unplug |")
    a(f"| B. R5 4.7k (E12's listed remedy) | {dur(h47):.0f} ms, same depth | +0.6 mA from USB while plugged |")
    a(f"| C. R5 1k | {dur(h1):.1f} ms, same depth | +4.5 mA from USB while plugged (25 mW in R5); a value "
      "change only |")
    a("| D. Next revision: drive Q1's gate actively (e.g. a comparator or ideal-diode controller) | not simulated; "
      "removes the body-diode phase | new part, layout change, standby-drain review (R17) |")
    a("")
    a("**Recommendation.** A for v0.1, and look for the dim during the E12 bench check. If it is visible, C is a "
      "one-resistor change that cuts it to a couple of milliseconds. Consider D in the next revision.")
    a("")
    a("**If no decision.** E12 will be marked failed at the bench against its current 0.3 V limit.")
    a("")

    a("### D2. Hot-plugging the LED-board cable (VERIFY E13)")
    a("")
    a(f"**Finding.** Plugging J3 while VLED is live sags VSYS to {j3l['vsys_min']:.2f} V at a 3.49 V cell (below the "
      f"2.6 V BOD: expect a reset) and to {j3f['vsys_min']:.2f} V on a full cell. The cable carries a "
      f"{j3f['ipk']:.0f} A pulse about 1.5 µs wide. Figure: section 3.")
    a("")
    a("**Cause.** The main board has no bulk capacitance on VLED, so the LED board's empty MLCCs (about 11 µF "
      "unbiased) take their charge from C4 on VSYS faster than the cell can supply it through its resistance and lead.")
    a("")
    a("| Option | Simulated effect | Cost / risk |")
    a("|---|---|---|")
    a("| A. Remove the hot-plug step from E13; plug J3 only with SW1 off | the case does not occur in use (the cable is "
      "inside the gooseneck) | none |")
    a(f"| B. 47 µF on VSYS (E13's listed remedy) | VSYS min {j3b['vsys_min']:.2f} V (0.12 V above BOD; depends on the "
      f"assumed 0.1 Ω ESR) | power-on inrush {po['ipk']:.2f} → {pob['ipk']:.2f} A; board space and a new part |")
    a("| C. Firmware: keep Q4 off until the cable is known to be connected | not simulated | only helps if the cable is "
      "plugged before power-up |")
    a("")
    a("**Recommendation.** A. B buys little margin and costs inrush.")
    a("")
    a("**If no decision.** The E13 hot-plug step will likely show a reset at a low battery.")
    a("")

    a("### D3. VSYS on a weak USB source (VERIFY E15)")
    a("")
    a(f"**Finding.** At 4.75 V USB (the bottom of the 5 V ±5 % band) through a 0.2 Ω cable with F1 at its 0.2 Ω "
      f"maximum, VSYS is {chw['vsys_min']:.2f} V while charging with the lamp on; on 5.0 V it is "
      f"{ch['vsys_min']:.2f} V. Q1's body diode then leaks {chw['idq1_max'] * 1e3:.2f} mA from the cell, which does "
      "not stop the charge from terminating. Figure: section 6.")
    a("")
    a("| Option | Effect | Cost / risk |")
    a("|---|---|---|")
    a(f"| A. Specify E15 on a 5.0 V source | E15 passes ({ch['vsys_min']:.2f} V) | none |")
    a(f"| B. Accept lower VSYS on weak sources | the whites stay regulated down to VSYS {hw['vsys_w95']:.2f} V "
      f"(typical dies), so the lamp is unaffected | none |")
    a("")
    a("**Recommendation.** A and B together: re-word E15. No hardware change.")
    a("")

    a("### D4. White-LED headroom with maximum-VF dies (VERIFY E9)")
    a("")
    a(f"**Finding.** With the highest-VF white dies and the worst LP5012 saturation voltage, the whites start to dim at "
      f"VSYS {hwm['vsys_w95']:.2f} V, just under the firmware's 3.45 V brightness cap (typical dies: "
      f"{hw['vsys_w95']:.2f} V). Figure: section 8.")
    a("")
    a("**Decision.** Already open as VERIFY E9 (measure the received dies; option RIREF 3.65 kΩ for 20 mA). This "
      "adds the white channels to what E9 should measure. No action before E9.")
    a("")

    a("### D5. I²C speed")
    a("")
    a(f"**Finding.** Rise times {tr['c60']:.0f} / {tr['c100']:.0f} / {tr['c150']:.0f} ns for 60 / 100 / 150 pF: "
      "inside standard mode (1000 ns) at every value, inside fast mode (300 ns) only at 60-100 pF.")
    a("")
    a("**Decision.** None needed while the firmware stays at 100 kHz. Moving to 400 kHz would need a measured bus "
      "capacitance below about 100 pF or stronger pull-ups.")
    a("")

    a("### D6. Documentation correction")
    a("")
    a(f"`docs/design/electronics.md` §1 says Q4's soft turn-on charges the LED board with 15-25 mA. The simulation "
      f"gives up to {d['q4max'] * 1e3:.0f} mA, because the MLCCs start near their unbiased value. Harmless "
      "(VSYS moves by about 12 mV). Decide whether to correct the note.")
    a("")
