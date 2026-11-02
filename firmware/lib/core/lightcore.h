// Portable light logic (no hardware access): modes, brightness, buttons, thermal & battery limits,
// saved default. Compiled for the ATtiny3216 and for the host (unit tests).
#pragma once
#include <stdint.h>
#include <stdbool.h>

#include "modes_table.h"

#ifdef __cplusplus
extern "C" {
#endif

// ----- tunables (see docs/design/firmware.md) -----
#define LEVELS            16        // brightness steps 0..15
#define LEVEL_MIN_FRAC    0.004f    // level 0 = 0.4 % of full drive; level 15 = 100 %
#define HOLD_SAVE_MS      2000      // MAIN held this long = save current colour + level as power-on default
#define REPEAT_DELAY_MS   450       // UP/DOWN auto-repeat start
#define REPEAT_EVERY_MS   150
#define DEBOUNCE_MS       15
#define FADE_MS           160       // cross-fade on any change
#define I_CHANNEL_MA      25.0f     // TLC59116 full-scale current: 1.26 V / 750 R x 15 x CG 0.992 (led-board R1)
#define I_CAP_MA          200.0f    // total LED current cap while the temperature sensor is trusted (short bursts)
#define I_CAP_UNTRUSTED_MA 110.0f   // hard cap without a trusted sensor: ~0.4 W in the head at 4.2 V (thermal review)
#define T_DERATE_START_C  45.0f     // LED-board temperature where derating starts (keeps the PLA <= ~47 C)
#define T_DERATE_KNEE_C   52.0f     // 30 % at the knee
#define T_DERATE_MAX_C    58.0f     // 5 % (faint glow) at/above this; the LM75B OS thermostat cuts the TLC at 60 C
#define T_PLAUSIBLE_MIN_C (-20.0f)
#define T_PLAUSIBLE_MAX_C 100.0f
#define T_FROZEN_MS       300000UL  // reading unchanged this long while > 50 mA flows = sensor not trusted
#define T_FAILSAFE_CAP    0.30f     // cap if the temperature sensor stops answering
#define VBAT_LOW_MV       3450      // under load: cap brightness, periodic blink
#define VBAT_EMPTY_MV     3300      // under load for EMPTY_HOLD_MS: fade out and sleep
#define VBAT_RESUME_MV    3700      // resume after empty (e.g. USB connected)
#define EMPTY_HOLD_MS     5000
#define LOW_CAP           0.35f
#define LOW_BLINK_EVERY_MS 60000UL
#define DEFAULT_MODE      1         // "Soft white 3000K"
#define DEFAULT_LEVEL     10

enum { BTN_UP = 0, BTN_MAIN, BTN_DN, BTN_COUNT };

typedef struct {
    uint8_t magic, version, mode, level, crc;
} saved_t;

typedef struct {
    // persistent-ish state
    uint8_t mode;
    uint8_t level[MODE_COUNT];
    // buttons
    bool raw[BTN_COUNT], stable[BTN_COUNT];
    uint32_t raw_since[BTN_COUNT], pressed_at[BTN_COUNT], last_repeat[BTN_COUNT];
    bool main_save_done;
    // limits
    float t_cap, t_cap_target;        // thermal derate (filtered)
    bool t_valid;
    uint32_t t_last_ok;
    float t_last_value;               // plausibility: last distinct reading and when it last changed
    uint32_t t_changed_at;
    bool t_trusted;                   // recent, in range and not frozen
    float i_cap;                      // total current cap in force (I_CAP_MA or I_CAP_UNTRUSTED_MA)
    uint16_t vbat_mv;
    uint8_t batt;                     // 0 ok, 1 low, 2 empty
    uint32_t below_empty_since, last_low_blink;
    // output
    float drive[G_COUNT];             // current output (after fades), 0..1 of full channel current
    float target[G_COUNT];
    float fade_from[G_COUNT];
    uint32_t fade_start;
    bool fade_active;                 // cleared when the fade completes, so a millis() wrap cannot restart it
    uint32_t blink_start;             // confirmation/low-battery blink window: start ...
    uint16_t blink_len;               // ... and length in ms (0 = no blink; no absolute deadline to wrap)
    float blink_level;
    bool save_request;                // main loop writes EEPROM when set
    uint32_t last_slew;               // thermal slew timestamp (per instance, not a function static)
} core_t;

void core_init(core_t *c, const saved_t *saved, uint32_t now);
void core_buttons(core_t *c, const bool pressed[BTN_COUNT], uint32_t now);
void core_temperature(core_t *c, bool ok, float temp_c, uint32_t now);
void core_battery(core_t *c, uint16_t vdd_mv, uint32_t now);
void core_tick(core_t *c, uint32_t now);         // updates c->drive[]

float level_fraction(uint8_t level);
float thermal_factor(float temp_c);
void mode_targets(uint8_t mode, uint8_t level, float cap, float i_cap_ma, float out[G_COUNT]);
float total_current_ma(const float drive[G_COUNT]);
uint8_t crc8(const uint8_t *p, uint8_t n);
void saved_make(saved_t *s, uint8_t mode, uint8_t level);
bool saved_valid(const saved_t *s);

// group sizes on the LED board (LEDs per group, all at the same drive)
extern const uint8_t GROUP_LEDS[G_COUNT];

#ifdef __cplusplus
}
#endif
