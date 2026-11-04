# 06: Test and verification

- **`VERIFY-bench-checklist.pdf`** (also `.md`, for recording results): every value nobody has measured yet, with
  how to check it, the pass band, and the action if it fails. It covers electrical (E1–E17), firmware bring-up
  (F1–F6), thermal (T1–T7; bench-only firmware in `04-firmware/bench-only/`), optics and colour (O1–O7) and
  mechanical fit (M1–M14).
- `verification-round{1,2,3}-dispositions.pdf`: every reviewer finding and what was done about it (fixed,
  mitigated, accepted, VERIFY, or Matt's decision). Round 3 reviewed the v0.2 LED board, its firmware and the slim
  moon head.
- `reviewer-reports/`: the nine full reviewer reports (round 1 electrical, adversarial, firmware, thermal/optical;
  round 2 electrical/firmware and DFM/fit; round 3 electrical/firmware, mechanical/optics and docs consistency),
  with datasheet references.

Record the measured values in the repo's `docs/verification/VERIFY.md` (not in this generated folder), and raise
anything outside its pass band before the second lamp is built.
