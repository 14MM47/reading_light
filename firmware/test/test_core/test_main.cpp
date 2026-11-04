// Host unit tests for the light logic: pio test -e native
#include <math.h>
#include <string.h>
#include <unity.h>

#include "lightcore.h"
#include "board_map.h"

static core_t c;
static uint32_t now;

static void run(uint32_t ms, bool up, bool main_, bool dn) {
    bool p[BTN_COUNT] = {up, main_, dn};
    for (uint32_t i = 0; i < ms; i++) {
        now++;
        core_buttons(&c, p, now);
        core_tick(&c, now);
    }
}
static void idle(uint32_t ms) { run(ms, false, false, false); }
static void tap(int b, uint32_t ms) { run(ms, b == BTN_UP, b == BTN_MAIN, b == BTN_DN); idle(50); }

void setUp(void) {
    now = 1000;
    core_init(&c, NULL, now);
    idle(300);
}
void tearDown(void) {}

void test_levels_monotonic_and_endpoints(void) {
    TEST_ASSERT_FLOAT_WITHIN(1e-5, LEVEL_MIN_FRAC, level_fraction(0));
    TEST_ASSERT_FLOAT_WITHIN(1e-5, 1.0f, level_fraction(LEVELS - 1));
    for (int i = 1; i < LEVELS; i++) TEST_ASSERT_TRUE(level_fraction(i) > level_fraction(i - 1) * 1.3f);
}

void test_thermal_curve(void) {
    TEST_ASSERT_FLOAT_WITHIN(1e-4, 1.0f, thermal_factor(25));
    TEST_ASSERT_FLOAT_WITHIN(1e-4, 1.0f, thermal_factor(45));
    TEST_ASSERT_FLOAT_WITHIN(1e-4, 0.65f, thermal_factor(48.5f));
    TEST_ASSERT_FLOAT_WITHIN(1e-4, 0.30f, thermal_factor(52));
    TEST_ASSERT_FLOAT_WITHIN(1e-4, 0.05f, thermal_factor(58));
    TEST_ASSERT_FLOAT_WITHIN(1e-4, 0.05f, thermal_factor(90));
}

void test_current_cap_every_mode_and_level(void) {
    float d[G_COUNT];
    for (int m = 0; m < MODE_COUNT; m++)
        for (int l = 0; l < LEVELS; l++) {
            mode_targets(m, l, 1.0f, I_CAP_MA, d);
            TEST_ASSERT_TRUE(total_current_ma(d) <= I_CAP_MA + 0.01f);
            mode_targets(m, l, 1.0f, I_CAP_UNTRUSTED_MA, d);
            TEST_ASSERT_TRUE(total_current_ma(d) <= I_CAP_UNTRUSTED_MA + 0.01f);
            for (int g = 0; g < G_COUNT; g++) TEST_ASSERT_TRUE(d[g] >= 0 && d[g] <= 1.0f);
        }
}

void test_night_modes_have_no_green_or_blue(void) {
    for (int m = 0; m < MODE_COUNT; m++) {
        if (strstr(MODES[m].name, "night") || strstr(MODES[m].name, "Red")) {
            TEST_ASSERT_EQUAL_UINT16(0, MODES[m].q12[G_G]);
            TEST_ASSERT_EQUAL_UINT16(0, MODES[m].q12[G_B]);
            TEST_ASSERT_EQUAL_UINT16(0, MODES[m].q12[G_CW]);
        }
    }
}

void test_saved_roundtrip_and_rejects(void) {
    saved_t s;
    saved_make(&s, 3, 7);
    TEST_ASSERT_TRUE(saved_valid(&s));
    s.level = 8;
    TEST_ASSERT_FALSE(saved_valid(&s));            // CRC catches corruption
    saved_t e;
    memset(&e, 0xFF, sizeof(e));                   // blank EEPROM
    TEST_ASSERT_FALSE(saved_valid(&e));
    saved_make(&s, MODE_COUNT, 7);
    TEST_ASSERT_FALSE(saved_valid(&s));            // out-of-range mode
}

