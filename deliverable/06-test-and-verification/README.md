# 06: Test and verification

- **`VERIFY-bench-checklist.pdf`** (also `.md`, for recording results): every value nobody has measured yet, with
  how to check it, the pass band, and the action if it fails. It covers electrical (E1–E15), firmware bring-up
  (F1–F6), thermal (T1–T7; bench-only firmware in `04-firmware/bench-only/`), optics and colour (O1–O7) and
  mechanical fit (M1–M14).
- `verification-round1-dispositions.pdf`, `verification-round2-dispositions.pdf`: every reviewer finding and what
  was done about it (fixed, mitigated, accepted, VERIFY, or Matt's decision).
- `reviewer-reports/`: the six full reviewer reports (electrical, adversarial, firmware, thermal/optical; round 2
  electrical/firmware and DFM/fit), with datasheet references.

Record the measured values in the repo's `docs/verification/VERIFY.md` (not in this generated folder), and raise
anything outside its pass band before the second lamp is built.
