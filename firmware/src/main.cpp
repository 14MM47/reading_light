// Moon reading light firmware - ATtiny3216 (megaTinyCore / PlatformIO).
// Hardware glue only; behaviour lives in lib/core/lightcore.cpp (host unit-tested).
#include <Arduino.h>
#include <EEPROM.h>
#include <Wire.h>
#include <avr/sleep.h>

#include "config.h"
#include "lightcore.h"

static core_t core;
static uint8_t lp_b = 0;                           // LEDx_BRIGHTNESS in use (0 = unknown, forces a full write)
static uint8_t last_regs[4 + N_OUT];              // 07h..16h as last written: 4 x brightness, N_OUT x colour
static bool lp_ok = false;
static uint8_t lp_fails = 0;
static float last_temp_c = 25.0f;

// -------------------------------------------------------------------- LP5012
// Registers (SLVSEH2B): 00h DEVICE_CONFIG0 (b6 Chip_EN), 01h DEVICE_CONFIG1, 02h LED_CONFIG0 (bank control),
// 07h-0Ah LED0..3_BRIGHTNESS (each covers OUT 3k..3k+2), 0Bh-16h OUT0..11_COLOR, 17h RESET (write FFh).
#define LP_DEVICE_CONFIG0 0x00
#define LP_DEVICE_CONFIG1 0x01
#define LP_LED_CONFIG0    0x02
#define LP_BRIGHTNESS0    0x07
#define LP_COLOR0         0x0B
#define LP_RESET          0x17
#define LP_CHIP_EN        0x40
// Log_Scale_EN 0 (the core already maps levels geometrically), Power_Save_EN 1, Auto_Incr_EN 1,
// PWM_Dithering_EN 1, Max_Current_Option 0 (IMAX 25.5 mA), LED_Global_Off 0
#define LP_CONFIG1        0x1C

static bool lp_write(uint8_t reg, const uint8_t *d, uint8_t n) {   // auto-increment (CONFIG1 b3) for n > 1
    Wire.beginTransmission(ADDR_LP5012);
    Wire.write(reg);
    for (uint8_t i = 0; i < n; i++) Wire.write(d[i]);
    return Wire.endTransmission() == 0;
}

static int16_t lp_read(uint8_t reg) {            // -1 on bus error
    Wire.beginTransmission(ADDR_LP5012);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) return -1;
    if (Wire.requestFrom((uint8_t)ADDR_LP5012, (uint8_t)1) != 1) return -1;
    return (int16_t)Wire.read();
}

static bool lp_init() {
    // EN high (R2 pull-up, ALERT released) for > 500 us before the first access (tEN_H): led_board_on() waits 10 ms
    const uint8_t en = LP_CHIP_EN, cfg1 = LP_CONFIG1, bank = 0x00;
    bool ok = lp_write(LP_DEVICE_CONFIG0, &en, 1);            // STANDBY -> NORMAL
    ok &= lp_write(LP_DEVICE_CONFIG1, &cfg1, 1);
    ok &= lp_write(LP_LED_CONFIG0, &bank, 1);                 // no bank control: every output on its own colour
    memset(last_regs, 0, sizeof(last_regs));
    ok &= lp_write(LP_BRIGHTNESS0, last_regs, sizeof(last_regs));   // all dark
    lp_b = 0;
    ok &= lp_read(LP_DEVICE_CONFIG1) == LP_CONFIG1;           // the device took the configuration
    return ok;                                               // any failure -> caller retries the whole init
}

