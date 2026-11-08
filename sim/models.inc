* sim/models.inc: shared SPICE models for the moon reading light (ngspice 42).
*
* Every value here is either a datasheet figure (docs/datasheets/KEYSPECS.md, cited) or marked PROVISIONAL.
* PROVISIONAL values are estimates until a bench measurement replaces them (docs/verification/VERIFY.md).
* sim/tests/check_models.py checks each model against the datasheet points it was fitted to.

* ---------------------------------------------------------------------------------------------------------------
* P-MOSFET DMG2305UX (Q1-Q4). KEYSPECS: VGS(th) -0.5...-0.9 V, RDS(on) 40/52 mOhm typ/max @ -4.5 V,
* 52/100 mOhm @ -2.5 V, Ciss 808 pF. Level-1 square law: KP 6.6 gives 40 mOhm @ -4.5 V and ~84 mOhm @ -2.5 V
* (between the typ and max). Capacitances split as Cgs 700 pF + Cgd 100 pF (Crss PROVISIONAL, not in KEYSPECS);
* external C5 (Q2) and C8 (Q4) are 100 nF and dominate. The body diode is explicit (drain = anode).
* Pins: D G S (source = the higher-voltage side in normal use).
.subckt DMG2305 d g s vto=-0.7
M1 d g s s PDMG L=1 W=1
Cgs g s 700p
Cgd g d 100p
Cds d s 150p
Dbody d s DBODY
.model PDMG PMOS(LEVEL=1 VTO={vto} KP=6.6 LAMBDA=0.01 IS=1e-18)
* body diode: VSD ~0.65 V @ 0.1 A, ~0.8 V @ 1 A (PROVISIONAL typical silicon body diode)
.model DBODY D(IS=2e-10 N=1.25 RS=0.05 CJO=150p TT=20n)
.ends

