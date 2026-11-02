"""Generate firmware/include/modes_table.h: per-mode drive ratios for the LED groups.

Groups: WW (4 x 2700K 2835), CW (4 x 5000K 2835), R, G, B (two 5050 RGB LEDs, each die on its own channel). For each white mode we solve the
luminance mix that lands exactly on the Planckian locus at the target CCT (CIE 1931 xy), using WW + CW and a
little G (or B) to correct Duv. Night modes follow docs/research/light-modes.md: red, or red + a little 2700K,
never green. Drive ratios are normalised so the strongest group = 1.0 (= full TLC59116 current, 25 mA), except
Green and Blue, which run at 0.5 for supply headroom.

LED data below is nominal datasheet data (VERIFY against the received bins; see docs/design/electronics.md).
Usage: python3 firmware/tools/gen_modes.py  [writes include/modes_table.h and prints a summary]
"""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np

LED = {   # lumens per LED at 25.0 mA (TLC59116, REXT 750 R). Datasheet typicals: VERIFY against received parts.
    "WW": (0.4599, 0.4106, 8.5, 4),    # Bridgelux BXEN-27S 2700K CRI97: 51 lm @150 mA x ~0.20 @30 mA (DS312 Fig. 10) x 25/30
    "CW": (0.3451, 0.3516, 9.3, 4),    # BXEN-50S 5000K CRI97: 56 lm @150 mA, same scaling
    "R": (0.700, 0.299, 1.06, 2),      # 2 x Wurth 150141M173100 red 625 nm: 270 mcd typ @20 mA -> pi*Iv x 25/20
    "G": (0.170, 0.700, 3.73, 2),      # green 520 nm: 950 mcd typ @20 mA (xy VERIFY: 520 nm sits greener than this)
    "B": (0.131, 0.075, 0.90, 2),      # blue 470 nm: 230 mcd typ @20 mA
}
GROUPS = ["WW", "CW", "R", "G", "B"]

PLANCK = {1900: (0.5389, 0.4103), 2700: (0.4599, 0.4106), 3000: (0.4369, 0.4041), 4000: (0.3805, 0.3768),
          5000: (0.3451, 0.3516), 6500: (0.3136, 0.3237)}   # CIE 1931 2deg (integrated; research note)


def mix_xy(lum):
    X = sum(LED[g][0] / LED[g][1] * lum[g] for g in lum)
    Y = sum(lum.values())
    Z = sum((1 - LED[g][0] - LED[g][1]) / LED[g][1] * lum[g] for g in lum)
    return X / (X + Y + Z), Y / (X + Y + Z)


def solve(target_xy, groups):
    """Luminance fractions (sum 1) of exactly three groups that hit target xy; None if any negative."""
    xt, yt = target_xy
    A = []
    for g in groups:
        x, y = LED[g][0], LED[g][1]
        A.append([x / y - xt / yt, (1 - x - y) / y - (1 - xt - yt) / yt, 1.0])
    A = np.array(A).T
    b = np.array([0.0, 0.0, 1.0])
    try:
        lum = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return None
    if (lum < -1e-9).any():
        return None
    return dict(zip(groups, np.clip(lum, 0, None)))


def drive_from_lum(lum):
    """Luminance shares -> group drive (fraction of full current), strongest group = 1."""
    d = {g: lum.get(g, 0.0) / (LED[g][2] * LED[g][3]) for g in GROUPS}
    m = max(d.values())
    return {g: d[g] / m for g in GROUPS}


MODES = []   # (id, label, recipe-dict-of-drives, default_level, max_level, note)


def white(cct, groups):
    lum = solve(PLANCK[cct], groups)
    if lum is None:
        raise ValueError(f"cannot reach {cct} K with {groups}")
    return drive_from_lum(lum), lum


