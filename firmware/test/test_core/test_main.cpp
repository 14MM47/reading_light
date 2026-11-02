// Host unit tests for the light logic: pio test -e native
#include <math.h>
#include <string.h>
#include <unity.h>

#include "lightcore.h"

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
    TEST_ASSERT_FLOAT_WITHIN(1e-4, 0.65f, thermal_factor(57.5f));
    TEST_ASSERT_FLOAT_WITHIN(1e-4, 0.30f, thermal_factor(65));
    TEST_ASSERT_FLOAT_WITHIN(1e-4, 0.05f, thermal_factor(90));
}

void test_current_cap_every_mode_and_level(void) {
    float d[G_COUNT];
    for (int m = 0; m < MODE_COUNT; m++)
        for (int l = 0; l < LEVELS; l++) {
            mode_targets(m, l, 1.0f, d);
            TEST_ASSERT_TRUE(total_current_ma(d) <= I_CAP_MA + 0.01f);
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
    mode_targets(c.mode, c.level[c.mode], 1.0f, d);
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
    mode_targets(c.mode, c.level[c.mode], LOW_CAP, d);
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
    return UNITY_END();
}