* ---------------------------------------------------------------------------------------------------------------
* Bias-dependent MLCC: i = C(v) dv/dt with C(v) = C0 / (1 + (|v|/V0)^n) (small-signal capacitance at bias, which
* is what the manufacturers' DC-bias curves give; integrating it gives the right charge).
* Fits:
*   10u/10V 0603 (LED board C2; Samsung CL10A106KP8 curve in KEYSPECS 10, Murata GRM188R61A106 assumed alike):
*       C0 10.07u V0 2.86 n 1.667 -> 4.84u @3.0, 3.49u @4.2, 2.85u @5.0 (table: 4.84 / 3.49 / 2.85)
*   10u/16V 0805 (main board C1-C4, CL21A106KOQNNNE): C0 10u V0 6.0 n 1.5 -> ~6.3u @4.2 V. PROVISIONAL (no curve in
*       the repo; VERIFY E5 requires >= 4.7u at 4 V)
*   1u/25V 0402 (LED board C1, GRM155R61E105): C0 1u V0 5 n 1.5 -> 0.56u @4.2. PROVISIONAL
*   1u/50V 0603 (main board C7, CL10A105KB8): C0 1u V0 8 n 1.5 -> 0.72u @4.2. PROVISIONAL
* esr: a few mOhm typical for these sizes.
.subckt MLCC a b c0=10u v0=3 nexp=1.5 esr=5m
* linear floor = C at 6 V + the bias-dependent excess. The excess uses a capacitance mirror (a real 1 uF reference
* capacitor sees a copy of the voltage; its current is scaled by dC(v)/1uF), which the integrator handles like any
* capacitor. A ddt() B-source version went unstable on fast edges.
.param cfl={c0/(1+pow(6/v0,nexp))}
Resr a x {esr}
Cfl x b {cfl}
Ecopy cpy 0 x b 1
Vref cpy cr 0
Rref cr cr2 1m
Cref cr2 0 1u
Bc x b I = ({c0} / (1 + pow(abs(V(x,b))/{v0}, {nexp})) - {cfl}) / 1u * I(Vref)
Rleak x b 1e9
.ends

* ---------------------------------------------------------------------------------------------------------------
* LiPo cell + PCM + lead (Pimoroni BAT0004, 1200 mAh). OCV(SoC) is a generic LiCoO2 pouch curve, PROVISIONAL
* until the cell's own discharge curve is measured. rint 0.15 Ohm (cell, PROVISIONAL) + 0.05 Ohm (PCM FETs)
* + lead. State of charge (node soc, 1 V = 100 %) integrates the terminal current.
* Pins: p (cell +, at the JST-PH plug), n.
.subckt LIPO p n soc0=0.5 cap_ah=1.2 rint=0.20 lead_l=150n
* charge drawn (fraction of capacity) integrates on Cdq; gated off at the operating point (time = 0) so the
* initial state is exactly soc0 whatever the load. soc = soc0 - V(dq).
Bdq 0 dq I = (time > 0 ? I(Vsense) : 0) / ({cap_ah} * 3600)
Cdq dq 0 1
Rdq dq 0 1e12
Bsoc soc 0 V = {soc0} - V(dq)
Bocv ocv n V = pwl(V(soc), -0.1,2.80, 0,3.00, 0.02,3.30, 0.05,3.48, 0.10,3.60, 0.15,3.66, 0.20,3.69, 0.30,3.74,
+ 0.40,3.78, 0.50,3.82, 0.60,3.87, 0.70,3.93, 0.80,4.00, 0.90,4.08, 1.00,4.18, 1.10,4.30)
Rint ocv m {rint}
Lw m k {lead_l}
Vsense k p 0
.ends

* ---------------------------------------------------------------------------------------------------------------
* S1J (D3): Vishay S1J, 1 A. VF ~0.85 V @ 0.2 A, ~0.95 V @ 1 A (typical curve; PLAN: ~0.85 V). Fitted N 1.8.
.model DS1J D(IS=2.4e-9 N=1.8 RS=0.03 CJO=10p TT=2u BV=600 IBV=5u)

* SMF5.0A (D1): VBR 6.4-7.0 V @ 10 mA, VC 9.2 V @ 21.7 A (Littelfuse; KEYSPECS 7 notes the PDF was not retrieved).
.model DSMF5 D(IS=1e-12 N=1.0 RS=0.12 BV=6.7 IBV=10m CJO=1.5n)

* ---------------------------------------------------------------------------------------------------------------
* LEDs (KEYSPECS 2, 3). Typical die; *_MAX are the maximum-VF dies.
* Bridgelux Thrive 2835 white: 2.70 V @10 mA, 2.77 @30, 2.85 @50 (Fig. 9). Max die +0.15 V (VF max 3.30 vs typ 3.13
* at 150 mA).
.model DWHITE     D(IS=1.31e-23 N=2.16 RS=1.5 CJO=50p)
.model DWHITE_MAX D(IS=8.93e-25 N=2.16 RS=1.5 CJO=50p)
* Wurth 150141M173100 RGB: red 2.0 typ / 2.4 max @ 20 mA; green/blue 3.2 typ / 3.6 max @ 20 mA, ~+0.09 V @ 25 mA.
.model DRED      D(IS=7.01e-18 N=2.0 RS=8 CJO=30p)
.model DRED_MAX  D(IS=3.06e-21 N=2.0 RS=8 CJO=30p)
.model DGB       D(IS=1.93e-16 N=3.5 RS=14 CJO=30p)
.model DGB_MAX   D(IS=2.32e-18 N=3.5 RS=14 CJO=30p)

* ---------------------------------------------------------------------------------------------------------------
* LP5012 constant-current sink, one channel (KEYSPECS LP5012): ISET 25.0 mA (RIREF 2.94k), VSAT 0.25 typ / 0.35 max
* at 20 mA (current down 5 %). At 25 mA VSAT is unspecified: 0.30 typ / 0.45 max assumed (PROVISIONAL, as in
* electronics.md 2). Shape: I = ISET * duty * tanh(Vout / Vk), Vk = VSAT / 1.83 (tanh(1.83) = 0.95).
* duty is a node (0..1) so PWM can be a voltage source.
.subckt LPSINK out gnd duty iset=25m vsat=0.30
B1 out gnd I = {iset} * max(min(V(duty),1),0) * tanh(max(V(out,gnd),0) / ({vsat}/1.83))
.ends
