"""Fabrication outputs for one board revision -> fab/<board>/v<REV>/

  gerbers/ + <board>-v<REV>-gerbers.zip   (Gerber X2 RS-274X, Excellon drill mm, PTH+NPTH) - PCBWay / JLCPCB / any fab
  bom_pcbway.csv, cpl_pcbway.csv            PCBWay assembly format
  bom_jlcpcb.csv, cpl_jlcpcb.csv            JLCPCB assembly format (LCSC column left for the quote step)
  bom_farnell.csv                           order lines for this board (see bom/ for the combined order)
  schematic.pdf, assembly_top.pdf, assembly_bottom.pdf, <board>.step, renders/*.png
  FAB_NOTES.md                              board spec to paste into the fab's order form
"""
from __future__ import annotations

import csv
import shutil
import subprocess
import zipfile
from collections import OrderedDict
from pathlib import Path

HW = Path(__file__).resolve().parent
ROOT = HW.parent

LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"


def sh(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def export(board, d, parts):
    rev = d.REV
    out = ROOT / "fab" / board / f"v{rev}"
    if out.exists():
        shutil.rmtree(out)
    (out / "gerbers").mkdir(parents=True)
    pcb = HW / board / f"{d.PROJECT}.kicad_pcb"
    sch = HW / board / f"{d.PROJECT}.kicad_sch"
    sh(["kicad-cli", "pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask",
        "--use-drill-file-origin", "-o", out / "gerbers", pcb])
    sh(["kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
        "--excellon-separate-th", "--generate-map", "--map-format", "gerberx2", "-o", str(out / "gerbers") + "/", pcb])
    zp = out / f"{board}-v{rev}-gerbers.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted((out / "gerbers").iterdir()):
            if f.name.endswith("-drl_map.gbr") or f.stat().st_size < 600 and not _has_features(f):
                continue                       # drill maps and empty layers confuse fab viewers (round2 R2-D20)
            z.write(f, f.name)
    # placement
    raw = out / "pos_raw.csv"
    sh(["kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
        "--exclude-dnp", "-o", raw, pcb])
    rows = list(csv.DictReader(raw.open()))
    raw.unlink()
    byref = {p.ref: p for p in parts}
    # placement only for parts that are bought and placed (not the LED board's J1 cable pads, round2 R2-D9)
    rows = [r for r in rows if r["Ref"] in byref and byref[r["Ref"]].in_bom and not byref[r["Ref"]].dnp]
    smd_refs = []
    with (out / "cpl_pcbway.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X(mm)", "Mid Y(mm)", "Layer", "Rotation"])
        for r in rows:
            w.writerow([r["Ref"], r["PosX"], r["PosY"], "Top" if r["Side"] == "top" else "Bottom", r["Rot"]])
            smd_refs.append(r["Ref"])
    with (out / "cpl_jlcpcb.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            w.writerow([r["Ref"], r["PosX"] + "mm", r["PosY"] + "mm", "Top" if r["Side"] == "top" else "Bottom", r["Rot"]])
    # BOM grouped by part number
    groups = OrderedDict()
    for p in parts:
        if not p.in_bom or p.dnp or not p.on_board:
            continue
        key = (p.fields.get("MPN", ""), p.value, p.footprint)
        groups.setdefault(key, []).append(p)
    with (out / "bom_pcbway.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Item #", "Designator", "Qty", "Manufacturer", "Mfg Part #", "Description / Value",
                    "Package/Footprint", "Type", "Your Instructions / Notes", "Farnell"])
        for i, ((mpn, val, fp), ps) in enumerate(groups.items(), 1):
            refs = sorted((p.ref for p in ps), key=_natkey)
            tht = any(fp.startswith(x) for x in ("Connector_PinHeader",))
            kind = "THT" if tht else ("SMD + THT (shell slots)" if "USB_C" in fp else "SMD")
            w.writerow([i, ",".join(refs), len(ps), ps[0].fields.get("Manufacturer", ""), mpn,
                        f"{val} - {ps[0].fields.get('Description', '')}", fp.split(':')[-1],
                        kind, _note(ps[0]), ps[0].fields.get("Farnell", "")])
    with (out / "bom_jlcpcb.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Manufacturer Part Number"])
        for (mpn, val, fp), ps in groups.items():
            w.writerow([val, ",".join(sorted((p.ref for p in ps), key=_natkey)), fp.split(':')[-1],
                        ps[0].fields.get("LCSC", ""), mpn])
    sh(["kicad-cli", "sch", "export", "pdf", "-o", out / "schematic.pdf", sch])
    sh(["kicad-cli", "pcb", "export", "pdf", "--layers", "F.Fab,F.Silkscreen,Edge.Cuts", "--include-border-title",
        "--crossout-DNP-footprints-on-fab-layers", "-o", out / "assembly_top.pdf", pcb])
    sh(["kicad-cli", "pcb", "export", "pdf", "--layers", "B.Fab,B.Silkscreen,Edge.Cuts", "--mirror",
        "--include-border-title", "--crossout-DNP-footprints-on-fab-layers", "-o", out / "assembly_bottom.pdf", pcb])
    try:
        sh(["kicad-cli", "pcb", "export", "step", "--subst-models", "--force", "-o", out / f"{board}.step", pcb])
    except RuntimeError as e:
        print("  STEP export failed:", str(e)[:200])
    try:
        import render
        render.render(board, out / "renders")
    except Exception as e:  # noqa: BLE001
        print("  render failed:", e)
    (out / "FAB_NOTES.md").write_text(d.FAB_NOTES if hasattr(d, "FAB_NOTES") else "")
    print(f"fab outputs -> {out.relative_to(ROOT)}")
    return out


def _note(p):
    """Per-part-type polarity notes for the assembler (round2 R2-D4 / R2-D9)."""
    fp = p.footprint
    n = []
    if "2835" in fp:
        n.append("polarity: pad 1 = cathode (the large pad); cathode mark on silk")
    elif "Wuerth" in fp or "RGB" in fp or "ABRG" in p.lib_id:
        n.append("polarity: pad 1 (silk '1') = common anode; the package's polarity mark (chamfer/dot) is pin 3, "
                 "red cathode, and goes on the silk chamfer")
    elif "LED" in fp or p.lib_id.startswith("Device:LED"):
        n.append("polarity: cathode mark to pad 1 (K)")
    elif p.lib_id.startswith(("Device:D", "Device:D_")):
        n.append("polarity: cathode bar to the silk bar (pad 1 = K)")
    if p.ref.startswith(("U", "Q")):
        n.append("check pin-1 / orientation in preview")
    return "; ".join(n)


def _has_features(path):
    """True if a Gerber/Excellon file contains any flash, draw or hit (not just a header)."""
    t = path.read_text(errors="ignore")
    return any(tok in t for tok in ("D03*", "D01*", "D3*", "D1*")) or any(
        line[:1] in ("X", "Y") for line in t.splitlines())


def _natkey(s):
    import re
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]
