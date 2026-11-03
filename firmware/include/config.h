// Hardware configuration: ATtiny3216 main board + LP5012/MCP9800 LED board v0.2 (see hardware/*/design.py).
#pragma once
#include <stdint.h>

#define F_CPU_NOTE "10 MHz (internal 20 MHz osc / 2), valid down to 2.7 V"

// I2C (TWI0 default pins: PB1 = SDA, PB0 = SCL)
#define I2C_HZ        100000UL
#define ADDR_LP5012   0x14   // LP5012 (0010 1 A1 A0), ADDR1 = ADDR0 = GND
#define ADDR_TSENSE   0x48   // MCP9800A0 (LM75-compatible registers), factory address 1001 000

// Buttons (to GND, internal pull-ups): PA6 = UP, PA5 = MAIN, PA4 = DOWN (see hardware/main-board/design.py)
#define PIN_BTN_UP    PIN_PA6
#define PIN_BTN_MAIN  PIN_PA5
#define PIN_BTN_DN    PIN_PA4
// LED-board supply switch Q4 (P-FET): LOW = LED board powered, HIGH/Hi-Z (R12 pull-up) = off
#define PIN_LED_EN_N  PIN_PB2
// MCP9800 thermostat: ALERT (open drain, active low, comparator mode) holds the LP5012 EN low (shutdown) above
// TSET and releases it below THYST; the LP5012 then restarts with its registers reset (re-initialised by firmware)
#define TSENSE_TSET_C  60
#define TSENSE_THYST_C 52
// MCP9800 CONFIG: 12-bit (0.0625 C, 240 ms per conversion, bits 6:5 = 11) so the frozen-sensor check sees the
// reading move; fault queue 2 (bits 4:3 = 01), active low, comparator mode, continuous (= LM75B layout for bits 4:0)
#define TSENSE_CONFIG  0x68
// Debug serial: USART0 alternate pins (TX = PA1, RX = PA2) -> header J4 pin 3
#define SERIAL_SWAP   1

#include "board_map.h"   // generated from hardware/led-board/design.py: LP5012 output -> LED group
