// Hardware configuration: ATtiny3216 main board + TLC59116/LM75B LED board (see hardware/*/design.py).
#pragma once
#include <stdint.h>

#define F_CPU_NOTE "10 MHz (internal 20 MHz osc / 2), valid down to 2.7 V"

// I2C (TWI0 default pins: PB1 = SDA, PB0 = SCL)
#define I2C_HZ        100000UL
#define ADDR_TLC      0x60   // TLC59116, A3..A0 = GND
#define ADDR_LM75     0x48   // LM75B, A2..A0 = GND

// Buttons (to GND, internal pull-ups): PA6 = UP, PA5 = MAIN, PA4 = DOWN (see hardware/main-board/design.py)
#define PIN_BTN_UP    PIN_PA6
#define PIN_BTN_MAIN  PIN_PA5
#define PIN_BTN_DN    PIN_PA4
// Debug serial: USART0 alternate pins (TX = PA1, RX = PA2) -> header J4 pin 3
#define SERIAL_SWAP   1

#include "board_map.h"   // generated from hardware/led-board/design.py: TLC59116 outputs per LED group
