#include "lightcore.h"

#include <math.h>
#include <string.h>

const uint8_t GROUP_LEDS[G_COUNT] = {4, 4, 2, 2, 2};

#define SAVED_MAGIC 0xA5
#define SAVED_VERSION 1

uint8_t crc8(const uint8_t *p, uint8_t n) {  // CRC-8/ATM, poly 0x07
    uint8_t c = 0;
    while (n--) {
        c ^= *p++;
        for (uint8_t i = 0; i < 8; i++) c = (c & 0x80) ? (uint8_t)((c << 1) ^ 0x07) : (uint8_t)(c << 1);
    }
    return c;
}

void saved_make(saved_t *s, uint8_t mode, uint8_t level) {
    s->magic = SAVED_MAGIC;
    s->version = SAVED_VERSION;
    s->mode = mode;
    s->level = level;
    s->crc = crc8((const uint8_t *)s, 4);
}

bool saved_valid(const saved_t *s) {
    return s && s->magic == SAVED_MAGIC && s->version == SAVED_VERSION && s->mode < MODE_COUNT &&
           s->level < LEVELS && s->crc == crc8((const uint8_t *)s, 4);
}

float level_fraction(uint8_t level) {
    if (level >= LEVELS) level = LEVELS - 1;
    // geometric steps from LEVEL_MIN_FRAC to 1.0 (equal perceived steps, ~0.55 stop each)
    return LEVEL_MIN_FRAC * powf(1.0f / LEVEL_MIN_FRAC, (float)level / (float)(LEVELS - 1));
}

float thermal_factor(float t) {
    if (t <= T_DERATE_START_C) return 1.0f;
    if (t <= T_DERATE_KNEE_C) return 1.0f - 0.70f * (t - T_DERATE_START_C) / (T_DERATE_KNEE_C - T_DERATE_START_C);
    if (t <= T_DERATE_MAX_C) return 0.30f - 0.25f * (t - T_DERATE_KNEE_C) / (T_DERATE_MAX_C - T_DERATE_KNEE_C);
    return 0.05f;
}

float total_current_ma(const float d[G_COUNT]) {
    float s = 0;
    for (int g = 0; g < G_COUNT; g++) s += d[g] * GROUP_LEDS[g] * I_CHANNEL_MA;
    return s;
}

void mode_targets(uint8_t mode, uint8_t level, float cap, float out[G_COUNT]) {
    if (mode >= MODE_COUNT) mode = 0;
    if (level > MODES[mode].max_level) level = MODES[mode].max_level;
    float f = level_fraction(level) * cap;
    for (int g = 0; g < G_COUNT; g++) out[g] = f * (float)MODES[mode].q12[g] / 4096.0f;
    float i = total_current_ma(out);
    if (i > I_CAP_MA) {
        float k = I_CAP_MA / i;
        for (int g = 0; g < G_COUNT; g++) out[g] *= k;
    }
}

static float limits(const core_t *c) {
    float cap = c->t_cap;
    if (c->batt == 1 && cap > LOW_CAP) cap = LOW_CAP;
    if (c->batt == 2) cap = 0.0f;
    return cap;
}

static void retarget(core_t *c, uint32_t now) {
    for (int g = 0; g < G_COUNT; g++) c->fade_from[g] = c->drive[g];
    mode_targets(c->mode, c->level[c->mode], limits(c), c->target);
    c->fade_start = now;
}

void core_init(core_t *c, const saved_t *saved, uint32_t now) {
    memset(c, 0, sizeof(*c));
    for (int m = 0; m < MODE_COUNT; m++) c->level[m] = MODES[m].default_level;
    if (saved_valid(saved)) {
        c->mode = saved->mode;
        c->level[c->mode] = saved->level;
    } else {
        c->mode = DEFAULT_MODE;
        c->level[c->mode] = DEFAULT_LEVEL;
    }
    c->t_cap = c->t_cap_target = 1.0f;
    c->t_last_ok = now;
    c->vbat_mv = 4000;
    retarget(c, now);   // fades in from 0 on power-up
}

static void press(core_t *c, int b, uint32_t now) {
    if (b == BTN_UP) {
        if (c->level[c->mode] < MODES[c->mode].max_level) c->level[c->mode]++;
        retarget(c, now);
    } else if (b == BTN_DN) {
        if (c->level[c->mode] > 0) c->level[c->mode]--;
        retarget(c, now);
    }
}