// Brightness / colour split lives in lib/core (lp_brightness, lp_colour; host-tested).
static bool lp_output(const float drive[G_COUNT]) {   // false on a bus error: caller re-initialises
    float mx = 0;
    for (uint8_t g = 0; g < G_COUNT; g++) if (drive[g] > mx) mx = drive[g];
    const uint8_t b = lp_brightness(mx, lp_b);
    uint8_t col[G_COUNT], regs[4 + N_OUT];
    for (uint8_t g = 0; g < G_COUNT; g++) col[g] = lp_colour(drive[g], b);
    memset(regs, b, 4);
    for (uint8_t o = 0; o < N_OUT; o++) regs[4 + o] = OUT_GROUP[o] >= 0 ? col[OUT_GROUP[o]] : 0;
    if (!memcmp(regs, last_regs, sizeof(regs))) return true;
    // Each register acts when written. Order the writes so the in-between state is never brighter than either
    // end: brightness up -> colours first, brightness down (or same) -> brightness first (one auto-increment write).
    if (lp_b && b > lp_b) {
        if (!lp_write(LP_COLOR0, regs + 4, N_OUT) || !lp_write(LP_BRIGHTNESS0, regs, 4)) return false;
    } else if (!lp_write(LP_BRIGHTNESS0, regs, sizeof(regs))) {
        return false;
    }
    memcpy(last_regs, regs, sizeof(regs));
    lp_b = b;
    return true;
}

static void lp_sleep() {                         // outputs off, then STANDBY (Chip_EN = 0, ~10 uA)
    uint8_t zero[N_OUT] = {0};
    lp_write(LP_COLOR0, zero, N_OUT);
    const uint8_t off = 0x00;
    lp_write(LP_DEVICE_CONFIG0, &off, 1);
}

static void lp_reset() {                         // RESET register: every register back to its default
    const uint8_t r = 0xFF;
    lp_write(LP_RESET, &r, 1);
}

// ------------------------------------------------------- MCP9800 (LM75-compatible)
static bool ts_config(uint8_t conf) {            // CONFIG (pointer 01h)
    Wire.beginTransmission(ADDR_TSENSE);
    Wire.write((uint8_t)0x01);
    Wire.write(conf);
    return Wire.endTransmission() == 0;
}

// TSET / THYST (pointers 03h / 02h): 9-bit two's complement, 0.5 C/LSB, left-aligned in 16 bits (D15..D7)
static bool ts_write_limit(uint8_t reg, int16_t celsius) {
    const uint16_t v = (uint16_t)((int16_t)(celsius * 2) << 7);
    Wire.beginTransmission(ADDR_TSENSE);
    Wire.write(reg);
    Wire.write((uint8_t)(v >> 8));
    Wire.write((uint8_t)(v & 0xFF));
    return Wire.endTransmission() == 0;
}

// Hardware thermostat: ALERT (comparator mode, active low, fault queue 2) holds the LP5012 EN low above TSET and
// releases it below THYST. The firmware derates from 45 C, so this is a backstop for a hung or wrong firmware.
// MCP9800 POR defaults are TSET 80 C / THYST 75 C, so a POR on the LED board leaves a looser backstop until re-init.
static bool ts_ok = false;
static bool ts_setup() {
    ts_ok = ts_write_limit(0x02, TSENSE_THYST_C) && ts_write_limit(0x03, TSENSE_TSET_C) && ts_config(TSENSE_CONFIG);
    return ts_ok;
}

// Read back CONFIG and TSET (R2-F5): a bus glitch that loosened the hardware thermostat is re-armed within 10 s
static bool ts_config_intact() {
    Wire.beginTransmission(ADDR_TSENSE);
    Wire.write((uint8_t)0x01);
    if (Wire.endTransmission(false) != 0 || Wire.requestFrom((uint8_t)ADDR_TSENSE, (uint8_t)1) != 1) return false;
    if ((uint8_t)Wire.read() != TSENSE_CONFIG) return false;
    Wire.beginTransmission(ADDR_TSENSE);
    Wire.write((uint8_t)0x03);
    if (Wire.endTransmission(false) != 0 || Wire.requestFrom((uint8_t)ADDR_TSENSE, (uint8_t)2) != 2) return false;
    const uint8_t msb = (uint8_t)Wire.read();
    const uint8_t lsb = (uint8_t)Wire.read();
    const uint16_t tset = (uint16_t)((int16_t)(TSENSE_TSET_C * 2) << 7);
    return msb == (uint8_t)(tset >> 8) && (lsb & 0x80) == (uint8_t)(tset & 0x80);
}