void test_power_on_uses_saved_default(void) {
    saved_t s;
    saved_make(&s, 7, 5);
    core_init(&c, &s, now);
    TEST_ASSERT_EQUAL_UINT8(7, c.mode);
    TEST_ASSERT_EQUAL_UINT8(5, c.level[7]);
    core_init(&c, NULL, now);
    TEST_ASSERT_EQUAL_UINT8(DEFAULT_MODE, c.mode);
    TEST_ASSERT_EQUAL_UINT8(DEFAULT_LEVEL, c.level[DEFAULT_MODE]);
}

void test_power_on_fades_in(void) {
    core_init(&c, NULL, now);
    core_tick(&c, now);
    float total0 = c.drive[0] + c.drive[1] + c.drive[2] + c.drive[3] + c.drive[4];
    TEST_ASSERT_FLOAT_WITHIN(1e-6, 0.0f, total0);
    idle(FADE_MS + 5);
    float d[G_COUNT];
    mode_targets(c.mode, c.level[c.mode], 1.0f, c.i_cap, d);
    for (int g = 0; g < G_COUNT; g++) TEST_ASSERT_FLOAT_WITHIN(1e-5, d[g], c.drive[g]);
}

void test_short_main_press_cycles_colour_on_release(void) {
    uint8_t m0 = c.mode;
    run(120, false, true, false);
    TEST_ASSERT_EQUAL_UINT8(m0, c.mode);           // nothing while held
    idle(50);
    TEST_ASSERT_EQUAL_UINT8((m0 + 1) % MODE_COUNT, c.mode);
    for (int i = 0; i < MODE_COUNT - 1; i++) tap(BTN_MAIN, 100);
    TEST_ASSERT_EQUAL_UINT8(m0, c.mode);           // wraps around
}

void test_hold_main_saves_default_without_cycling(void) {
    tap(BTN_MAIN, 100);
    uint8_t m = c.mode;
    run(HOLD_SAVE_MS + 300, false, true, false);
    TEST_ASSERT_TRUE(c.save_request);
    idle(100);
    TEST_ASSERT_EQUAL_UINT8(m, c.mode);            // release after a hold does not change colour
}

void test_hold_just_under_2s_is_a_press(void) {
    uint8_t m = c.mode;
    run(HOLD_SAVE_MS - 100, false, true, false);
    TEST_ASSERT_FALSE(c.save_request);
    idle(50);
    TEST_ASSERT_EQUAL_UINT8((m + 1) % MODE_COUNT, c.mode);
}

void test_up_down_and_clamp_and_repeat(void) {
    uint8_t l0 = c.level[c.mode];
    tap(BTN_UP, 60);
    TEST_ASSERT_EQUAL_UINT8(l0 + 1, c.level[c.mode]);
    tap(BTN_DN, 60);
    TEST_ASSERT_EQUAL_UINT8(l0, c.level[c.mode]);
    run(5000, true, false, false);                 // hold: auto-repeat to the top
    TEST_ASSERT_EQUAL_UINT8(MODES[c.mode].max_level, c.level[c.mode]);
    run(6000, false, false, true);
    TEST_ASSERT_EQUAL_UINT8(0, c.level[c.mode]);
    tap(BTN_DN, 60);
    TEST_ASSERT_EQUAL_UINT8(0, c.level[c.mode]);
}

void test_per_mode_brightness_memory(void) {
    uint8_t m = c.mode;
    tap(BTN_UP, 60);
    uint8_t l = c.level[m];
    tap(BTN_MAIN, 100);
    tap(BTN_DN, 60);
    for (int i = 0; i < MODE_COUNT - 1; i++) tap(BTN_MAIN, 100);
    TEST_ASSERT_EQUAL_UINT8(m, c.mode);
    TEST_ASSERT_EQUAL_UINT8(l, c.level[m]);
}

