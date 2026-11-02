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

// ------------------------------------------------------------------ TLC59116
static bool tlc_write(uint8_t reg, const uint8_t *d, uint8_t n) {
    Wire.beginTransmission(ADDR_TLC);
    Wire.write((uint8_t)(0x80 | reg));          // AI2=1: auto-increment through all registers
    for (uint8_t i = 0; i < n; i++) Wire.write(d[i]);
    return Wire.endTransmission() == 0;
}

static bool tlc_init() {
    const uint8_t mode[2] = {0x00, 0x00};       // MODE1: oscillator on, no sub/all-call; MODE2: dimming, defaults
    if (!tlc_write(0x00, mode, 2)) return false;
    delayMicroseconds(600);                      // oscillator start-up (500 us max)
    uint8_t zero[16] = {0};
    tlc_write(0x02, zero, 16);                   // PWM0..15 = 0
    const uint8_t grp[2] = {0xFF, 0x00};         // GRPPWM, GRPFREQ (group dimming unused: LDR=10)
    tlc_write(0x12, grp, 2);
    uint8_t ledout[4] = {0, 0, 0, 0};
    for (uint8_t o = 0; o < 16; o++)
        if (OUT_GROUP[o] >= 0) ledout[o / 4] |= (uint8_t)(0x2 << (2 * (o % 4)));   // LDRx = 10: individual PWM
    tlc_write(0x14, ledout, 4);
    iref_code = 0xFF;
    const uint8_t iref = iref_code;              // CM=1 HC=1 CC=63 -> CG 0.992 (full scale)
    tlc_write(0x1C, &iref, 1);
    memset(last_pwm, 0, sizeof(last_pwm));
    return true;
}

// current-gain steps (IREF register {CM,HC,CC[5:0]}): CG = (1+HC)(1+CC/64)/4 * 3^(CM-1)
static const struct { uint8_t code; float cg; } CG_STEPS[] = {
    {0x00, 0.0833f}, {0x3F, 0.1654f}, {0x7F, 0.3307f}, {0xBF, 0.4961f}, {0xFF, 0.9922f}};

static void tlc_output(const float drive[G_COUNT]) {
    float mx = 0;
    for (uint8_t g = 0; g < G_COUNT; g++) if (drive[g] > mx) mx = drive[g];
    uint8_t k = 0;
    while (k < 4 && CG_STEPS[k].cg < mx) k++;
    // hysteresis: only step down when the max is comfortably below the lower gain
    if (CG_STEPS[k].code != iref_code) {
        uint8_t cur = 0;
        while (cur < 4 && CG_STEPS[cur].code != iref_code) cur++;
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
    if (CG_STEPS[k].code != iref_code) {
        iref_code = CG_STEPS[k].code;
        tlc_write(0x1C, &iref_code, 1);
        changed = true;
    }
    if (changed && tlc_write(0x02, pwm, 16)) memcpy(last_pwm, pwm, 16);
}

static void tlc_sleep() {
    uint8_t zero[16] = {0};
    tlc_write(0x02, zero, 16);
    const uint8_t mode1 = 0x10;                  // OSC=1: oscillator off (low power)
    tlc_write(0x00, &mode1, 1);
}

// --------------------------------------------------------------------- LM75B
static bool lm75_read(float *t) {
    Wire.beginTransmission(ADDR_LM75);
    Wire.write((uint8_t)0x00);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom((uint8_t)ADDR_LM75, (uint8_t)2) != 2) return false;
    int16_t raw = (int16_t)((Wire.read() << 8) | Wire.read());
    *t = (float)(raw >> 5) * 0.125f;              // 11-bit, 0.125 C/LSB
    return true;
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
    uint32_t acc = 0;
    for (uint8_t i = 0; i < 8; i++) {
        ADC0.COMMAND = ADC_STCONV_bm;
        while (ADC0.COMMAND & ADC_STCONV_bm) {}
        acc += ADC0.RES;
    }
    uint16_t res = (uint16_t)(acc / 8);
    return res ? (uint16_t)((1100UL * 1023UL) / res) : 0;
}

// ------------------------------------------------------------- empty battery
ISR(RTC_PIT_vect) { RTC.PITINTFLAGS = RTC_PI_bm; }

static void sleep_until_resumed() {
    tlc_sleep();
    Wire.beginTransmission(ADDR_LM75);           // LM75B shutdown (config register bit 0)
    Wire.write((uint8_t)0x01);
    Wire.write((uint8_t)0x01);
    Wire.endTransmission();
    while (RTC.STATUS) {}
    RTC.CLKSEL = RTC_CLKSEL_INT32K_gc;
    while (RTC.PITSTATUS) {}
    RTC.PITINTCTRL = RTC_PI_bm;
    RTC.PITCTRLA = RTC_PERIOD_CYC32768_gc | RTC_PITEN_bm;   // wake every ~1 s
    set_sleep_mode(SLEEP_MODE_PWR_DOWN);
    for (;;) {
        sleep_enable();
        sleep_cpu();
        sleep_disable();
        if (vdd_mv() >= VBAT_RESUME_MV) break;    // e.g. USB plugged in
    }
    RTC.PITCTRLA = 0;
    _PROTECTED_WRITE(RSTCTRL.SWRR, RSTCTRL_SWRE_bm);   // clean restart
}

// ---------------------------------------------------------------------- main
static void unused_pins_low_power() {
    const uint8_t pins[] = {PIN_PA2, PIN_PA3, PIN_PA7, PIN_PB2, PIN_PB3, PIN_PB4, PIN_PB5,
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
#else
    pinMode(PIN_PA1, INPUT_PULLUP);
#endif
    Wire.begin();
    Wire.setClock(I2C_HZ);
    delay(5);                                     // LED board rails settle
    saved_t saved;
    EEPROM.get(0, saved);
    core_init(&core, &saved, millis());
    tlc_ok = tlc_init();
}

void loop() {
    static uint32_t last_ms, last_t, last_v, last_tlc_retry;
    uint32_t now = millis();
    if (now != last_ms) {
        last_ms = now;
        bool pressed[BTN_COUNT] = {digitalReadFast(PIN_BTN_UP) == LOW, digitalReadFast(PIN_BTN_MAIN) == LOW,
                                   digitalReadFast(PIN_BTN_DN) == LOW};
        core_buttons(&core, pressed, now);
        if (now - last_t >= 1000) {
            last_t = now;
            float t;
            bool ok = lm75_read(&t);
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
            tlc_ok = tlc_init();
        }
        if (tlc_ok && (now & 3) == 0) tlc_output(core.drive);   // 250 Hz update, only writes on change
        if (core.save_request) {
            core.save_request = false;
            saved_t s;
            saved_make(&s, core.mode, core.level[core.mode]);
            EEPROM.put(0, s);
        }
        if (core.batt == 2 && core.drive[G_WW] + core.drive[G_CW] + core.drive[G_R] + core.drive[G_G] + core.drive[G_B] < 1e-4f)
            sleep_until_resumed();
    }
    set_sleep_mode(SLEEP_MODE_IDLE);
    sleep_mode();                                 // wakes on the millis timer interrupt
}
