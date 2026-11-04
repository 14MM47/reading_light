"""PCB stage: place footprints from design.PLACE, outline, rules, route (kigen.router), pours, DRC."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import pcbnew

from kigen.board import Board
from kigen.router import Router, RouteError, stitch_grid

HW = Path(__file__).resolve().parent
LIBFP = HW / "lib" / "reading_light.pretty"


def _footprint_lib_path(fpid: str):
    lib, name = fpid.split(":", 1)
    if lib == "reading_light":
        return str(LIBFP), name
    return f"/usr/share/kicad/footprints/{lib}.pretty", name


def build_pcb(board: str, d, parts, attempts=12):
    """Greedy routing with retries: failed nets move to the front; the rest rotate so other orders get tried.
    Keeps the best order and rebuilds it last so the saved board is the best one found."""
    import random
    rng = random.Random(7)
    order = list(d.ROUTE)
    best = None
    optional = {r[0] for r in d.ROUTE if len(r) > 2 and r[2].get("optional")}
    for k in range(attempts):
        report = _build_once(board, d, parts, order)
        # an optional net (e.g. GND under a pour) may fail its track tree as long as DRC finds nothing unconnected
        nf = len([n for n in report["failed"] if n not in optional or report["drc"]["unconnected"]])
        if best is None or nf < best[0]:
            best = (nf, list(order))
        if nf == 0:
            return report
        failed = set(report["failed"])
        print(f"  attempt {k + 1}: {nf} nets failed, retrying with them first")
        rest = [r for r in order if r[0] not in failed]
        if k % 2 == 1:
            rng.shuffle(rest)
        order = [r for r in order if r[0] in failed] + rest
    if best[1] != order:
        report = _build_once(board, d, parts, best[1])
    return report


def _build_once(board: str, d, parts, order):
    bdir = HW / board
    B = Board(d.PROJECT, getattr(d, "RULES", {}))
    import kigen.board as kb
    orig = pcbnew.FootprintLoad

    def load(libdir, name):                       # route project footprints to hardware/lib/*.pretty
        if libdir.endswith("reading_light.pretty"):
            return orig(str(LIBFP), name)
        return orig(libdir, name)
    kb.pcbnew.FootprintLoad = load
    for nc in getattr(d, "NETCLASSES", []):
        B.netclass(**nc)
    # title block: reaches the Gerber job file, the drawings and the assembly PDFs (round2 R2-D23)
    tb = B.b.GetTitleBlock()
    tb.SetTitle(getattr(d, "TITLE", d.PROJECT))
    tb.SetRevision(getattr(d, "REV", ""))
    tb.SetDate(getattr(d, "DATE", "2026-11-02"))
    tb.SetCompany("Moon reading light (14MM47/reading_light)")
    # board thickness goes into the STEP model and the fab notes (electrical review N9: the LED board is 1.0 mm)
    B.b.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(getattr(d, "BOARD_THICKNESS", 1.6)))
    # outline
    o = d.OUTLINE
    if o[0] == "circle":
        B.outline_circle(o[1], o[2], o[3])
    else:
        B.outline_poly(o[1])
    byref = {p.ref: p for p in parts}
    for ref, (x, y, rot, side) in d.PLACE.items():
        p = byref[ref]
        fp_lib = p.footprint.split(":", 1)[0]
        if fp_lib == "reading_light":
            p_fp = p.footprint.replace("reading_light:", "reading_light:")
        B.place(p, x, y, rot, side, getattr(d, "PAD_MAP", {}).get(ref))
    missing = [p.ref for p in parts if p.on_board and p.ref not in d.PLACE]
    if missing:
        raise SystemExit(f"unplaced parts: {missing}")
    for h in getattr(d, "HOLES", []):
        B.hole(*h)
    for (x, y) in getattr(d, "MOUNT_HOLES", []):
        B.hole(x, y, 2.2)                                   # M2 clearance, NPTH
        B.keepout("FB", [(x + 2.6 * math.cos(a * math.pi / 8), y + 2.6 * math.sin(a * math.pi / 8)) for a in range(16)])
    for sl in getattr(d, "SLOTS", []):
        B.slot(*sl)
    for k in getattr(d, "KEEPOUTS", []):
        B.keepout(**k)
    for t in getattr(d, "SILK", []):
        B.text(**t)
    # pre-routed copper (fixed tracks/vias the design wants exactly)
    for tr in getattr(d, "TRACKS", []):
        B.track(**tr)
    for v in getattr(d, "VIAS", []):
        B.via(**v)
    # route
    R = Router(B.b, grid=getattr(d, "ROUTE_GRID", 0.05), clearance=d.RULES.get("clearance", 0.2) + 0.03,
               edge_clear=d.RULES.get("edge_clear", 0.3) + 0.05, align=getattr(d, "ROUTE_ALIGN", None))
    report = {"routed": [], "failed": []}
    for net, layer in getattr(d, "PRE_STITCH", []):
        n = R.stitch_pads(net, layer=layer, width=0.3, max_mm=2.0,
                          skip_connected=getattr(d, "STITCH_SKIP_CONNECTED", False))
        print(f"  pre-stitched {n} {net} pads")
    base_kw = getattr(d, "ROUTE_OPTS", {})
    for net, width, *opt in order:
        kw = dict(base_kw, **(opt[0] if opt else {}))
        kw.pop("optional", None)
        done = False
        for w in [width] + [x for x in (0.4, 0.3, 0.25, 0.2) if x < width]:
            try:
                R.route_net(net, w, **kw)
                report["routed"].append([net, w])
                print(f"  routed {net} @ {w} mm")
                done = True
                break
            except RouteError as e:
                last = e
        if not done:
            report["failed"].append(net)
            print(f"  FAILED {net}: {last}")
    for net, layer in getattr(d, "STITCH", []):
        n = R.stitch_pads(net, layer=layer)
        print(f"  stitched {n} {net} pads")
    for net, pitch in getattr(d, "STITCH_GRID", []):
        print(f"  stitch grid: {stitch_grid(R, net, pitch)} {net} vias")
    for z in d.ZONES:
        B.zone(**z)
    o = d.OUTLINE
    # round board: keep silk inside the part-free radius (the LED board edge band is clamped by the moon ring)
    fab_refs = B.place_refs(circle=(o[1], o[2], getattr(d, "SILK_R_MAX", o[3] - 0.5)) if o[0] == "circle" else None)
    if fab_refs:
        print(f"  refs moved to Fab (no room on silk): {fab_refs}")
    pcb = bdir / f"{d.PROJECT}.kicad_pcb"
    B.save(str(pcb))
    if getattr(d, "CUSTOM_RULES", None):           # project .kicad_dru: rules the board setup cannot express
        (bdir / f"{d.PROJECT}.kicad_dru").write_text(d.CUSTOM_RULES)
    drc = run_drc(bdir, d.PROJECT)
    report["drc"] = drc
    (bdir / "reports" / "route.json").write_text(json.dumps(report, indent=1))
    return report


def run_drc(bdir: Path, project: str):
    out = bdir / "reports" / "drc.json"
    subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--schematic-parity", "--severity-all",
                    "-o", str(out), str(bdir / f"{project}.kicad_pcb")], capture_output=True, text=True)
    d = json.loads(out.read_text())
    viol = d.get("violations", [])
    unc = d.get("unconnected_items", [])
    par = d.get("schematic_parity", [])
    for v in viol:
        print(f"  DRC {v['severity']:<8} {v['type']}: {v['description'][:80]} {[i['description'][:50] for i in v['items']][:2]}")
    for v in unc:
        print(f"  UNCONNECTED {[i['description'][:60] for i in v['items']]}")
    for v in par:
        print(f"  PARITY {v['type']}: {v['description'][:90]}")
    print(f"DRC: {len(viol)} violations, {len(unc)} unconnected, {len(par)} parity")
    return {"violations": len(viol), "errors": sum(v["severity"] == "error" for v in viol),
            "unconnected": len(unc), "parity": len(par)}