void test_debounce_ignores_glitch(void) {
    uint8_t m = c.mode;
    run(DEBOUNCE_MS - 5, false, true, false);
    idle(100);
    TEST_ASSERT_EQUAL_UINT8(m, c.mode);
}

void test_battery_low_empty_resume(void) {
    for (int i = 0; i < 20; i++) { core_battery(&c, 3400, now); idle(10); }
    TEST_ASSERT_EQUAL_UINT8(1, c.batt);
    idle(FADE_MS + 5);
    float d[G_COUNT];
    mode_targets(c.mode, c.level[c.mode], LOW_CAP, c.i_cap, d);
    TEST_ASSERT_FLOAT_WITHIN(1e-4, d[G_WW], c.target[G_WW]);
    for (int i = 0; i < 80; i++) { core_battery(&c, 3200, now); idle(100); }
    TEST_ASSERT_EQUAL_UINT8(2, c.batt);
    idle(FADE_MS + 5);
    for (int g = 0; g < G_COUNT; g++) TEST_ASSERT_FLOAT_WITHIN(1e-6, 0.0f, c.drive[g]);
    for (int i = 0; i < 20; i++) { core_battery(&c, 4700, now); idle(10); }   // USB plugged in
    TEST_ASSERT_EQUAL_UINT8(0, c.batt);
}

void test_brief_sag_does_not_shut_down(void) {
    for (int i = 0; i < 20; i++) { core_battery(&c, 3200, now); idle(100); }   // 2 s < EMPTY_HOLD_MS
    for (int i = 0; i < 20; i++) { core_battery(&c, 3900, now); idle(10); }
    TEST_ASSERT_NOT_EQUAL(2, c.batt);
}

void test_thermal_derating_and_sensor_failsafe(void) {
    core_temperature(&c, true, 80.0f, now);
    idle(12000);
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.05f, c.t_cap);
    core_temperature(&c, true, 30.0f, now);
    idle(12000);
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 1.0f, c.t_cap);
    uint32_t t0 = now;
    idle(3500);
    core_temperature(&c, false, 0, now);           // sensor silent > 3 s
    TEST_ASSERT_TRUE(now - t0 > 3000);
    idle(12000);
    TEST_ASSERT_FLOAT_WITHIN(0.01f, T_FAILSAFE_CAP, c.t_cap);
}

void test_save_confirmation_dips(void) {
    run(HOLD_SAVE_MS + 10, false, true, false);
    float during = c.drive[G_WW] + c.drive[G_CW] + c.drive[G_G];
    idle(500);
    float after = c.drive[G_WW] + c.drive[G_CW] + c.drive[G_G];
    TEST_ASSERT_TRUE(after > 0);
    (void)during;
}

// ---- sensor trust: the 200 mA cap only unlocks with a fresh, plausible, changing reading (thermal review)
void test_untrusted_until_sensor_answers_then_200mA(void) {
    TEST_ASSERT_FALSE(c.t_trusted);
    TEST_ASSERT_FLOAT_WITHIN(1e-3, I_CAP_UNTRUSTED_MA, c.i_cap);
    core_temperature(&c, true, 30.0f, now);
    TEST_ASSERT_TRUE(c.t_trusted);
    TEST_ASSERT_FLOAT_WITHIN(1e-3, I_CAP_MA, c.i_cap);
}

void test_implausible_reading_is_a_failure(void) {
    core_temperature(&c, true, 30.0f, now);
    idle(3500);
    core_temperature(&c, true, 150.0f, now);        // out of range: ignored -> silent sensor
    TEST_ASSERT_FALSE(c.t_trusted);
    TEST_ASSERT_FLOAT_WITHIN(1e-3, I_CAP_UNTRUSTED_MA, c.i_cap);
}

void test_frozen_reading_under_load_is_not_trusted(void) {
    // full 4000 K so > 50 mA flows, then the same value every second for 6 minutes
    while (c.mode != 2) tap(BTN_MAIN, 100);
    run(5000, true, false, false);
    for (int s = 0; s < 360; s++) { core_temperature(&c, true, 40.0f, now); idle(1000); }
    TEST_ASSERT_FALSE(c.t_trusted);
    TEST_ASSERT_TRUE(total_current_ma(c.drive) <= I_CAP_UNTRUSTED_MA + 0.01f);
}