void core_buttons(core_t *c, const bool pressed[BTN_COUNT], uint32_t now) {
    for (int b = 0; b < BTN_COUNT; b++) {
        if (pressed[b] != c->raw[b]) {
            c->raw[b] = pressed[b];
            c->raw_since[b] = now;
        }
        bool st = c->stable[b];
        if (c->raw[b] != st && (uint32_t)(now - c->raw_since[b]) >= DEBOUNCE_MS) {
            c->stable[b] = c->raw[b];
            if (c->stable[b]) {                         // pressed
                c->pressed_at[b] = now;
                c->last_repeat[b] = now;
                if (b == BTN_MAIN) c->main_save_done = false;
                else press(c, b, now);
            } else if (b == BTN_MAIN) {                 // released
                if (!c->main_save_done && c->batt != 2) {
                    c->mode = (uint8_t)((c->mode + 1) % MODE_COUNT);
                    retarget(c, now);
                }
            }
        }
        if (c->stable[b]) {
            uint32_t held = now - c->pressed_at[b];
            if (b == BTN_MAIN) {
                if (!c->main_save_done && held >= HOLD_SAVE_MS) {
                    c->main_save_done = true;
                    c->save_request = true;
                    c->blink_until = now + 400;          // confirmation: two dips (see core_tick)
                    c->blink_level = 0.15f;
                }
            } else if (held >= REPEAT_DELAY_MS && (uint32_t)(now - c->last_repeat[b]) >= REPEAT_EVERY_MS) {
                c->last_repeat[b] = now;
                press(c, b, now);
            }
        }
    }
}

void core_temperature(core_t *c, bool ok, float temp_c, uint32_t now) {
    float target;
    if (ok) {
        c->t_valid = true;
        c->t_last_ok = now;
        target = thermal_factor(temp_c);
    } else if ((uint32_t)(now - c->t_last_ok) > 3000) {
        target = T_FAILSAFE_CAP;
    } else {
        return;
    }
    if (target < c->t_cap_target - 0.01f || target > c->t_cap_target + 0.01f) {
        c->t_cap_target = target;
    }
}

void core_battery(core_t *c, uint16_t vdd_mv, uint32_t now) {
    c->vbat_mv = (uint16_t)((c->vbat_mv * 3u + vdd_mv) / 4u);   // light IIR
    uint8_t before = c->batt;
    if (c->batt == 2) {
        if (c->vbat_mv >= VBAT_RESUME_MV) c->batt = 0;
    } else {
        if (c->vbat_mv < VBAT_EMPTY_MV) {
            if (!c->below_empty_since) c->below_empty_since = now ? now : 1;
            if ((uint32_t)(now - c->below_empty_since) >= EMPTY_HOLD_MS) c->batt = 2;
        } else {
            c->below_empty_since = 0;
        }
        if (c->batt != 2) {
            if (c->vbat_mv < VBAT_LOW_MV) c->batt = 1;
            else if (c->vbat_mv > VBAT_LOW_MV + 100) c->batt = 0;
        }
    }
    if (c->batt != before) retarget(c, now);
}

void core_tick(core_t *c, uint32_t now) {
    // thermal cap slews at ~10 %/s (0.0001 per 1 ms tick) so derating is gentle and invisible
    static uint32_t last_slew;
    float d = c->t_cap_target - c->t_cap;
    if ((d > 0.0005f || d < -0.0005f) && now != last_slew) {
        float step = (float)(now - last_slew) * 0.0001f;
        if (step > 0.01f) step = 0.01f;
        if (d < 0) step = -step;
        if ((d > 0 && step > d) || (d < 0 && step < d)) step = d;
        c->t_cap += step;
        bool fading = (uint32_t)(now - c->fade_start) < FADE_MS;
        mode_targets(c->mode, c->level[c->mode], limits(c), c->target);
        if (!fading)
            for (int g = 0; g < G_COUNT; g++) c->fade_from[g] = c->target[g];
    }
    last_slew = now;
    // low-battery reminder blink
    if (c->batt == 1 && (uint32_t)(now - c->last_low_blink) >= LOW_BLINK_EVERY_MS) {
        c->last_low_blink = now;
        c->blink_until = now + 200;
        c->blink_level = 0.25f;
    }
    float k = (float)(now - c->fade_start) / (float)FADE_MS;
    if (k > 1.0f) k = 1.0f;
    for (int g = 0; g < G_COUNT; g++) c->drive[g] = c->fade_from[g] + (c->target[g] - c->fade_from[g]) * k;
    if ((int32_t)(c->blink_until - now) > 0) {
        // dips: for the save confirmation two 100 ms dips inside 400 ms; for low battery one 200 ms dip
        uint32_t left = c->blink_until - now;
        bool dip = (c->blink_level < 0.2f) ? ((left / 100u) % 2u == 1u) : true;
        if (dip)
            for (int g = 0; g < G_COUNT; g++) c->drive[g] *= c->blink_level;
    }
}
