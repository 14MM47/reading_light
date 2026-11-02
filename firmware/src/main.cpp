// Moon reading light firmware - ATtiny3216 (megaTinyCore / PlatformIO).
// Hardware glue only; behaviour lives in lib/core/lightcore.cpp (host unit-tested).
#include <Arduino.h>
#include <EEPROM.h>
#include <Wire.h>
#include <avr/sleep.h>

#include "config.h"
#include "lightcore.h"

static core_t core;
static uint8_t iref_code = 0xFF;
static uint8_t last_pwm[16];
static bool tlc_ok = false;
static uint8_t tlc_fails = 0;
static float last_temp_c = 25.0f;

// ------------------------------------------------------------------ TLC59116
static bool tlc_write(uint8_t reg, const uint8_t *d, uint8_t n) {
    Wire.beginTransmission(ADDR_TLC);
    // AI=100 (all registers, rolls over after 1Bh) only for block writes; single registers (IREF 1Ch) without AI
    Wire.write((uint8_t)(n > 1 ? (0x80 | reg) : reg));
    for (uint8_t i = 0; i < n; i++) Wire.write(d[i]);
    return Wire.endTransmission() == 0;
}

static int16_t tlc_read(uint8_t reg) {          // -1 on bus error
    Wire.beginTransmission(ADDR_TLC);
    Wire.write(reg);                             // control byte, no auto-increment
    if (Wire.endTransmission(false) != 0) return -1;
    if (Wire.requestFrom((uint8_t)ADDR_TLC, (uint8_t)1) != 1) return -1;
    return (int16_t)Wire.read();
}

static bool tlc_init() {
    const uint8_t mode[2] = {0x00, 0x00};       // MODE1: oscillator on, no sub/all-call; MODE2: dimming, defaults
    if (!tlc_write(0x00, mode, 2)) return false;
    delayMicroseconds(600);                      // oscillator start-up (500 us max)
    bool ok = true;
    uint8_t zero[16] = {0};
    ok &= tlc_write(0x02, zero, 16);             // PWM0..15 = 0
    const uint8_t grp[2] = {0xFF, 0x00};         // GRPPWM, GRPFREQ (group dimming unused: LDR=10)
    ok &= tlc_write(0x12, grp, 2);
    uint8_t ledout[4] = {0, 0, 0, 0};
    for (uint8_t o = 0; o < 16; o++)
        if (OUT_GROUP[o] >= 0) ledout[o / 4] |= (uint8_t)(0x2 << (2 * (o % 4)));   // LDRx = 10: individual PWM
    ok &= tlc_write(0x14, ledout, 4);
    iref_code = 0xFF;
    const uint8_t iref = iref_code;              // CM=1 HC=1 CC=63 -> CG 0.992 (full scale)
    ok &= tlc_write(0x1C, &iref, 1);
    memset(last_pwm, 0, sizeof(last_pwm));
    return ok;                                   // any failed write -> caller retries the whole init
}

// current-gain steps (IREF register {CM,HC,CC[5:0]}): CG = (1+HC)(1+CC/64)/4 * 3^(CM-1)
// Only steps inside the datasheet's output-current ranges (CM=0: 5-40 mA, CM=1: 10-120 mA) at 25 mA full scale:
// 0x7F -> 8.3 mA (CM=0), 0xBF -> 12.4 mA, 0xFF -> 24.8 mA (thermal review: 2.1 mA was below the 5 mA minimum)
static const struct { uint8_t code; float cg; } CG_STEPS[] = {
    {0x7F, 0.3307f}, {0xBF, 0.4961f}, {0xFF, 0.9922f}};
#define CG_N (sizeof(CG_STEPS) / sizeof(CG_STEPS[0]))