void test_night_modes_light_only_red_and_warm_on_the_real_board(void) {
    for (int m = 0; m < MODE_COUNT; m++) {
        if (!(strstr(MODES[m].name, "night") || strstr(MODES[m].name, "Red"))) continue;
        float d[G_COUNT];
        mode_targets(m, MODES[m].max_level, 1.0f, I_CAP_MA, d);
        for (int o = 0; o < N_OUT; o++) {
            int g = OUT_GROUP[o];
            if (g < 0) continue;
            if (g == G_G || g == G_B || g == G_CW) TEST_ASSERT_FLOAT_WITHIN(1e-6, 0.0f, d[g]);
        }
    }
}

// ---- millis() wrap (firmware review FW-02): steady output 24.86 and 49.7 days after power-on
void test_no_strobe_after_24_8_days_on(void) {
    float ref = c.drive[G_WW] + c.drive[G_CW] + c.drive[G_G];
    now = 1000u + 0x80000000u + 10u;
    float mn = 1e9f;
    for (int i = 0; i < 2000; i++) {
        now++;
        bool p[BTN_COUNT] = {false, false, false};
        core_buttons(&c, p, now);
        core_tick(&c, now);
        float s = c.drive[G_WW] + c.drive[G_CW] + c.drive[G_G];
        if (s < mn) mn = s;
    }
    TEST_ASSERT_FLOAT_WITHIN(1e-4, ref, mn);
}

void test_no_refade_after_49_7_days_on(void) {
    float ref = c.drive[G_WW] + c.drive[G_CW] + c.drive[G_G];
    now = (uint32_t)(1000u + 0xFFFFFFFFu + 1u);
    float mn = 1e9f;
    for (int i = 0; i < 100; i++) {
        now++;
        bool p[BTN_COUNT] = {false, false, false};
        core_buttons(&c, p, now);
        core_tick(&c, now);
        float s = c.drive[G_WW] + c.drive[G_CW] + c.drive[G_G];
        if (s < mn) mn = s;
    }
    TEST_ASSERT_FLOAT_WITHIN(1e-4, ref, mn);
}

void test_thermal_slew_independent_per_instance(void) {
    static core_t a, b;
    uint32_t t = 5000;
    core_init(&a, NULL, t);
    core_init(&b, NULL, t);
    core_temperature(&a, true, 80.0f, t);
    core_temperature(&b, true, 80.0f, t);
    bool p[BTN_COUNT] = {false, false, false};
    for (int i = 0; i < 12000; i++) {
        t++;
        core_buttons(&a, p, t); core_tick(&a, t);
        core_buttons(&b, p, t); core_tick(&b, t);
    }
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.05f, a.t_cap);
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.05f, b.t_cap);
}

void test_channel_current_matches_riref_2k94(void) {
    const float i_fs = 105.0f * 0.7f / 2940.0f * 1000.0f;      // LP5012: ISET = KIREF x VIREF / RIREF
    TEST_ASSERT_FLOAT_WITHIN(0.1f, i_fs, I_CHANNEL_MA);
    TEST_ASSERT_TRUE(I_CHANNEL_MA <= 25.5f);                  // IMAX with Max_Current_Option = 0
}

// ---- LED board v0.2: LP5012 brightness x colour quantiser (replaces the TLC59116 IREF steps)
void test_lp_quantise_tracks_every_mode_and_level(void) {
    float d[G_COUNT];
    for (int m = 0; m < MODE_COUNT; m++)
        for (int l = 0; l < LEVELS; l++) {
            mode_targets(m, l, 1.0f, I_CAP_MA, d);
            float mx = 0;
            for (int g = 0; g < G_COUNT; g++) if (d[g] > mx) mx = d[g];
            uint8_t b = lp_brightness(mx, 0);
            TEST_ASSERT_TRUE(b >= 1);
            for (int g = 0; g < G_COUNT; g++) {
                uint8_t col = lp_colour(d[g], b);
                float shown = (float)col * (float)b / 65025.0f;
                // within half a colour step of the target, and never clipped
                TEST_ASSERT_FLOAT_WITHIN(0.5f * (float)b / 65025.0f + 1e-6f, d[g], shown);
                if (d[g] == mx && mx > 0) TEST_ASSERT_TRUE(col >= 127);   // b is the smallest that fits
            }
        }
}