static bool ts_read(float *t) {
    Wire.beginTransmission(ADDR_TSENSE);
    Wire.write((uint8_t)0x00);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom((uint8_t)ADDR_TSENSE, (uint8_t)2) != 2) return false;
    const uint8_t msb = (uint8_t)Wire.read();     // two statements: operand evaluation order is unspecified
    const uint8_t lsb = (uint8_t)Wire.read();
    const int16_t raw = (int16_t)(((uint16_t)msb << 8) | lsb);
    *t = (float)(raw >> 4) * 0.0625f;             // 12-bit two's complement, 0.0625 C/LSB (arithmetic shift)
    return *t > -55.0f && *t < 125.0f;            // outside the sensor's range = treat as a failed read
}

// ------------------------------------------------- supply (= battery) voltage
// ADC0 measures the internal 1.1 V reference with VDD as the ADC reference: VDD = 1.1 V * 1023 / RES.
static uint16_t vdd_mv() {
    VREF.CTRLA = (uint8_t)((VREF.CTRLA & ~VREF_ADC0REFSEL_gm) | VREF_ADC0REFSEL_1V1_gc);
    ADC0.CTRLC = ADC_SAMPCAP_bm | ADC_REFSEL_VDDREF_gc | ADC_PRESC_DIV16_gc;
    ADC0.CTRLD = ADC_INITDLY_DLY64_gc;
    ADC0.SAMPCTRL = 16;
    ADC0.MUXPOS = ADC_MUXPOS_INTREF_gc;
    ADC0.CTRLA = ADC_ENABLE_bm;                   // 10-bit
    VREF.CTRLB |= VREF_ADC0REFEN_bm;              // keep INTREF running for the whole burst ...
    delayMicroseconds(50);                        // ... and let it start (TStart 25 us typ, Table 36-22)
    uint32_t acc = 0;
    for (uint8_t i = 0; i < 9; i++) {
        ADC0.COMMAND = ADC_STCONV_bm;
        while (ADC0.COMMAND & ADC_STCONV_bm) {}
        if (i) acc += ADC0.RES;                   // discard the first conversion after the reference starts
    }
    VREF.CTRLB &= (uint8_t)~VREF_ADC0REFEN_bm;
    uint16_t res = (uint16_t)(acc / 8);
    return res ? (uint16_t)((1100UL * 1023UL) / res) : 0;
}

// ------------------------------------------------------------- empty battery
ISR(RTC_PIT_vect) { RTC.PITINTFLAGS = RTC_PI_bm; }

static void i2c_bus_recover();

static uint32_t ts_valid_after;                  // first 12-bit MCP9800 conversion (600 ms max) after power-up

// bleed = true for a recovery power-cycle: SDA/SCL are driven low so VLED discharges through the 3.3 k pull-ups
// and the LP5012 really drops below its UVLO (2.0 V) and restarts from a clean POR (round2 R2-E2).
static void led_board_off(bool bleed) {
    lp_sleep();                                  // outputs off before the rail goes
    Wire.end();
    digitalWriteFast(PIN_LED_EN_N, HIGH);        // Q4 off (soft, R13/C8): LP5012 + MCP9800 unpowered; R12 holds it
    if (bleed) {
        pinMode(PIN_PB0, OUTPUT);                // PORT OUT is 0: both lines low, sinking VLED through the pull-ups
        pinMode(PIN_PB1, OUTPUT);
    } else {
        pinMode(PIN_PB0, INPUT);                 // SCL / SDA: the pull-ups sit on VLED, which is about to drop
        pinMode(PIN_PB1, INPUT);
        PORTB.PIN0CTRL = PORT_ISC_INPUT_DISABLE_gc;   // no input-buffer current while the bus floats
        PORTB.PIN1CTRL = PORT_ISC_INPUT_DISABLE_gc;
    }
}

static void led_board_on() {
    pinMode(PIN_PB0, INPUT);                     // release the bus before VLED comes up
    pinMode(PIN_PB1, INPUT);
    pinMode(PIN_LED_EN_N, OUTPUT);
    digitalWriteFast(PIN_LED_EN_N, LOW);          // Q4 on: ~2 ms soft ramp (R13/C8) to VLED, pull-ups included
    delay(10);                                    // VLED rise, POR, LP5012 EN high > 500 us (tEN_H)
    PORTB.PIN0CTRL = 0;                           // input buffers back on (led_board_off() disabled them)
    PORTB.PIN1CTRL = 0;
    i2c_bus_recover();
    Wire.begin();
    Wire.setClock(I2C_HZ);
    ts_valid_after = millis() + 700;              // the MCP9800 reads 0 C until its first conversion is done
}

