/*
 * button.c
 *
 * Created: 2025/4/2 9:23:21
 *  Author: ZheGao
 */

#include "button.h"
#include "eeprom.h"
#include "lcd.h"
#include "uart.h"
#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdbool.h>

// check button 1 change channel press or not
volatile bool button1Pressed = false;

// check button 2 change channel press or not
volatile bool button2Pressed = false;

// check button 3 change channel press or not
volatile bool button3Pressed = false;

// 1 for CH1-CH4 readings, 0 for CH5-CH8 readings
volatile int page = 1;

/**
 *
 * init the pushbutton
 *
 *
 * return:None
 *
 */
void button_init()
{
    // set for button 1
    DDRC &= ~(1 << PORTC1);
    PORTC |= (1 << PORTC1);
    PCICR |= (1 << PCIE1);
    PCMSK1 |= (1 << PCINT9);

    // set for button 2
    DDRC &= ~(1 << PORTC0);
    PORTC |= (1 << PORTC0);
    PCICR |= (1 << PCIE1);
    PCMSK1 |= (1 << PCINT8);

    // set for button 2
    DDRB &= ~(1 << PORTB5);
    PORTB |= (1 << PORTB5);
    PCICR |= (1 << PCIE0);
    PCMSK0 |= (1 << PCINT5);

    sei();
}

/**
 * change the voltage in range
 *
 * loggt_config: the config of the the loggy to check and change range
 *
 *
 * return: None
 *
 */
void change_scale(Config* loggyConfig)
{
    if (loggyConfig->InputRange == RANGE_10V) {
        PORTC |= (1 << PORTC2);
        if (!onReplay) {
            uart_send_string("V0\r\n");
        }
        loggyConfig->InputRange = RANGE_1V;
    } else if (loggyConfig->InputRange == RANGE_1V) {
        PORTC &= ~(1 << PORTC2);
        if (!onReplay) {
            uart_send_string("V1\r\n");
        }
        loggyConfig->InputRange = RANGE_10V;
    } else {
        PORTC &= ~(1 << PORTC2);
        loggyConfig->InputRange = RANGE_10V;
    }
    save_config_to_eeprom(loggyConfig);
}

/**
 * check the voltage range now and set the port in beginning
 *
 * loggt_config: the config of the the loggy to check and change range
 *
 *
 * return: None
 *
 */
void check_scale(Config* loggyConfig)
{
    DDRC |= (1 << PORTC2);
    if (loggyConfig->InputRange == RANGE_1V) {
        PORTC |= (1 << PORTC2);
    } else if (loggyConfig->InputRange == RANGE_10V) {
        PORTC &= ~(1 << PORTC2);
    }
    if (loggyConfig->AlarmType[0] != ALARM_DISABLED
        && loggyConfig->AlarmType[0] != ALARM_LATCHING
        && loggyConfig->AlarmType[0] != ALARM_LIVE) {
        loggyConfig->AlarmType[0] = ALARM_DISABLED;
    }
    save_config_to_eeprom(loggyConfig);
}

/**
 * if the button pressed then do some change like change page/scale/clear alarm
 *
 * loggt_config: save the change to the config
 *
 *
 * return: None
 *
 */
void check_button(Config* loggyConfig)
{

    if (button1Pressed) {
        HD44780_DisplayClear();
        button1Pressed = false;
        page = (page + 1) % 2;
    }

    if (button2Pressed) {
        HD44780_DisplayClear();
        button2Pressed = false;
        change_scale(loggyConfig);
    }

    if (button3Pressed) {
        reset_alarm();
        button3Pressed = false;
    }
}

/**
 *
 * the interrupt of the pb1 and pb2
 *
 */
ISR(PCINT1_vect)
{
    // check port status to find press or not
    if (PINC & (1 << PORTC1)) {
        button1Pressed = true;
    }
    // check port status to find press or not
    if (PINC & (1 << PORTC0)) {
        // when record not change the status
        if (offRec) {
            button2Pressed = true;
        }
    }
}

/**
 *
 * the interrupt of the pb3
 *
 */
ISR(PCINT0_vect)
{
    // check port status to find press or not
    if (PINB & (1 << PORTB5)) {
        button3Pressed = true;
    }
}