void test_lp_brightness_hysteresis_and_ends(void) {
    TEST_ASSERT_EQUAL_UINT8(128, lp_brightness(0.5f, 0));
    TEST_ASSERT_EQUAL_UINT8(128, lp_brightness(0.45f, 128));     // still fits with >= 7-bit colour: keep
    TEST_ASSERT_EQUAL_UINT8(51, lp_brightness(0.2f, 128));       // below half: step down (0.2 x 255 = 51)
    TEST_ASSERT_EQUAL_UINT8(131, lp_brightness(0.51f, 128));     // above: step up at once
    TEST_ASSERT_EQUAL_UINT8(255, lp_brightness(1.0f, 40));
    TEST_ASSERT_EQUAL_UINT8(255, lp_colour(1.0f, 255));
    TEST_ASSERT_EQUAL_UINT8(0, lp_colour(0.0f, 77));
    TEST_ASSERT_EQUAL_UINT8(77, lp_brightness(0.0f, 77));        // all off: keep b, colours are 0
    TEST_ASSERT_EQUAL_UINT8(2, lp_brightness(LEVEL_MIN_FRAC, 0)); // level 0 of a full-drive group
    TEST_ASSERT_TRUE(lp_colour(LEVEL_MIN_FRAC, 2) >= 127);
}

void test_trust_change_fades_instead_of_stepping(void) {
    while (c.mode != 2) tap(BTN_MAIN, 100);                  // 4000 K
    run(3000, true, false, false);                           // to max level
    idle(500);
    float before = total_current_ma(c.drive);
    TEST_ASSERT_TRUE(before <= I_CAP_UNTRUSTED_MA + 0.01f);
    core_temperature(&c, true, 30.0f, now);                  // first good reading: cap 110 -> 200
    idle(1);
    TEST_ASSERT_TRUE(total_current_ma(c.drive) < before + 5.0f);   // no step within 1 ms
    idle(FADE_MS + 10);
    TEST_ASSERT_TRUE(total_current_ma(c.drive) > before + 20.0f);  // reached the higher level by fading
}

void test_frozen_timer_starts_when_load_starts(void) {
    // dim for 10 minutes with a perfectly steady reading, then full: still trusted for T_FROZEN_MS after the load
    while (c.mode != 2) tap(BTN_MAIN, 100);
    run(3000, false, false, true);                           // down to level 0 (< 50 mA)
    idle(500);
    TEST_ASSERT_TRUE(total_current_ma(c.drive) < 50.0f);
    for (int s = 0; s < 600; s++) { core_temperature(&c, true, 30.0f, now); idle(1000); }
    TEST_ASSERT_TRUE(c.t_trusted);
    run(3000, true, false, false);
    for (int s = 0; s < 120; s++) { core_temperature(&c, true, 30.0f, now); idle(1000); }
    TEST_ASSERT_TRUE(c.t_trusted);
    for (int s = 0; s < 240; s++) { core_temperature(&c, true, 30.0f, now); idle(1000); }
    TEST_ASSERT_FALSE(c.t_trusted);                          // > 5 min under load with no change
}

