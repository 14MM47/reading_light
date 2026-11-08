"""Run one ngspice case variant: template substitution, batch run, .meas parsing, wrdata loading."""
from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SIM = Path(__file__).resolve().parent
OUT = SIM / "out"
DIE = {"typ": {"@WHITE@": "DWHITE", "@RED@": "DRED", "@GB@": "DGB"},
       "max": {"@WHITE@": "DWHITE_MAX", "@RED@": "DRED_MAX", "@GB@": "DGB_MAX"}}
MEAS_RE = re.compile(r"^([a-z_][a-z0-9_]*)\s+=\s+([-+0-9.eE]+)", re.M)


@dataclass
class Result:
    case: str
    variant: str
    meas: dict[str, float]
    data: np.ndarray | None
    cols: list[str]
    log: str
    errors: list[str] = field(default_factory=list)

    def col(self, name: str) -> np.ndarray:
        """wrdata writes (x, y) pairs per vector; column 0 is the sweep variable."""
        assert self.data is not None, f"{self.case}/{self.variant}: no waveform data"
        i = self.cols.index(name)
        return self.data[:, 2 * i + 1]

    @property
    def x(self) -> np.ndarray:
        assert self.data is not None, f"{self.case}/{self.variant}: no waveform data"
        return self.data[:, 0]


def run(case: str, variant: str = "base", params: dict | None = None, die: str = "typ",
        ngspice: str = "ngspice") -> Result:
    """Write out/<case>/<variant>/ with models, boards and the netlist (params overridden), run it, parse it."""
    src = (SIM / "cases" / f"{case}.cir").read_text()
    for k, v in (params or {}).items():
        pat = re.compile(rf"^(\.param\b.*?\b{k}=)(\S+)", re.M)
        if not pat.search(src):
            raise KeyError(f"{case}: no .param {k}")
        src = pat.sub(lambda m: m.group(1) + str(v), src)
    d = OUT / case / variant
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(SIM / "models.inc", d / "models.inc")
    boards = (SIM / "boards.inc").read_text()
    for a, b in DIE[die].items():
        boards = boards.replace(a, b)
    on = lambda k: bool(float(str((params or {}).get(k, 0))))  # noqa: E731
    keep = {"redesign": on("q1gd") or on("sch") or on("usbid"), "usbid": on("usbid"), "nousbid": not on("usbid"),
            "chgsense": case == "charge", "nochgsense": case != "charge"}
    for name, k in keep.items():
        if not k:
            boards = re.sub(rf"^\*>{name}$.*?^\*<{name}$\n", "", boards, flags=re.S | re.M)
    assert "XQ1 " in boards, "block strip removed Q1"
    assert boards.count("Bchg ") == 1, "charger selection wrong"
    assert ("D3 vbus vsysraw" in boards) != on("usbid"), "D3 / USB ideal diode selection wrong"
    (d / "boards.inc").write_text(boards)
    dat = f"{case}.dat"
    (d / f"{case}.cir").write_text(src.replace("@DAT@", dat))
    p = subprocess.run([ngspice, "-b", f"{case}.cir"], cwd=d, capture_output=True, text=True, timeout=1800)
    log = p.stdout + p.stderr
    (d / "ngspice.log").write_text(log)
    meas = {m.group(1): float(m.group(2)) for m in MEAS_RE.finditer(log)}
    errors = [ln for ln in log.splitlines()
              if re.search(r"error|trouble|aborted|singular|failed", ln, re.I) and "measure" not in ln.lower()]
    # measure failures are reported separately (a WHEN that never happens is often the answer, e.g. "never dips")
    errors += [ln.strip() for ln in log.splitlines() if re.search(r"meas.*failed", ln)]
    wr = re.search(r"wrdata\s+@DAT@\s+(.*)", (SIM / "cases" / f"{case}.cir").read_text())
    cols: list[str] = wr.group(1).split() if wr else []
    data = np.loadtxt(d / dat) if (d / dat).exists() and (d / dat).stat().st_size else None
    if data is not None and data.ndim == 1:
        data = data[None, :]
    return Result(case, variant, meas, data, cols, log, errors)


def cross(t: np.ndarray, y: np.ndarray, level: float, after: float = 0.0) -> float:
    """First rising crossing of `level` at or after `after`, linearly interpolated."""
    i0 = int(np.searchsorted(t, after))
    idx = np.nonzero((y[i0:-1] < level) & (y[i0 + 1:] >= level))[0]
    if not len(idx):
        return float("nan")
    i = i0 + int(idx[0])
    return float(t[i] + (level - y[i]) * (t[i + 1] - t[i]) / (y[i + 1] - y[i]))
