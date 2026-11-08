"""Waveform figures for the SPICE report (matplotlib, PNG). One figure per case; panels share x, never a 2nd y-axis."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

FIG = Path(__file__).resolve().parents[1] / "docs" / "verification" / "spice"
# reference categorical palette, fixed order (dataviz skill references/palette.md, light mode)
S = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "font.size": 9,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "lines.linewidth": 1.8, "legend.frameon": False, "axes.titlesize": 10,
    "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def limit(ax, y, text, va="bottom", color=INK2):
    ax.axhline(y, color=color, lw=1.0, ls=(0, (4, 3)))
    ax.annotate(text, (1.0, y), xycoords=("axes fraction", "data"), ha="right", va=va, fontsize=8, color=color,
                xytext=(0, 2 if va == "bottom" else -2), textcoords="offset points")


def save(fig, name, title, sub):
    h = fig.get_figheight()
    fig.text(0.01, 1 - 0.08 / h, title, ha="left", va="top", fontsize=11, fontweight="bold")
    fig.text(0.01, 1 - 0.34 / h, sub, ha="left", va="top", fontsize=8.5, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.58 / h))
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{name}.png", dpi=130)
    plt.close(fig)
    return f"spice/{name}.png"


def make_all(R) -> dict[str, str]:
    f = {}
    g = lambda c, v: R[(c, v)][1]  # noqa: E731
    lab = lambda c, v: R[(c, v)][0]  # noqa: E731

    # ---- power-on
    fig, ax = plt.subplots(2, 1, figsize=(7.5, 5.2), sharex=True)
    for k, v in enumerate(("full", "low", "full_bulk47")):
        r = g("poweron", v)
        t = (r.x - 1e-3) * 1e3
        ax[0].plot(t, r.col("ibat"), color=S[k], label=lab("poweron", v))
        ax[1].plot(t, r.col("v(vsys)"), color=S[k], label=lab("poweron", v))
        ax[0].annotate(f"{r.meas['ipk']:.2f} A", (t[np.argmax(r.col('ibat'))], r.meas["ipk"]), xytext=(6, 0),
                       textcoords="offset points", fontsize=8, color=INK)
    ax[0].set_ylabel("cell current (A)")
    ax[1].set_ylabel("VSYS (V)")
    ax[1].set_xlabel("time after SW1 closes (ms)")
    ax[0].legend(loc="upper right")
    ax[1].set_xlim(-0.1, 1.0)
    f["poweron"] = save(fig, "poweron", "Power-on inrush through Q2 (slide switch)",
                        "Cell current and VSYS; LED board off (Q4 held off by R12). Q2 soft start R7 10k / C5 100n")

    # ---- Q4 soft start
    fig, ax = plt.subplots(2, 1, figsize=(7.5, 5.2), sharex=True)
    for k, v in enumerate(("low", "full", "low_vth05", "low_vth09")):
        r = g("q4_softstart", v)
        t = (r.x - 1e-3) * 1e3
        ax[0].plot(t, r.col("v(vledb)"), color=S[k], label=lab("q4_softstart", v))
        ax[1].plot(t, r.col("iq4") * 1e3, color=S[k], label=lab("q4_softstart", v))
    r = g("q4_softstart", "low")
    ax[0].plot((r.x - 1e-3) * 1e3, r.col("v(vsys)"), color=INK2, lw=1, ls=":", label="VSYS (3.49 V cell)")
    ax[0].set_ylabel("VLED at the LED board (V)")
    ax[1].set_ylabel("Q4 / cable current (mA)")
    ax[1].set_xlabel("time after PB2 goes low (ms)")
    ax[0].legend(loc="lower right", fontsize=8)
    ax[1].set_xlim(-0.2, 3)
    f["q4_softstart"] = save(fig, "q4_softstart", "Q4 soft turn-on of the LED board",
                             "R13 10k into C8 100n (gate-drain) sets the ramp; 4 corners (cell voltage, VGS(th))")

    # ---- J3 hot-plug
    fig, ax = plt.subplots(2, 1, figsize=(7.5, 5.2), sharex=True)
    for k, v in enumerate(("full", "low", "low_bulk47")):
        r = g("j3_hotplug", v)
        t = (r.x - 100e-6) * 1e6
        ax[0].plot(t, r.col("icab"), color=S[k], label=lab("j3_hotplug", v))
        ax[1].plot(t, r.col("v(vsys)"), color=S[k], label=f"VSYS, {lab('j3_hotplug', v)}")
        ax[1].plot(t, r.col("v(vledb)"), color=S[k], lw=1.1, ls="--", label=f"LED board, {lab('j3_hotplug', v)}")
    limit(ax[1], 2.6, "ATtiny BOD 2.6 V", va="top")
    ax[0].set_ylabel("cable current (A)")
    ax[1].set_ylabel("voltage (V)")
    ax[1].set_xlabel("time after the plug makes contact (us)")
    ax[0].legend(loc="upper right")
    ax[1].legend(loc="lower right", fontsize=7, ncol=3)
    ax[1].set_xlim(-1, 12)
    f["j3_hotplug"] = save(fig, "j3_hotplug", "Hot-plugging the LED-board cable with VLED live",
                           "No bulk capacitance on the main board's VLED: C4 (VSYS) charges the LED board's MLCCs")

    # ---- USB hot-plug
    fig, ax = plt.subplots(2, 1, figsize=(7.5, 5.2), sharex=True)
    for k, v in enumerate(("r01", "r03")):
        r = g("usb_hotplug", v)
        t = (r.x - 100e-6) * 1e6
        ax[0].plot(t, r.col("iusb"), color=S[k], label=lab("usb_hotplug", v))
        ax[1].plot(t, r.col("v(vbus)"), color=S[k], label=f"VBUS, {lab('usb_hotplug', v)}")
        ax[1].plot(t, r.col("v(vsys)"), color=S[k], lw=1.1, ls="--", label=f"VSYS, {lab('usb_hotplug', v)}")
    limit(ax[1], 7.0, "MCP73831 abs max 7.0 V")
    limit(ax[1], 6.0, "ATtiny / LP5012 abs max 6.0 V")
    ax[0].set_ylabel("USB current (A)")
    ax[1].set_ylabel("voltage (V)")
    ax[1].set_ylim(3.0, 7.5)
    ax[1].set_xlabel("time after the USB plug makes contact (us)")
    ax[0].legend(loc="upper right")
    ax[1].legend(loc="lower right", fontsize=7.5, ncol=2)
    ax[1].set_xlim(-2, 60)
    f["usb_hotplug"] = save(fig, "usb_hotplug", "USB-C plug-in while the lamp runs on the battery",
                            "5.25 V source, 1 uH cable; C1 rings with the cable, D3 charges VSYS_RAW from VBUS")

    # ---- USB unplug
    fig, ax = plt.subplots(2, 1, figsize=(7.5, 5.2), sharex=True)
    for k, v in enumerate(("r5_10k", "r5_4k7", "r5_1k")):
        r = g("usb_unplug", v)
        t = (r.x - 5e-3) * 1e3
        ax[0].plot(t, r.col("v(vsys)"), color=S[k], label=lab("usb_unplug", v))
        ax[1].plot(t, r.col("iled") * 1e3, color=S[k], label=lab("usb_unplug", v))
    vb = g("usb_unplug", "r5_10k").meas["vsys_bat"]
    limit(ax[0], vb - 0.3, "E12 limit: 0.3 V below the battery level", va="top")
    limit(ax[0], 2.6, "BOD 2.6 V")
    ax[0].set_ylabel("VSYS (V)")
    ax[1].set_ylabel("LED-board current (mA)")
    ax[1].set_xlabel("time after USB is pulled (ms)")
    ax[0].legend(loc="upper right")
    ax[0].set_xlim(-2, 40)
    f["usb_unplug"] = save(fig, "usb_unplug", "USB unplug handover to the battery (4000 K full, cell 3.6 V)",
                           "Q1's body diode carries the load until R5 pulls VBUS low enough to turn Q1's channel on")

    # ---- handover redesign options (D1)
    fig, ax = plt.subplots(2, 1, figsize=(7.5, 5.2), sharex=True)
    for k, v in enumerate(("r5_10k", "r5_1k", "sch", "lm_r5_1k", "idd")):
        r = g("usb_unplug", v)
        t = (r.x - 5e-3) * 1e3
        ax[0].plot(t, r.col("v(vsys)"), color=S[k], label=lab("usb_unplug", v))
        ax[1].plot(t, r.col("iled") * 1e3, color=S[k], label=lab("usb_unplug", v))
    vb = g("usb_unplug", "r5_10k").meas["vsys_bat"]
    limit(ax[0], vb - 0.3, "E12 limit", va="top")
    ax[0].set_ylabel("VSYS (V)")
    ax[1].set_ylabel("LED-board current (mA)")
    ax[1].set_xlabel("time after USB is pulled (ms)")
    ax[0].legend(loc="upper right", fontsize=8)
    ax[0].set_xlim(-1, 25)
    f["handover_options"] = save(fig, "handover_options", "USB unplug: the as-built handover and the alternatives",
                                 "Cell 3.6 V, 4000 K full. Options other than R5 are not on the v0.1 board")
    # ---- detector hazard on a weak source (D1)
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    for k, v in ((2, "weak_det43"), (3, "weak_idd")):
        r = g("charge", v)
        sel = r.x <= 150
        ax.plot(r.x[sel], r.col("ichg")[sel] * 1e3, color=S[k], label=lab("charge", v),
                lw=1.2 if v == "weak_det43" else 1.8)
    limit(ax, 256, "charger setting 256 mA")
    ax.set_xlabel("time from plug-in (s), empty cell")
    ax.set_ylabel("cell current (mA)")
    ax.legend(loc="upper right", fontsize=8)
    f["handover_hazard"] = save(fig, "handover_hazard", "Why a raised switch-over threshold needs reverse blocking",
                                "4.75 V source, lamp on: a detector-driven Q1 latches on at plug-in and USB charges the "
                                "cell through D3 + Q1, past the charger")

    # ---- charge
    fig, ax = plt.subplots(3, 1, figsize=(7.5, 6.6), sharex=True)
    for k, v in enumerate(("lamp", "dark", "lamp_weak")):
        r = g("charge", v)
        t = r.x / 3600
        ax[0].plot(t, r.col("ichg") * 1e3, color=S[k], label=lab("charge", v))
        ax[1].plot(t, r.col("v(batraw)"), color=S[k], label=lab("charge", v))
        ax[2].plot(t, r.col("v(vsys)"), color=S[k], label=lab("charge", v))
    limit(ax[0], 31, "termination 31 mA (7.5 %)")
    limit(ax[2], 3.9, "E15: VSYS >= 3.9 V on USB", va="top")
    ax[0].set_ylabel("cell current (mA)")
    ax[1].set_ylabel("cell voltage (V)")
    ax[2].set_ylabel("VSYS (V)")
    ax[2].set_xlabel("time (h)")
    ax[0].legend(loc="upper right", fontsize=8)
    ax[2].set_xlim(0, 7)
    f["charge"] = save(fig, "charge", "Charging from empty on USB, with and without the lamp",
                       "MCP73831 CC 256 mA / CV 4.20 V; the lamp is fed through D3, so the cell current is unchanged")

    # ---- runtime: small multiples (different time scales)
    fig, ax = plt.subplots(1, 3, figsize=(9.5, 3.6))
    for k, (v, extra) in enumerate((("4000k", []), ("soft10", []), ("night", ["night_lo", "night_hi"]))):
        r = g("runtime", v)
        t = r.x / 3600
        ax[k].plot(t, r.col("v(vsys)"), color=S[k], label="VSYS (under load)")
        ax[k].plot(t, r.col("v(batraw)"), color=S[k], lw=1.0, ls="--", label="cell terminal")
        for e in extra:
            re_ = g("runtime", e)
            ax[k].plot(re_.x / 3600, re_.col("v(vsys)"), color=S[k], lw=0.8, alpha=0.45)
        ax[k].axhline(3.45, color=INK2, lw=1, ls=(0, (4, 3)))
        ax[k].axhline(3.30, color=INK2, lw=1, ls=(0, (4, 3)))
        te = r.meas["t_empty"] / 3600
        ax[k].axvline(te, color=INK2, lw=0.8)
        ax[k].set_title(f"{lab('runtime', v)}: {te:.0f} h" if te > 20 else f"{lab('runtime', v)}: {te:.1f} h",
                        fontsize=9)
        ax[k].set_xlim(0, te * 1.08)
        ax[k].set_ylim(3.1, 4.25)
        ax[k].set_xlabel("time (h)")
    ax[0].set_ylabel("voltage (V)")
    ax[0].text(0.2, 3.46, "LOW cap 3.45 V", fontsize=7.5, color=INK2, va="bottom")
    ax[0].text(0.2, 3.29, "empty 3.30 V", fontsize=7.5, color=INK2, va="top")
    ax[0].legend(loc="upper right", fontsize=7.5)
    ax[2].text(0.02, 0.04, "faint: electronics 7 / 12 mA", transform=ax[2].transAxes, fontsize=7.5, color=INK2)
    f["runtime"] = save(fig, "runtime", "Battery life per mode (1200 mAh, from full to the firmware's empty cut)",
                        "Firmware caps brightness to 35 % below 3.45 V and sleeps below 3.30 V (measured on VSYS)")

    # ---- headroom
    fig, ax = plt.subplots(1, 2, figsize=(9.0, 3.8), sharey=True)
    for k, v in enumerate(("white_typ", "white_max")):
        r = g("headroom", v)
        ax[0].plot(r.x, r.col("iw") * 1e3, color=S[k], label=lab("headroom", v).replace("8 whites, ", ""))
    for k, v in enumerate(("green_typ", "green_max")):
        r = g("headroom", v)
        ax[1].plot(r.x, r.col("ig") * 1e3, color=S[k + 2], label=lab("headroom", v).replace("Green mode, ", ""))
    for a in ax:
        a.axhline(23.75, color=INK2, lw=1, ls=(0, (4, 3)))
        a.axvline(3.45, color=INK2, lw=0.8, ls=":")
        a.set_xlabel("cell open-circuit voltage (V)")
        a.legend(loc="lower right", fontsize=8)
        a.set_xlim(3.0, 4.3)
    ax[0].set_ylabel("channel current (mA)")
    ax[0].set_title("White channel (all 8 on: 200 mA peak)", fontsize=9)
    ax[1].set_title("Green channel (Green mode)", fontsize=9)
    ax[0].text(3.02, 24.0, "95 % of 25 mA", fontsize=7.5, color=INK2)
    ax[0].text(3.46, 2, "3.45 V", fontsize=7.5, color=INK2)
    f["headroom"] = save(fig, "headroom", "LED channel regulation vs battery voltage",
                         "LP5012 sink (VSAT) + LED VF + path drop (cell 0.2 Ohm, Q3/Q1/Q2/Q4, cable)")

    # ---- PWM ripple
    fig, ax = plt.subplots(2, 1, figsize=(7.5, 5.0), sharex=True)
    for k, v in enumerate(("d50", "d89")):
        r = g("pwm_ripple", v)
        sel = r.x >= 2.9e-3
        t = (r.x[sel] - 2.9e-3) * 1e6
        ax[0].plot(t, r.col("ib")[sel], color=S[k], label=f"VLED at LP5012, {lab('pwm_ripple', v)}")
        ax[0].plot(t, r.col("v(vsys)")[sel], color=S[k], lw=1.0, ls="--", label=f"VSYS, {lab('pwm_ripple', v)}")
        ax[1].plot(t, r.col("icab")[sel] * 1e3, color=S[k], label=lab("pwm_ripple", v))
    ax[0].set_ylabel("voltage (V)")
    ax[1].set_ylabel("cable current (mA)")
    ax[1].set_xlabel("time (us), 3 PWM periods at 29 kHz")
    ax[0].legend(loc="lower right", fontsize=7.5, ncol=2)
    f["pwm_ripple"] = save(fig, "pwm_ripple", "29 kHz PWM ripple, all 8 whites switching in phase (worst case)",
                           "The cable and LED-board MLCCs filter the 200 mA steps; battery cell at 3.74 V")

    # ---- I2C
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    for k, v in enumerate(("c60", "c100", "c150")):
        r = g("i2c_rise", v)
        tr = (r.meas["t70"] - r.meas["t30"]) * 1e9
        ax.plot((r.x - 10e-6) * 1e9, r.col("v(sda)"), color=S[k], label=f"{lab('i2c_rise', v)}: tr {tr:.0f} ns")
    limit(ax, 0.3 * 4.2, "30 %")
    limit(ax, 0.7 * 4.2, "70 %")
    limit(ax, 1.4, "LP5012 VIH 1.4 V", va="top")
    ax.set_xlim(-50, 1500)
    ax.set_xlabel("time after release (ns)")
    ax.set_ylabel("SDA (V)")
    ax.legend(loc="lower right")
    f["i2c_rise"] = save(fig, "i2c_rise", "I2C rise time, 3.3 k pull-ups on VLED (4.2 V)",
                         "Standard mode allows 1000 ns (30-70 %); the bus runs at 100 kHz")
    return f