static void sleep_until_resumed() {
    led_board_off(false);
    while (RTC.STATUS) {}
    RTC.CLKSEL = RTC_CLKSEL_INT32K_gc;
    RTC.PER = 0xFFFF;
    RTC.CTRLA = RTC_RTCEN_bm;                     // tinyAVR 1-series erratum: the PIT only runs while RTCEN = 1 (FW-12)
    while (RTC.PITSTATUS) {}
    RTC.PITINTCTRL = RTC_PI_bm;
    RTC.PITCTRLA = RTC_PERIOD_CYC32768_gc | RTC_PITEN_bm;   // wake every ~1 s
    set_sleep_mode(SLEEP_MODE_PWR_DOWN);
    uint8_t good = 0;
    for (;;) {
        sleep_enable();
        sleep_cpu();
        sleep_disable();
        __builtin_avr_wdr();                      // WDT (2 s) keeps running in power-down; PIT wakes every 1 s
        good = (vdd_mv() >= VBAT_RESUME_MV) ? (uint8_t)(good + 1) : 0;
        if (good >= 3) break;                     // 3 consecutive 1 s readings (e.g. USB plugged in)
    }
    RTC.PITCTRLA = 0;
    _PROTECTED_WRITE(RSTCTRL.SWRR, RSTCTRL_SWRE_bm);   // clean restart
}

// ---------------------------------------------------------------------- main
// A reset in the middle of a transfer can leave a slave holding SDA low (neither LED-board part has a time-out):
// clock SCL until SDA is released, then send a STOP. Pins are open-drain here (PORT OUT = 0, external pull-ups).
static void i2c_bus_recover() {
    pinMode(PIN_PB0, INPUT);
    pinMode(PIN_PB1, INPUT);
    for (uint8_t i = 0; i < 9 && digitalReadFast(PIN_PB1) == LOW; i++) {
        pinMode(PIN_PB0, OUTPUT); delayMicroseconds(5);   // SCL low
        pinMode(PIN_PB0, INPUT);  delayMicroseconds(5);   // SCL released
    }
    pinMode(PIN_PB1, OUTPUT); delayMicroseconds(5);       // SDA low while SCL high ...
    pinMode(PIN_PB1, INPUT);  delayMicroseconds(5);       // ... then high = STOP
}

static void unused_pins_low_power() {
    const uint8_t pins[] = {PIN_PA2, PIN_PA3, PIN_PA7, PIN_PB3, PIN_PB4, PIN_PB5,
                            PIN_PC0, PIN_PC1, PIN_PC2, PIN_PC3};
    for (uint8_t i = 0; i < sizeof(pins); i++) pinMode(pins[i], INPUT_PULLUP);
}

void setup() {
    unused_pins_low_power();
    pinMode(PIN_BTN_UP, INPUT_PULLUP);
    pinMode(PIN_BTN_MAIN, INPUT_PULLUP);
    pinMode(PIN_BTN_DN, INPUT_PULLUP);
#ifdef DEBUG_SERIAL
    Serial.swap(SERIAL_SWAP);                     // TX on PA1 (header J4 pin 3)
    Serial.begin(115200);
    if ((FUSE.BODCFG & 0x0C) == 0) Serial.println(F("BOD OFF: run pio run -e attiny3216 -t fuses"));   // FW-09
#else
    pinMode(PIN_PA1, INPUT_PULLUP);
#endif
    led_board_on();
    _PROTECTED_WRITE(WDT.CTRLA, WDT_PERIOD_2KCLK_gc);   // 2 s watchdog: a hung loop resets, LEDs re-init
    saved_t saved;
    EEPROM.get(0, saved);
    core_init(&core, &saved, millis());
    ts_setup();                                   // best effort: a dead sensor is handled by the core (fail-safe cap)
    lp_ok = lp_init();
}

