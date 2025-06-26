/*
 * alarm.c
 *
 * Created: 2025/3/30 12:44:11
 *  Author: ZheGao
 */

#include "alarm.h"
#include "eeprom.h"

#include <avr/interrupt.h>
#include <avr/io.h>
#include <ctype.h>
#include <stdbool.h>
#include <util/delay.h>

// global of the latch bit to record
static uint16_t latchBits = 0;
// global of last alarm led bits status
static uint16_t ledBitsLast = 0;
// global of the led bits status
uint16_t ledBits = 0;
// global of alarm status of every channel
int alarmStatus[8] = { 0 };

/**
 *
 * init the alarm driver
 *
 *
 * return: None
 */
void init_pins()
{
    DDRD |= (1 << CLK_PIN) | (1 << SIN_PIN); // set CLK->PD2 SIN->PD3 as output
}

/**
 *
 * send the 1-bit data to alarm driver
 *
 *
 * bit: the 1 bits need to send to driver
 *
 *
 * return: None
 */

void send_bit(uint8_t bit)
{
    if (bit) {
        // set SIN is high when bit is '1'
        PORTD |= (1 << SIN_PIN);
    } else {
        // set SIN is low when bit is '0'
        PORTD &= ~(1 << SIN_PIN);
    }
    // create a increase and decrease edge for CLK
    PORTD |= (1 << CLK_PIN);
    PORTD &= ~(1 << CLK_PIN);
}

/**
 *
 * send the 16-bit data to alarm driver
 *
 *
 * bit: the 16 bits need to send to driver
 *
 *
 * return: None
 */
void alarm_send_data(uint16_t data)
{
    for (int i = 15; i >= 0; i--) {
        send_bit((data >> i) & 1);
    }
}

/**
 *
 * unlatch one channel
 *
 * channel : the channel need to be reset
 *
 *
 */
void reset_latched_alarm(uint8_t channel)
{
    // 01 set
    uint16_t setbit = 1 << (2 * (channel - 1));
    // 10 clr
    uint16_t clearbit = 1 << (2 * (channel - 1) + 1);
    // this channel not latch
    if (latchBits & setbit) {
        // clear it
        latchBits &= ~setbit;
        // clear the status
        alarmStatus[(channel - 1)] = 0;
        ledBits |= clearbit;
        ledBits &= ~setbit;
        // not same
        if (ledBits != ledBitsLast) {
            alarm_send_data(ledBits);
            ledBitsLast = ledBits;
            if (contSending && !onReplay) {
                char buf[64];
                sprintf(buf, "AS CH%u 0\r\n", (unsigned)channel);
                uart_send_string(buf);
            }
        }
    }
}

/**
 *
 * check the alarm happenes or not and send the alarm data to driver
 *
 *
 * conf: the config of loggy like alarm status and high/low limit
 * data: the latest data value like Vol Acc and Temp
 *
 *
 * return: None
 */
void check_alarm_threshold(Config conf, SensorData data)
{
    float test_data[8] = { data.adc[0], data.adc[1], data.adc[2], data.adc[3],
        data.Acc.x, data.Acc.y, data.Acc.z, data.temp };
    for (int i = 0; i < 8; i++) {
        // 00 disabled
        uint16_t disabledbits = 1 << (2 * i) | 1 << (2 * i + 1);
        // 01 set
        uint16_t setbits = 1 << (2 * i);
        // 10 clr
        uint16_t clearbits = 1 << (2 * i + 1);

        switch (conf.AlarmType[i]) {
        // 0000aa00|=00000100 -> 0000a100 &= ~(000011000) -> 00000100
        case ALARM_DISABLED:
            alarmStatus[i] = 0;
            ledBits &= ~disabledbits;
            break;
        // 0000aa00|=00000100 -> 0000a100 &= ~(00001000) -> 00000100
        case ALARM_LIVE:
            if (test_data[i] > conf.highThreshold[i]
                || test_data[i] < conf.lowThreshold[i]) {
                alarmStatus[i] = 1;
                ledBits |= setbits;
                ledBits &= ~clearbits;
            } else {
                alarmStatus[i] = 0;
                ledBits |= clearbits;
                ledBits &= ~setbits;
            }
            break;

        case ALARM_LATCHING:
            if (test_data[i] > conf.highThreshold[i]
                || test_data[i] < conf.lowThreshold[i]) {
                latchBits |= setbits;
            }
            if (latchBits & setbits) {
                alarmStatus[i] = 1;
                ledBits |= setbits;
                ledBits &= ~clearbits;
            } else {
                alarmStatus[i] = 0;
                ledBits |= clearbits;
                ledBits &= ~setbits;
            }
            break;
        }
    }
    // check the alarm change than last time
    if (ledBits != ledBitsLast) {
        alarm_send_data(ledBits);
        ledBitsLast = ledBits;
        // not connect not send data
        if (contSending && (!onReplay)) {
            for (int i = 0; i < 8; i++) {
                if (((ledBits >> (2 * i)) & 0x03) == 0x01) {
                    char buff[64];
                    sprintf(buff, "AS CH%d 1\r\n", (i + 1));
                    uart_send_string(buff);
                } else {
                    char buff[64];
                    sprintf(buff, "AS CH%d 0\r\n", (i + 1));
                    uart_send_string(buff);
                }
            }
        }
    }
}

/**
 * reset the alarm status like unlatch
 *
 *
 * return: None
 */
void reset_alarm()
{

    if (contSending && !onReplay) {
        for (int i = 0; i < 8; i++) {
            char buff[64];
            sprintf(buff, "AS CH%d 0\r\n", (i + 1));
            uart_send_string(buff);
        }
    }
    latchBits = 0;
    ledBitsLast = 0;
    ledBits = 0;
}
