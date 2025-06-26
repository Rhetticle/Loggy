/*
 * alarm.h
 *
 * Created: 2025/3/30 12:44:32
 *  Author: Zhe Gao
 */

#ifndef ALARM_H_
#define ALARM_H_
#include "eeprom.h"
#include "uart.h"
#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

// port of chip
#define CLK_PIN PD2
#define SIN_PIN PD3

// number of channel alarm
#define ALARM_COUNT 8

extern Config LoggyConfig;

extern int alarmStatus[8];

extern volatile bool contSending;

void init_pins();

void send_bit(uint8_t bit);

void alarm_send_data(uint16_t data);

void check_alarm_threshold(Config conf, SensorData data);

void reset_latched_alarm(uint8_t channel);

void reset_alarm(void);

#endif /* ALARM_H_ */