void loop() {
    static uint32_t last_ms, last_t, last_v, last_lp_retry, last_lp_check;
    uint32_t now = millis();
    if (now != last_ms) {
        last_ms = now;
        bool pressed[BTN_COUNT] = {digitalReadFast(PIN_BTN_UP) == LOW, digitalReadFast(PIN_BTN_MAIN) == LOW,
                                   digitalReadFast(PIN_BTN_DN) == LOW};
        core_buttons(&core, pressed, now);
        if (now - last_t >= 1000) {
            last_t = now;
            float t = 0.0f;
            bool ok = (int32_t)(now - ts_valid_after) >= 0 && ts_read(&t);
#if defined(FAULT_T_NACK)                         // bench fault injection only (VERIFY T5a/T5b): never in a release
            ok = false;
#elif defined(FAULT_T_STUCK)
            ok = true;
            t = 25.0f;
#endif
            if (ok) last_temp_c = t;
            static uint8_t ts_check_div;
            if (!ok) ts_ok = false;
            else if (!ts_ok) ts_setup();          // sensor came back: re-arm the thermostat thresholds
            else if (++ts_check_div >= 10) {      // every 10 s: is the thermostat still armed as we set it?
                ts_check_div = 0;
                if (!ts_config_intact()) ts_setup();
            }
            core_temperature(&core, ok, t, now);
#ifdef DEBUG_SERIAL
            Serial.print(F("T=")); Serial.print(ok ? t : -99.0f); Serial.print(F(" V=")); Serial.print(core.vbat_mv);
            Serial.print(F(" mode=")); Serial.print(core.mode); Serial.print(F(" lvl=")); Serial.print(core.level[core.mode]);
            Serial.print(F(" cap=")); Serial.print(core.t_cap);
            const int16_t c1 = lp_read(LP_DEVICE_CONFIG1);   // bring-up (VERIFY E16): expect 1C
            Serial.print(F(" lp=")); if (c1 < 0) Serial.print(F("--")); else Serial.print((uint8_t)c1, HEX);
            Serial.print(F(" ts=")); Serial.println(ts_ok ? 1 : 0);
#endif
        }
        if (now - last_v >= 500) {
            last_v = now;
            core_battery(&core, vdd_mv(), now);
        }
        core_tick(&core, now);
        if (!lp_ok && now - last_lp_retry >= 500) {
            last_lp_retry = now;
            ts_setup();                           // same rail: an LP5012 POR means the MCP9800 lost its limits too
            lp_ok = lp_init();
            // 4 failed inits (2 s) and not a thermostat trip (ALERT holds EN low only while hot, and the LP5012
            // does not answer in shutdown): power-cycle the LED board through Q4 (m6)
            lp_fails = lp_ok ? 0 : (uint8_t)(lp_fails + 1);
            if (lp_fails >= 4 && (!ts_ok || last_temp_c < (float)TSENSE_THYST_C)) {
                lp_fails = 0;
                lp_reset();                       // cheap first: an LP5012 that still listens is reset in place
                led_board_off(true);
                delay(200);                       // >10 tau of the VLED bleed; well under the 2 s watchdog
                led_board_on();
                ts_setup();
                lp_ok = lp_init();
            }
        }
        if (lp_ok && (now & 3) == 0 && !lp_output(core.drive)) lp_ok = false;   // 250 Hz, writes on change
        if (lp_ok && now - last_lp_check >= 1000) {   // LED-board POR (cable, VLED dropout) or a thermostat EN
            last_lp_check = now;                       // cycle reset the LP5012 to STANDBY with Chip_EN = 0
            int16_t c0 = lp_read(LP_DEVICE_CONFIG0);
            if (c0 < 0 || !(c0 & LP_CHIP_EN)) lp_ok = false;   // not our configuration -> re-init
        }
        if (core.save_request) {
            core.save_request = false;
            saved_t s;
            saved_make(&s, core.mode, core.level[core.mode]);
            EEPROM.put(0, s);
        }
        if (core.batt == 2 && core.drive[G_WW] + core.drive[G_CW] + core.drive[G_R] + core.drive[G_G] + core.drive[G_B] < 1e-4f)
            sleep_until_resumed();
    }
    __builtin_avr_wdr();
    set_sleep_mode(SLEEP_MODE_IDLE);
    sleep_mode();                                 // wakes on the millis timer interrupt
}