def build():
    out = []
    w2700 = {"WW": 1.0, "CW": 0.0, "R": 0.0, "G": 0.0, "B": 0.0}
    out.append(("WARM_2700", "Warm white 2700K", w2700, 9, 15, "WW only"))
    for cct, lab, dflt in ((3000, "Soft white 3000K", 10), (4000, "Neutral reading 4000K", 12), (5000, "Daylight 5000K", 12)):
        best = None
        for grp in (["WW", "CW", "G"], ["WW", "CW", "R"], ["WW", "CW", "B"]):
            s = solve(PLANCK[cct], grp)
            if s is not None and (best is None or s.get("G", 0) + s.get("R", 0) + s.get("B", 0) < best[1]):
                best = (grp, s.get("G", 0) + s.get("R", 0) + s.get("B", 0), s)
        d = drive_from_lum(best[2])
        out.append((f"WHITE_{cct}", lab, d, dflt, 15, f"{'+'.join(best[0])}, Duv 0 by construction"))
    d6500, _ = white(6500, ["CW", "B", "G"])
    out.append(("COOL_6500", "Blue-white 6500K", d6500, 12, 15, "CW + B + G"))
    d1900, _ = white(1900, ["WW", "R", "G"])
    out.append(("CANDLE_1900", "Candlelight 1900K", d1900, 7, 13, "WW + R + a little G"))
    orange = drive_from_lum({"R": 0.7, "WW": 0.3})
    # WW is ~16x more efficient than R, so its drive is ~3 % of R's: at 8-bit PWM it has 0-3 counts below level 10
    # and the low levels render red-orange to red (accepted, docs/verification/round1.md F9; v0.2: an amber LED)
    out.append(("NIGHT_ORANGE", "Soft orange night light", orange, 6, 15, "R 70% + WW 30% by luminance; no green"))
    out.append(("NIGHT_RED", "Red night light", {"WW": 0, "CW": 0, "R": 1.0, "G": 0, "B": 0}, 4, 15,
                "R only (max 15: optical review F9, still < 1 lux at 30 cm)"))
    # Green and blue at half current (12.4 mA, IREF step 0xBF): VF + TLC knee then fits under VLED down to ~3.6 V
    # of battery instead of only near full charge (electrical review M1)
    out.append(("GREEN", "Green", {"WW": 0, "CW": 0, "R": 0, "G": 0.5, "B": 0}, 8, 15, "G only, half current"))
    out.append(("BLUE", "Blue", {"WW": 0, "CW": 0, "R": 0, "G": 0, "B": 0.5}, 8, 15, "B only, half current"))
    return out


def main():
    modes = build()
    root = Path(__file__).resolve().parents[1]
    lines = ["// GENERATED by firmware/tools/gen_modes.py - do not edit by hand.",
             "// Drive ratios per LED group (Q12: 4096 = full TLC59116 current), strongest group = 4096 (Green/Blue 2048).",
             "#pragma once", "#include <stdint.h>", "",
             "enum { G_WW = 0, G_CW, G_R, G_G, G_B, G_COUNT };", "",
             "typedef struct { const char *name; uint16_t q12[G_COUNT]; uint8_t default_level; uint8_t max_level; } mode_t_;",
             f"#define MODE_COUNT {len(modes)}", "",
             "static const mode_t_ MODES[MODE_COUNT] = {"]
    print(f"{'mode':<24}{'WW':>7}{'CW':>7}{'R':>7}{'G':>7}{'B':>7}   xy check")
    for mid, label, d, dl, ml, note in modes:
        q = [int(round(4096 * d[g])) for g in GROUPS]
        lum = {g: d[g] * LED[g][2] * LED[g][3] for g in GROUPS if d[g] > 0}
        xy = mix_xy(lum)
        lumens = sum(lum.values())
        lines.append(f'    {{"{label}", {{{", ".join(str(v) for v in q)}}}, {dl}, {ml}}},  // {mid}: {note}; '
                     f'xy=({xy[0]:.4f},{xy[1]:.4f}), {lumens:.0f} lm at full drive')
        print(f"{mid:<24}" + "".join(f"{d[g]:7.3f}" for g in GROUPS) + f"   ({xy[0]:.4f},{xy[1]:.4f}) {lumens:5.1f} lm")
    lines += ["};", ""]
    (root / "include" / "modes_table.h").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
