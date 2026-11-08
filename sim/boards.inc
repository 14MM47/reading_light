* sim/boards.inc: the two boards as SPICE subcircuits, from hardware/main-board/design.py and
* hardware/led-board/design.py (reference designators kept). Needs models.inc.
*
* Simplifications (all stated in the report):
*  - MCU (ATtiny3216) = 2.5 mA constant above 1.8 V (PROVISIONAL; awake, 1 ms ticks). BOD 2.6 V is checked by
*    measurement, not modelled.
*  - MCP73831 = behavioural CC/CV source: 10 % precharge below V_PTH 2.79 V, I_REG 256 mA, CV 4.20 V, pass FET
*    0.35 Ohm, off below VDD 3.75 V (operating minimum). Termination (7.5 % = 31 mA) is read off the plot, not
*    modelled. 0.5 mA quiescent, ~3 mA charge LED (R4 1k + D2) while charging.
*  - F1 PTC = its cold resistance (param rptc, 0.06-0.20 Ohm); tripping is thermal (seconds) and out of scope.
*  - Slide switch SW1 and the MCU pin PB2 are ideal drivers behind 1 Ohm / 25 Ohm; control inputs are 0/1 V nodes.

* ===============================================================================================================
* Main board power path.  Ports:
*   vbusin  USB-C VBUS (after the cable)       batraw  cell + (J2 pin 1)       vsys  VSYS (MCU rail, TP3)
*   vled    VLED (J3 pin 2, main-board side)    swon    1 = slide switch ON      ledon 1 = PB2 low (Q4 on)
*   vbus vsysraw bat: internal nodes brought out for probing
.subckt MAINPWR vbusin batraw vsys vled swon ledon vbus vsysraw bat rptc=0.12 vto=-0.7 r5=10k cbulk=1p
+ q1gd=0 rq1pd=100k sch=0 vdet=4.3 ron_id=0.08
* --- A: USB input, TVS, charger
RF1 vbusin vbus {rptc}
D1 0 vbus DSMF5
XC1 vbus 0 MLCC c0=10u v0=6 nexp=1.5
R5 vbus 0 {r5}
*>chgsense
* charge case only: the charger output current is sensed by Vchg (the MCP73831 terminates on this, not on
* the cell current); sim/spice.py keeps this block for the charge case and the plain one for every other case
Bchg vbus chgo I = 0.5*(1+tanh((V(vbus)-3.75)/0.03)) * max(0, min( min( (V(bat) < 2.79 ? 0.0256 : 0.256),
+   (4.20 - V(bat))/0.02), (V(vbus) - V(bat))/0.35 ))
Vchg chgo bat 0
*<chgsense
*>nochgsense
Bchg vbus bat I = 0.5*(1+tanh((V(vbus)-3.75)/0.03)) * max(0, min( min( (V(bat) < 2.79 ? 0.0256 : 0.256),
+   (4.20 - V(bat))/0.02), (V(vbus) - V(bat))/0.35 ))
*<nochgsense