static bool tlc_output(const float drive[G_COUNT]) {   // false on a bus error: caller re-initialises
    float mx = 0;
    for (uint8_t g = 0; g < G_COUNT; g++) if (drive[g] > mx) mx = drive[g];
    uint8_t k = 0;
    while (k < CG_N - 1 && CG_STEPS[k].cg < mx) k++;
    // hysteresis: only step down when the max is comfortably below the lower gain
    if (CG_STEPS[k].code != iref_code) {
        uint8_t cur = 0;
        while (cur < CG_N - 1 && CG_STEPS[cur].code != iref_code) cur++;
        if (k < cur && mx > 0.8f * CG_STEPS[k].cg) k = cur;   // stay
    }
    float cg = CG_STEPS[k].cg;
    uint8_t pwm[16];
    bool changed = false;
    for (uint8_t o = 0; o < 16; o++) {
        int8_t g = OUT_GROUP[o];
        float v = (g >= 0) ? drive[g] * 0.9922f / cg : 0.0f;  // drive is a fraction of full scale (CG 0.992)
        int p = (int)(v * 255.0f + 0.5f);
        pwm[o] = (uint8_t)(p > 255 ? 255 : (p < 0 ? 0 : p));
        changed |= pwm[o] != last_pwm[o];
    }
    const uint8_t code = CG_STEPS[k].code;
    if (code != iref_code) {
        // IREF acts when written; PWM acts at STOP (MODE2.OCH=0 covers 02h..17h only). Order the writes so the
        // in-between state is never brighter than either end: gain up -> PWM first, gain down -> IREF first.
        const bool gain_up = code > iref_code;   // codes in CG_STEPS increase with gain
        if (gain_up) {
            if (!tlc_write(0x02, pwm, 16)) return false;
            memcpy(last_pwm, pwm, 16);
            if (!tlc_write(0x1C, &code, 1)) return false;
        } else {
            if (!tlc_write(0x1C, &code, 1)) return false;
            iref_code = code;
            if (!tlc_write(0x02, pwm, 16)) return false;
            memcpy(last_pwm, pwm, 16);
        }
        iref_code = code;
        return true;
    }
    if (changed) {
        if (!tlc_write(0x02, pwm, 16)) return false;
        memcpy(last_pwm, pwm, 16);
    }
    return true;
}

static void tlc_sleep() {
    uint8_t zero[16] = {0};
    tlc_write(0x02, zero, 16);
    const uint8_t mode1 = 0x10;                  // OSC=1: oscillator off (low power)
    tlc_write(0x00, &mode1, 1);
}

// --------------------------------------------------------------------- LM75B
static bool lm75_config(uint8_t conf) {        // Conf register (pointer 01h): B0 = SHUTDOWN
    Wire.beginTransmission(ADDR_LM75);
    Wire.write((uint8_t)0x01);
    Wire.write(conf);
    return Wire.endTransmission() == 0;
}

// Tos / Thyst (pointers 03h / 02h): 9-bit two's complement, 0.5 C/LSB, left-aligned in 16 bits (D15..D7)
static bool lm75_write_limit(uint8_t reg, int16_t celsius) {
    const uint16_t v = (uint16_t)((int16_t)(celsius * 2) << 7);
    Wire.beginTransmission(ADDR_LM75);
    Wire.write(reg);
    Wire.write((uint8_t)(v >> 8));
    Wire.write((uint8_t)(v & 0xFF));
    return Wire.endTransmission() == 0;
}

// Hardware thermostat: OS (comparator mode, active low, fault queue 2) holds the TLC59116 RESET low above TOS and
// releases it below THYST. The firmware derates from 45 C, so this is a backstop for a hung or wrong firmware.
// LM75B POR defaults are Tos 80 C / Thyst 75 C, so a POR on the LED board leaves a looser backstop until re-init.
static bool lm75_ok = false;
static bool lm75_setup() {
    lm75_ok = lm75_write_limit(0x02, LM75_THYST_C) && lm75_write_limit(0x03, LM75_TOS_C) &&
              lm75_config(0x08);                  // B4:B3 = 01 (2 faults), B2 = 0 (active low), B1 = 0 (comparator)
    return lm75_ok;
}

static bool lm75_read(float *t) {
    Wire.beginTransmission(ADDR_LM75);
    Wire.write((uint8_t)0x00);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom((uint8_t)ADDR_LM75, (uint8_t)2) != 2) return false;
    const uint8_t msb = (uint8_t)Wire.read();     // two statements: operand evaluation order is unspecified
    const uint8_t lsb = (uint8_t)Wire.read();
    const int16_t raw = (int16_t)(((uint16_t)msb << 8) | lsb);
    *t = (float)(raw >> 5) * 0.125f;              // 11-bit two's complement, 0.125 C/LSB (arithmetic shift)
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

