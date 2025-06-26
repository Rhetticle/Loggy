/*
 * adc.h
 *
 * Created: 2025/3/26 14:53:17
 *  Author: Zhe Gao
 */

#ifndef ADC_H_
#define ADC_H_

#include "eeprom.h"
#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

// address of ADS1115 chip
#define ADC_ADDRESS_1 0x49
#define ADC_ADDRESS_2 0x48

// basic setting for chip
#define ADDR_CONV 0
#define ADDR_CONF 1
#define ADDR_LOWTHRESH 2
#define ADDR_HIGHTHRESH 3
#define ADC_CONF_OS 0x8000
#define ADC_CONF_MUX1 0x0000
#define ADC_CONF_MUX2 0x3000
#define ADC_CONF_PGA 0x0600
#define ADC_CONF_MODE 0x0000
#define ADC_CONF_DR 0x00E0

// The constant value to calculate the temp
#define ADC_10_RESOLUTION 1023.0
#define TEMP_ADC_V 3.3
#define RESISTER_VALUE 12253.0
#define BETA_CONSTANT 1.0
#define BETA_TEMP_VALUE 3380
#define BETA_TEMP_25_NORMAL 298.15
#define BETA_TEMP_0_NORMAL 273.15
#define BETA_NORMAL_TEMP_VALUE 10000

// number of formula to calculate the vol
#define ADC_GAIN 10
#define ADC_DIVI 9.98
#define ADC_1_VREF 1.65
#define ADC_10_VREF 16.5
#define ADC_SCALE 1.024
#define ADC_16_RESOLUTION 32768.0

#define ADC_CALC_1V_SCALE_CHAN2_4(adc)                                \
    ((ADC_GAIN * (ADC_1_VREF + ((adc)*ADC_SCALE / ADC_16_RESOLUTION)) \
         - ADC_10_VREF)                                               \
        / ADC_DIVI)

#define ADC_CALC_10V_SCALE_CHAN2_4(adc)                              \
    (ADC_GAIN * (ADC_1_VREF + ((adc)*ADC_SCALE / ADC_16_RESOLUTION)) \
        - ADC_10_VREF)

#define ADC_CALC_1V_SCALE_CHAN1_3(adc)                                \
    ((ADC_GAIN * (ADC_1_VREF - ((adc)*ADC_SCALE / ADC_16_RESOLUTION)) \
         - ADC_10_VREF)                                               \
        / ADC_DIVI)

#define ADC_CALC_10V_SCALE_CHAN1_3(adc)                              \
    (ADC_GAIN * (ADC_1_VREF - ((adc)*ADC_SCALE / ADC_16_RESOLUTION)) \
        - ADC_10_VREF)

extern Config LoggyConfig;

int16_t read_adc_channel(uint8_t addr);

void select_adc_channel(uint8_t addr, uint16_t config);

void get_vol_values(SensorData* data, Config* loggy_config);

void adc_init(void);

uint16_t read_adc(void);

void wait_adc_chip1();

void wait_adc_chip2();

void get_temp_value(float* temp);

#endif /* INCFILE1_H_ */