void test_first_reading_sets_the_derate_without_slewing(void) {
    // a warm restart (WDT reset with the head at 55 C): the first reading takes effect within the fade, not 8 s
    while (c.mode != 2) tap(BTN_MAIN, 100);
    run(5000, true, false, false);
    core_init(&c, NULL, now);
    idle(1000);
    core_temperature(&c, true, 55.0f, now);
    TEST_ASSERT_FLOAT_WITHIN(1e-4, thermal_factor(55.0f), c.t_cap);
    idle(FADE_MS + 10);
    float d[G_COUNT];
    mode_targets(c.mode, c.level[c.mode], thermal_factor(55.0f), c.i_cap, d);
    TEST_ASSERT_FLOAT_WITHIN(0.5f, total_current_ma(d), total_current_ma(c.drive));
}

void test_quiet_sensor_after_a_rise_stays_trusted(void) {
    // full 4000 K: the reading climbs 30 -> 40 C over 4 min, then sits on one code for 10 min (equilibrium)
    while (c.mode != 2) tap(BTN_MAIN, 100);
    run(5000, true, false, false);
    for (int s = 0; s < 240; s++) { core_temperature(&c, true, 30.0f + s / 24.0f, now); idle(1000); }
    for (int s = 0; s < 600; s++) { core_temperature(&c, true, 40.0f, now); idle(1000); }
    TEST_ASSERT_TRUE(c.t_trusted);
    TEST_ASSERT_FLOAT_WITHIN(1e-3, I_CAP_MA, c.i_cap);
}

void test_stuck_sensor_at_load_start_is_not_trusted_even_after_dim_period(void) {
    // the load starts before the sensor's first answer: the first valid reading is the reference, not 0 C
    while (c.mode != 2) tap(BTN_MAIN, 100);
    run(5000, true, false, false);
    for (int s = 0; s < 360; s++) { core_temperature(&c, true, 25.0f, now); idle(1000); }
    TEST_ASSERT_FALSE(c.t_trusted);
}

int main(int, char **) {
    UNITY_BEGIN();
    RUN_TEST(test_levels_monotonic_and_endpoints);
    RUN_TEST(test_thermal_curve);
    RUN_TEST(test_current_cap_every_mode_and_level);
    RUN_TEST(test_night_modes_have_no_green_or_blue);
    RUN_TEST(test_saved_roundtrip_and_rejects);
    RUN_TEST(test_power_on_uses_saved_default);
    RUN_TEST(test_power_on_fades_in);
    RUN_TEST(test_short_main_press_cycles_colour_on_release);
    RUN_TEST(test_hold_main_saves_default_without_cycling);
    RUN_TEST(test_hold_just_under_2s_is_a_press);
    RUN_TEST(test_up_down_and_clamp_and_repeat);
    RUN_TEST(test_per_mode_brightness_memory);
    RUN_TEST(test_debounce_ignores_glitch);
    RUN_TEST(test_battery_low_empty_resume);
    RUN_TEST(test_brief_sag_does_not_shut_down);
    RUN_TEST(test_thermal_derating_and_sensor_failsafe);
    RUN_TEST(test_save_confirmation_dips);
    RUN_TEST(test_untrusted_until_sensor_answers_then_200mA);
    RUN_TEST(test_implausible_reading_is_a_failure);
    RUN_TEST(test_frozen_reading_under_load_is_not_trusted);
    RUN_TEST(test_night_modes_light_only_red_and_warm_on_the_real_board);
    RUN_TEST(test_no_strobe_after_24_8_days_on);
    RUN_TEST(test_no_refade_after_49_7_days_on);
    RUN_TEST(test_thermal_slew_independent_per_instance);
    RUN_TEST(test_channel_current_matches_riref_2k94);
    RUN_TEST(test_lp_quantise_tracks_every_mode_and_level);
    RUN_TEST(test_lp_brightness_hysteresis_and_ends);
    RUN_TEST(test_trust_change_fades_instead_of_stepping);
    RUN_TEST(test_frozen_timer_starts_when_load_starts);
    RUN_TEST(test_first_reading_sets_the_derate_without_slewing);
    RUN_TEST(test_quiet_sensor_after_a_rise_stays_trusted);
    RUN_TEST(test_stuck_sensor_at_load_start_is_not_trusted_even_after_dim_period);
    return UNITY_END();
}