Biq vbus 0 I = 0.5*(1+tanh((V(vbus)-3.75)/0.03)) * (0.5m + (V(bat) < 4.15 ? 3m : 0))
XC2 bat 0 MLCC c0=10u v0=6 nexp=1.5
* --- B: reverse-battery FET Q3 (G = R10 to GND, S = BAT, D = BAT_RAW), load share Q1 (G = VBUS, S = VSYS_RAW,
*        D = BAT), D3 S1J VBUS -> VSYS_RAW, C3, power switch Q2 (G = SW_GATE, S = VSYS_RAW, D = VSYS), C4
XQ3 batraw q3g bat DMG2305 vto={vto}
R10 q3g 0 10k
* Q1. As built: gate on VBUS. The redesign options for decision D1 (q1gd = 1, 2, 3 and sch = 1) sit between
* the two redesign marker lines below; sim/spice.py strips that block unless a variant sets q1gd or sch, so the
* as-built netlist is exactly the board.
Rq1link vbus q1g {q1gd > 0.5 ? 1e9 : 1m}
XQ1 q1d q1g vsysraw DMG2305 vto={vto}
Rq1d bat q1d {q1gd > 2.5 ? 1e9 : 1m}
*>redesign
* q1gd=1: gate fed from VBUS through a small Schottky (BAT54-class) with its own pull-down rq1pd.
Dq1g vbus q1gd1 DBAT54
Rq1gd1 q1gd1 q1g {abs(q1gd - 1) < 0.5 ? 1m : 1e9}
Rq1pd q1g 0 {abs(q1gd - 1) < 0.5 ? rq1pd : 1e9}
* q1gd=2: a VBUS voltage detector (behavioural stand-in for a supervisor IC, threshold vdet, 100 mV hysteresis)
* drives the gate: gate = VBUS while VBUS is good, 0 V once VBUS falls below vdet.
Bdet det 0 V = V(vbus) > ({vdet} + 0.1*V(detst)) ? V(vbus) : 0
Bdetst detst 0 V = V(det) > 1 ? 0 : 1
Rdet det q1g {q1gd > 1.5 ? 10k : 1e9}
* q1gd=3: Q1 replaced by a reverse-blocking ideal diode (LM66100-class: ~80 mOhm switch + near-ideal diode),
* enabled while VBUS < ~4.35 V (smooth step), ~20 us enable response.
Bidraw iden_r 0 V = 0.5*(1 - tanh((V(vbus) - {vdet} - 0.05)/0.02))
Rid iden_r iden 20k
Cid iden 0 1n
Sid bat idm iden 0 SIDEAL
.model SIDEAL SW(VT=0.5 VH=0.05 RON={ron_id} ROFF=1e9)
Did idm idk DIDEAL
Rid_en idk vsysraw {abs(q1gd - 3) < 0.5 ? 1m : 1e9}
.model DIDEAL D(IS=1e-6 N=0.1 RS=0)
* q1gd=4: TI LM66100 in place of Q1 (SLVSEZ8A): VIN = BAT, VOUT = VSYS_RAW, CE = VBUS (TI's OR-ing circuit).
* Datasheet figures: RON 91 mOhm typ at 3.6 V; body diode ~0.5 V typ (VIN -> VOUT); CE comparator against VIN:
* on when CE < VIN - 150 mV, off when CE > VIN + 35 mV; turn-on 40 us, turn-off 2 us; conducts both ways when on.
Blmst lmst 0 V = (V(bat) - V(vbus) > (V(lmen) > 0.5 ? -0.035 : 0.15)) ? 1 : 0
Rlmon lmst lmen 40k
Clmen lmen 0 1n
Dlmoff lmen lmoffk DIDEAL
Rlmoff lmoffk lmst 2k
* switch: 8 parallel stages (8 x 0.728 Ohm = 91 mOhm) closing at staggered enable levels, so the on-resistance
* ramps as the enable node rises (~40 us) instead of switching in one step; off in ~2 us
Slm0 bat lmo lmen 0 SLM0
.model SLM0 SW(VT=0.1 VH=0.02 RON=0.728 ROFF=1e10)
Slm1 bat lmo lmen 0 SLM1
.model SLM1 SW(VT=0.2 VH=0.02 RON=0.728 ROFF=1e10)
Slm2 bat lmo lmen 0 SLM2
.model SLM2 SW(VT=0.3 VH=0.02 RON=0.728 ROFF=1e10)
Slm3 bat lmo lmen 0 SLM3
.model SLM3 SW(VT=0.4 VH=0.02 RON=0.728 ROFF=1e10)
Slm4 bat lmo lmen 0 SLM4
.model SLM4 SW(VT=0.5 VH=0.02 RON=0.728 ROFF=1e10)
Slm5 bat lmo lmen 0 SLM5
.model SLM5 SW(VT=0.6 VH=0.02 RON=0.728 ROFF=1e10)
Slm6 bat lmo lmen 0 SLM6
.model SLM6 SW(VT=0.7 VH=0.02 RON=0.728 ROFF=1e10)
Slm7 bat lmo lmen 0 SLM7
.model SLM7 SW(VT=0.8 VH=0.02 RON=0.728 ROFF=1e10)
Rlmo lmo vsysraw {abs(q1gd - 4) < 0.5 ? 1m : 1e9}
Dlmbd bat lmbd DLMBODY
Rlmbd lmbd vsysraw {abs(q1gd - 4) < 0.5 ? 1m : 1e9}
.model DLMBODY D(IS=7.4e-9 N=1.25 RS=0.05)
* sch=1: a 1 A Schottky across Q1 (anode BAT, cathode VSYS_RAW)
Rsch bat schA {sch > 0.5 ? 1m : 1e9}
Dsch schA vsysraw DSCH1A
*<redesign
*>nousbid
D3 vbus vsysraw DS1J
*<nousbid
*>usbid
* usbid=1 (redesign): D3 replaced by a second reverse-blocking ideal diode, always enabled (ron_id)
Sud vbus udm uen 0 SIDEAL
Vuen uen 0 1
Dud udm vsysraw DIDEAL
*<usbid
XC3 vsysraw 0 MLCC c0=10u v0=6 nexp=1.5
XQ2 vsys swgate vsysraw DMG2305 vto={vto}
R6 vsysraw swgate 1Meg
C5 vsysraw swgate 100n
R7 swgate swcom 10k
* SW1 (PCM12): COM to GND when ON, to VSYS_RAW when OFF
Bsw swcom_i 0 V = V(swon) > 0.5 ? 0 : V(vsysraw)
Rsw swcom_i swcom 1
XC4 vsys 0 MLCC c0=10u v0=6 nexp=1.5
* optional bulk capacitor on VSYS (VERIFY E13 remedy: 47 uF), ESR 0.1 Ohm (tantalum/polymer, PROVISIONAL)
Rbulk vsys nbulk 0.1
Cbulk nbulk 0 {cbulk}
* --- C: MCU decoupling and load
C6 vsys 0 100n
XC7 vsys 0 MLCC c0=1u v0=8 nexp=1.5
Bmcu vsys 0 I = 2.5m * 0.5*(1+tanh((V(vsys)-1.8)/0.05))
* --- D: LED-board switch Q4 (G = Q4_G, S = VSYS, D = VLED), R12 100k pull-up, R13 10k from PB2, C8 100n G-D
XQ4 vled q4g vsys DMG2305 vto={vto}
R12 vsys q4g 100k
Bpb2 pb2_i 0 V = V(ledon) > 0.5 ? 0 : V(vsys)
Rpb2 pb2_i pb2 25
R13 pb2 q4g 10k
C8 q4g vled 100n
.ends

* ===============================================================================================================
* Neck cable: J3 (JST-SH) + 2 x 200 mm 28 AWG + J1 pads on the LED board. 28 AWG 0.213 Ohm/m -> 43 mOhm per
* conductor, + 2 x 20 mOhm contacts (PROVISIONAL), loop inductance ~0.15 uH (PROVISIONAL, 200 mm pair inside the
* metal gooseneck).  Ports: main-side VLED, main-side GND, board-side VLED, board-side GND.
.subckt CABLE vm gm vb gb rc=0.063 lc=75n
Rv vm v1 {rc}
Lv v1 vb {lc}
Rg gb g1 {rc}
Lg g1 gm {lc}
.ends

* ===============================================================================================================
* LED board v0.2.  Ports: vled gnd (board side of the cable), dw dr dg db (duty 0..1 of the white, red, green and
* blue channels; the 8 whites share dw).  params: iq = LP5012 active supply current (4-10 mA, VERIFY E7);
* vsat = LP5012 VSAT at 25 mA. @WHITE@ @RED@ @GB@ are replaced by the runner with the typical or maximum-VF models.
.subckt LEDBOARD vled gnd dw dr dg db iq=6.8m vsat=0.30
XC2 vled gnd MLCC c0=10.07u v0=2.86 nexp=1.667
XC1 vled gnd MLCC c0=1u v0=5 nexp=1.5
C3 vled gnd 100n
* LP5012 supply: active above its 2.5 V restart, ~10 uA below; MCP9800 0.2 mA above 1.7 V
Blp vled gnd I = 10u*tanh(max(V(vled,gnd),0)/0.3) + {iq} * 0.5*(1+tanh((V(vled,gnd)-2.5)/0.05))
* an unpowered board is a 1 MOhm-ish load, not a floating node
Rbl vled gnd 1Meg
Bts vled gnd I = 0.2m * 0.5*(1+tanh((V(vled,gnd)-1.7)/0.05))
* 8 whites (4 x 2700 K + 4 x 5000 K; same VF model) on one duty node
D1 vled k1 @WHITE@
X1 k1 gnd dw vled LPSINK2 vsat={vsat}
D2 vled k2 @WHITE@
X2 k2 gnd dw vled LPSINK2 vsat={vsat}
D3 vled k3 @WHITE@
X3 k3 gnd dw vled LPSINK2 vsat={vsat}
D4 vled k4 @WHITE@
X4 k4 gnd dw vled LPSINK2 vsat={vsat}
D5 vled k5 @WHITE@
X5 k5 gnd dw vled LPSINK2 vsat={vsat}
D6 vled k6 @WHITE@
X6 k6 gnd dw vled LPSINK2 vsat={vsat}
D7 vled k7 @WHITE@
X7 k7 gnd dw vled LPSINK2 vsat={vsat}
D8 vled k8 @WHITE@
X8 k8 gnd dw vled LPSINK2 vsat={vsat}
* RGB (D9, common anode)
D9R vled kr @RED@
XR kr gnd dr vled LPSINK2 vsat={vsat}
D9G vled kg @GB@
XG kg gnd dg vled LPSINK2 vsat={vsat}
D9B vled kb @GB@
XB kb gnd db vled LPSINK2 vsat={vsat}
.ends

* LP5012 sink with the chip's UVLO: outputs only run with VCC above ~2.5 V.
.subckt LPSINK2 out gnd duty vcc iset=25m vsat=0.30
B1 out gnd I = {iset} * max(min(V(duty),1),0) * tanh(max(V(out,gnd),0) / ({vsat}/1.83))
+ * 0.5*(1+tanh((V(vcc,gnd)-2.5)/0.05))
.ends
