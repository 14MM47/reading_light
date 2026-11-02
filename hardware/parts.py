"""Parts catalogue: one entry per orderable part. Every board and the BOM/order list read from here.

Farnell UK order codes were taken from Farnell product URLs (verified code) during sourcing on
2026-11-02; prices are indicative (cached pages) and must be re-checked at order time. `alt` lists a
drop-in alternative where one was identified.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Cat:
    key: str
    value: str
    mpn: str
    mfr: str
    farnell: str
    footprint: str
    desc: str
    datasheet: str = ""
    unit_gbp: float = 0.0          # indicative ex-VAT unit price at the order quantity
    moq: int = 1                   # Farnell minimum / multiple
    alt: str = ""
    lcsc: str = ""                 # for JLCPCB assembly route (fill/verify at quote time)


R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"

CAT = {c.key: c for c in [
    # ---------------------------------------------------------------- ICs
    Cat("MCU", "ATtiny3216-SN", "ATTINY3216-SN", "Microchip", "3018703", "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
        "8-bit AVR MCU, 32 KB flash, 256 B EEPROM, UPDI, 1.8-5.5 V, SOIC-20 (300 mil)",
        "https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/ATtiny3216-17-DataSheet-DS40002205A.pdf",
        1.04, alt="ATTINY1616-SFR (Farnell 2920834)"),
    Cat("CHG", "MCP73831-2ACI/OT", "MCP73831T-2ACI/OT", "Microchip", "1332158", "Package_TO_SOT_SMD:SOT-23-5",
        "Li-ion/LiPo linear charger 4.20 V, up to 500 mA, SOT-23-5",
        "https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP73831-Family-Data-Sheet-DS20001984H.pdf",
        0.59),
    Cat("LEDDRV", "TLC59116IPWR", "TLC59116IPWR", "Texas Instruments", "3119169", "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm",
        "16-ch I2C constant-current LED sink driver, 97 kHz PWM, TSSOP-28",
        "https://www.ti.com/lit/ds/symlink/tlc59116.pdf", 1.89),
    Cat("TEMP", "LM75BDP", "LM75BDP,118", "NXP", "", "Package_SO:TSSOP-8_3x3mm_P0.65mm",
        "I2C digital temperature sensor, +/-2 C, 2.8-5.5 V, TSSOP-8 (same die/pinout as LM75BD SOIC-8)",
        "https://www.nxp.com/docs/en/data-sheet/LM75B.pdf", 0.55, moq=5,
        alt="LM75BD,118 SOIC-8 (Farnell 2841138) does not fit the 24 mm LED board"),
    # --------------------------------------------------------- discretes
    Cat("PFET", "DMG2305UX", "DMG2305UX-7", "Diodes Inc", "2543533", "Package_TO_SOT_SMD:SOT-23",
        "P-MOSFET -20 V -4.2 A, Rds(on) 52 mOhm @ -4.5 V (max), SOT-23 (G=1 S=2 D=3)",
        "https://www.diodes.com/assets/Datasheets/DMG2305UX.pdf", 0.30),
    Cat("SCHOTTKY", "MBR120VLSFT1G", "MBR120VLSFT1G", "onsemi", "1431044", "Diode_SMD:D_SOD-123F",
        "Schottky 20 V 1 A, Vf 0.315 V max @ 0.5 A, SOD-123FL. NOT USED: IR up to 0.6 mA @25 C would drain the cell "
        "while switched off (see decision log 2026-11-02)",
        "https://www.onsemi.com/download/data-sheet/pdf/mbr120vlsft1-d.pdf", 0.35, moq=5),
    Cat("RECT", "S1J", "S1J-E3/61T", "Vishay", "", "Diode_SMD:D_SMA",
        "Silicon rectifier 1 A 600 V, SMA (DO-214AC); Vf ~0.85 V @ 0.3 A; leakage nA at 4 V reverse (USB -> VSYS OR-ing)",
        "https://www.vishay.com/docs/88711/s1a.pdf", 0.12, moq=5),
    Cat("TVS", "SMF5.0A", "SMF5.0A", "Littelfuse", "2691565", "Diode_SMD:D_SOD-123F",
        "TVS unidirectional 5.0 V standoff, 200 W, SOD-123FL",
        "https://www.littelfuse.com/products/tvs-diodes/surface-mount/smf.aspx", 0.15, moq=5),
    Cat("LED_RED_0603", "red", "APT1608SURCK", "Kingbright", "", "LED_SMD:LED_0603_1608Metric",
        "Hyper-red chip LED 0603, 230 mcd @ 20 mA, pin 1 = K (charge indicator, ~3 mA)",
        "https://www.kingbrightusa.com/images/catalog/SPEC/APT1608SURCK.pdf", 0.15),
    # ------------------------------------------------------------- LEDs
    Cat("LED_WW", "2700K CRI97", "BXEN-27S-11M-3C-00-0-3", "Bridgelux", "3498849", "LED_SMD:LED_PLCC_2835",
        "Mid-power white LED 2835, 2700 K, CRI 97 (Thrive), 3 V class", "", 0.10),
    Cat("LED_CW", "5000K CRI97", "BXEN-50S-11M-3C-00-0-3", "Bridgelux", "3498853", "LED_SMD:LED_PLCC_2835",
        "Mid-power white LED 2835, 5000 K, CRI 97 (Thrive), 3 V class", "", 0.18,
        alt="BXEN-65S-11M-3C-00-0-3 (6500 K) if a UK source appears"),
    Cat("LED_RGB", "RGB 3528 CA", "150141M173100", "Wurth Elektronik", "2322115",
        "LED_SMD:LED_RGB_Wuerth-PLCC4_3.2x2.8mm_150141M173100",
        "RGB LED PLCC-4 3528, common anode (1 A, 2 B-K, 3 R-K, 4 G-K), 30 mA max/die, R 625 / G 520 / B 470 nm",
        "https://www.we-online.com/components/products/datasheet/150141M173100.pdf", 0.44,
        alt="Kingbright KAAF-5050RGBS-13 (Farnell 2335791) - datasheet not obtained, pinout unverified"),
    # ----------------------------------------------------- electromech
    Cat("USBC", "USB4125-GF-A", "USB4125-GF-A", "GCT", "3648642",
        "Connector_USB:USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal",
        "USB-C receptacle, 6-pin power only, top mount, SMT + THT shell", "https://gct.co/files/drawings/usb4125.pdf", 0.59),
    Cat("TACT", "PTS645SM43SMTR92", "PTS645SM43SMTR92 LFS", "C&K", "3941596", "Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92",
        "Tactile switch 6x6x4.3 mm SMD, 160 gf", "", 0.19, moq=10),
    Cat("SLIDE", "PCM12SMTR", "PCM12SMTR", "C&K", "9575146", "Button_Switch_SMD:SW_SPDT_PCM12",
        "Mini slide switch SPDT, right-angle SMD (side actuated)", "", 0.85),
    Cat("JST_PH2", "S2B-PH-SM4-TB", "S2B-PH-SM4-TB(LF)(SN)", "JST", "9492615",
        "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
        "JST PH 2-pin side-entry SMD header (battery)", "", 0.48, moq=10),
    Cat("JST_SH4", "SM04B-SRSS-TB", "SM04B-SRSS-TB(LF)(SN)", "JST", "1830839",
        "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
        "JST SH 4-pin side-entry SMD header (Qwiic pinout, moon cable)", "", 0.45),
    # ---------------------------------------------------------- passives
    Cat("R_5K1", "5.1k", "MCWR06X5101FTL", "Multicomp Pro", "", R0603, "Resistor 5.1 kOhm 1% 0603", unit_gbp=0.01, moq=50),
    Cat("R_2K4", "2.4k", "MCWR06X2401FTL", "Multicomp Pro", "", R0603, "Resistor 2.4 kOhm 1% 0603 (charge current)", unit_gbp=0.01, moq=50),
    Cat("R_1K", "1k", "MCWR06X1001FTL", "Multicomp Pro", "", R0603, "Resistor 1 kOhm 1% 0603", unit_gbp=0.01, moq=50),
    Cat("R_10K", "10k", "MCWR06X1002FTL", "Multicomp Pro", "2447230", R0603, "Resistor 10 kOhm 1% 0603", unit_gbp=0.01, moq=50),
    Cat("R_100K", "100k", "MCWR06X1003FTL", "Multicomp Pro", "", R0603, "Resistor 100 kOhm 1% 0603", unit_gbp=0.01, moq=50),
    Cat("R_1M", "1M", "MCWR06X1004FTL", "Multicomp Pro", "", R0603, "Resistor 1 MOhm 1% 0603", unit_gbp=0.01, moq=50),
    Cat("R_3K3", "3.3k", "MCWR06X3301FTL", "Multicomp Pro", "", R0603, "Resistor 3.3 kOhm 1% 0603 (I2C pull-up)", unit_gbp=0.01, moq=50),
    Cat("R_750", "750", "MCWR06X7500FTL", "Multicomp Pro", "", R0603, "Resistor 750 Ohm 1% 0603 (TLC59116 REXT: 25.0 mA/channel)", unit_gbp=0.01, moq=50),
    Cat("C_100N", "100n", "MC0603B104K500CT", "Multicomp Pro", "1759122", C0603, "MLCC 100 nF 50 V X7R 0603", unit_gbp=0.01, moq=50),
    Cat("C_1U", "1u", "CL10A105KB8NNNC", "Samsung", "3013385", C0603, "MLCC 1 uF 50 V X5R 0603", unit_gbp=0.03, moq=10),
    Cat("C_4U7", "4.7u 16V", "CL10A475KO8NNNC", "Samsung", "3013398", C0603, "MLCC 4.7 uF 16 V X5R 0603", unit_gbp=0.04, moq=10),
    Cat("C_10U", "10u 16V 0805", "CL21A106KOQNNNE", "Samsung", "", "Capacitor_SMD:C_0805_2012Metric",
        "MLCC 10 uF 16 V X5R 0805 (0603 10 V part keeps only 2.9 uF at 5 V)", unit_gbp=0.08, moq=10),
]}

# Parts with an empty `farnell` code: the Multicomp Pro MCWR06X series MPN follows the 10k part that was seen
# (MCWR06X1002FTL = 2447230); look these up by MPN in Farnell's BOM upload / search at order time.
