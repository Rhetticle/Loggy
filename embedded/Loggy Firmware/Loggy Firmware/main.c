/*
 * main.c
 *
 * Created: 14/03/2025 10:04:23 AM
 * Author : rhett
 */

#include "accelerometer.h"
#include "adc.h"
#include "alarm.h"
#include "button.h"
#include "eeprom.h"
#include "lcd.h"
#include "twi_hal.h"
#include "uart.h"
#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdbool.h>
#include <util/delay.h>

#define SAMPLE_LED_TOGGLE()     \
    {                           \
        PORTC ^= (1 << PORTC3); \
    }
#define SAMPLE_LED_OFF()         \
    {                            \
        PORTC &= ~(1 << PORTC3); \
    }

// global to store board configuration
Config LoggyConfig;

// flag set true when board connects to GUI false otherwise
extern volatile bool contSending;

// Queue to store commands needed to be processed
extern volatile char cmdsToProcess[UART_QUEUE_LENGTH][UART_QUEUE_STR_LENGTH];
// Store the number of commands in cmdsToProcess
extern volatile uint8_t cmdsWaiting;

void hardware_init(void);

/**
 * Main super loop
 */
int main(void)
{
    hardware_init();

    while (1) {
        SensorData Data;
        SAMPLE_LED_TOGGLE();
        // get channel data
        get_vol_values(&Data, &LoggyConfig);
        accelerometer_read(&Data.Acc);
        get_temp_value(&Data.temp);
        SAMPLE_LED_TOGGLE();
        show_lcd(page, Data, alarmStatus);
        show_connected_icon(contSending);
        Display_range_value(&LoggyConfig);
        while (cmdsWaiting != 0) { // still have cmd wait to process
            TCCR1B &= ~((1 << CS11)
                | (1 << CS10)); // stop timer1 in order to influence I2C
            process_command(
                (char*)cmdsToProcess[cmdsWaiting - 1], &LoggyConfig);
            TCCR1B |= ((1 << CS11) | (1 << CS10));
            cmdsWaiting--;
        }
        // send channel data over UART
        com_send_data(&Data);
        check_button(&LoggyConfig);
        check_alarm_threshold(LoggyConfig, Data);
    }
}

/**
 * Initialise gpio and peripherals
 *
 * Return: None
 */
void hardware_init(void)
{
    sei();
    DDRC |= (1 << PORTC2) | (1 << PORTC3);
    DDRB &= ~((1 << PORTB3) | (1 << PORTB4));
    SAMPLE_LED_OFF();
    // init peripherals
    button_init();
    init_pins();
    USART_Init(BAUD);
    HD44780_Init();
    HD44780_DisplayOn();
    // create special lcd icon
    HD44780_create_icons();
    hal_i2c_init(I2C_CLOCK);
    accelerometer_init();
    adc_init();
    // clear all alarm LEDs, output is indeterminate at power up
    alarm_send_data(0x0000);
    // get config from eeprom
    load_config_from_eeprom(&LoggyConfig);
    // change set based on eeprom
    check_scale(&LoggyConfig);
}
