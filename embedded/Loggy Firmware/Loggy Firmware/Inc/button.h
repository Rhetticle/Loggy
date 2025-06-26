/*
 * button.h
 *
 * Created: 2025/4/2 9:23:36
 *  Author: ZheGao
 */

#ifndef BUTTON_H_
#define BUTTON_H_
#include "eeprom.h"
#include <stdbool.h>
#include <stdint.h>

extern volatile bool button1Pressed;

extern volatile bool button2Pressed;

extern volatile bool button3Pressed;

extern volatile int page;

extern Config LoggyConfig;

extern volatile bool offRec;

void button_init();

void change_scale(Config* loggy_config);

void check_scale(Config* loggy_config);

void check_button(Config* loggy_config);

#endif /* BUTTOM_H_ */