static void led_board_off() {
    tlc_sleep();                                 // outputs off before the rail goes
    Wire.end();
    pinMode(PIN_PB0, INPUT);                     // SCL / SDA: the pull-ups sit on VLED, which is about to drop
    pinMode(PIN_PB1, INPUT);
    PORTB.PIN0CTRL = PORT_ISC_INPUT_DISABLE_gc;  // no input-buffer current while the bus floats
    PORTB.PIN1CTRL = PORT_ISC_INPUT_DISABLE_gc;
    digitalWriteFast(PIN_LED_EN_N, HIGH);        // Q4 off: TLC59116 + LM75B unpowered (R12 keeps it off in reset)
}

static void led_board_on() {
    pinMode(PIN_LED_EN_N, OUTPUT);
    digitalWriteFast(PIN_LED_EN_N, LOW);          // Q4 on: power the LED board (the I2C pull-ups are on VLED too)
    delay(10);                                    // VLED rise + TLC59116 / LM75B power-on reset
    PORTB.PIN0CTRL = 0;                           // input buffers back on (led_board_off() disabled them)
    PORTB.PIN1CTRL = 0;
    i2c_bus_recover();
    Wire.begin();
    Wire.setClock(I2C_HZ);
}

static void sleep_until_resumed() {
    led_board_off();
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
// A reset in the middle of a transfer can leave a slave holding SDA low (the TLC59116 has no bus time-out):
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
    lm75_setup();                                 // best effort: a dead sensor is handled by the core (fail-safe cap)
    tlc_ok = tlc_init();
}

void loop() {
    static uint32_t last_ms, last_t, last_v, last_tlc_retry, last_tlc_check;
    uint32_t now = millis();
    if (now != last_ms) {
        last_ms = now;
        bool pressed[BTN_COUNT] = {digitalReadFast(PIN_BTN_UP) == LOW, digitalReadFast(PIN_BTN_MAIN) == LOW,
                                   digitalReadFast(PIN_BTN_DN) == LOW};
        core_buttons(&core, pressed, now);
        if (now - last_t >= 1000) {
            last_t = now;
            float t = 0.0f;
            bool ok = lm75_read(&t);
#if defined(FAULT_T_NACK)                         // bench fault injection only (VERIFY T5a/T5b): never in a release
            ok = false;
#elif defined(FAULT_T_STUCK)
            ok = true;
            t = 25.0f;
#endif
            if (ok) last_temp_c = t;
            if (!ok) lm75_ok = false;
            else if (!lm75_ok) lm75_setup();      // sensor came back: re-arm the thermostat thresholds
            core_temperature(&core, ok, t, now);
#ifdef DEBUG_SERIAL
            Serial.print(F("T=")); Serial.print(ok ? t : -99.0f); Serial.print(F(" V=")); Serial.print(core.vbat_mv);
            Serial.print(F(" mode=")); Serial.print(core.mode); Serial.print(F(" lvl=")); Serial.print(core.level[core.mode]);
            Serial.print(F(" cap=")); Serial.println(core.t_cap);
#endif
        }
        if (now - last_v >= 500) {
            last_v = now;
            core_battery(&core, vdd_mv(), now);
        }
        core_tick(&core, now);
        if (!tlc_ok && now - last_tlc_retry >= 500) {
            last_tlc_retry = now;
            lm75_setup();                         // same rail: a TLC POR means the LM75B lost its limits too
            tlc_ok = tlc_init();
            // 4 failed inits (2 s) and not a thermostat trip (OS holds RESET only while hot): power-cycle the LED
            // board through Q4. A sag that left VCC between 0.2 and 2.5 V can leave the TLC59116 undefined (m6).
            tlc_fails = tlc_ok ? 0 : (uint8_t)(tlc_fails + 1);
            if (tlc_fails >= 4 && (!lm75_ok || last_temp_c < (float)LM75_THYST_C)) {
                tlc_fails = 0;
                led_board_off();
                delay(500);                       // under the 2 s watchdog; VLED (10 uF) decays through the board load
                led_board_on();
                lm75_setup();
                tlc_ok = tlc_init();
            }
        }
        if (tlc_ok && (now & 3) == 0 && !tlc_output(core.drive)) tlc_ok = false;   // 250 Hz, writes on change
        if (tlc_ok && now - last_tlc_check >= 1000) {   // LED board POR (cable, VLED dropout) resets MODE1 to 11h
            last_tlc_check = now;
            int16_t m1 = tlc_read(0x00);
            if (m1 < 0 || (m1 & 0x11)) tlc_ok = false;  // OSC or ALLCALL set = not our configuration -> re-init
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
