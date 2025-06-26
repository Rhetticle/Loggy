/*
 * I2c.c
 *
 * Created: 2025/3/26 14:53:02
 *  Author: Zhe Gao
 */

#include "adc.h"
#include "button.h"
#include "eeprom.h"
#include "twi_hal.h"
#include <avr/io.h>
#include <math.h>
#include <stdio.h>
#include <util/delay.h>

/**
 * init the adc chip
 *
 *
 * return: None
 */
void adc_init(void)
{
    ADMUX = (1 << REFS0) | (1 << MUX2) | (1 << MUX1) | (1 << MUX0);
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);
    uint8_t low[2] = { 0x00, 0x00 };
    uint8_t high[2] = { 0x80, 0x00 };
    hal_i2c_write(ADC_ADDRESS_1, ADDR_LOWTHRESH, low, sizeof(low));
    hal_i2c_write(ADC_ADDRESS_1, ADDR_HIGHTHRESH, high, sizeof(high));
    hal_i2c_write(ADC_ADDRESS_2, ADDR_LOWTHRESH, low, sizeof(low));
    hal_i2c_write(ADC_ADDRESS_2, ADDR_HIGHTHRESH, high, sizeof(high));
}

/**
 * read the temp adc value
 *
 *
 * return: None
 */
uint16_t read_adc(void)
{
    ADCSRA |= (1 << ADSC);
    while (ADCSRA & (1 << ADSC))
        ;
    return ADC;
}

/**
 * calculate the temp value
 *
 *
 * temp: the temp value will be shown in the LCD after calculate
 *
 *
 * return: None
 */

void get_temp_value(float* temp)
{
    uint16_t adc7 = read_adc();
    float vout = (adc7 / ADC_10_RESOLUTION) * TEMP_ADC_V;
    float Rth = RESISTER_VALUE * (TEMP_ADC_V - vout) / vout;
    float tempK = BETA_CONSTANT
        / ((BETA_CONSTANT / BETA_TEMP_25_NORMAL)
            + (BETA_CONSTANT / BETA_TEMP_VALUE)
                * log(Rth / BETA_NORMAL_TEMP_VALUE));
    *temp = tempK - BETA_TEMP_0_NORMAL;
}

/**
 * select and set the suitable adc chip
 *
 *
 * addr: the address of the chip we want to read
 * config: the basic config of the chip
 *
 *
 * return: None
 */
void select_adc_channel(uint8_t addr, uint16_t config)
{
    uint8_t data[2];
    data[0] = (config >> 8) & 0xFF;
    data[1] = config & 0xFF;
    hal_i2c_write(addr, ADDR_CONF, data, 2);
}

/**
 * read the Vol adc value
 *
 *
 * addr: the address of the chip we want to read
 *
 *
 * return: return the adc value what we get
 */
int16_t read_adc_channel(uint8_t addr)
{
    uint8_t data[2];
    hal_i2c_read(addr, ADDR_CONV, data, 2);
    uint16_t data1 = ((uint16_t)data[0]) << 8;
    return (data1 | data[1]);
}

/**
 * wait the first chip adc conversion finished
 *
 *
 * return:None
 */
void wait_adc_chip1()
{
    while (PINB & (1 << PINB3))
        ;
    while (!(PINB & (1 << PINB3)))
        ;
    while (PINB & (1 << PINB3))
        ;
    while (!(PINB & (1 << PINB3)))
        ;
    while (PINB & (1 << PINB3))
        ;
    while (!(PINB & (1 << PINB3)))
        ;
    while (PINB & (1 << PINB3))
        ;
    while (!(PINB & (1 << PINB3)))
        ;
}

/**
 * wait the second chip adc conversion finished
 *
 *
 * return:None
 */
void wait_adc_chip2()
{
    while (PINB & (1 << PINB4))
        ;
    while (!(PINB & (1 << PINB4)))
        ;
    while (PINB & (1 << PINB4))
        ;
    while (!(PINB & (1 << PINB4)))
        ;
    while (PINB & (1 << PINB4))
        ;
    while (!(PINB & (1 << PINB4)))
        ;
    while (PINB & (1 << PINB4))
        ;
    while (!(PINB & (1 << PINB4)))
        ;
}

/**
 * calculate the voltage value based on the adc value
 *
 *
 * data: the data will be set as the vol value what we get
 * config: the basic config of the loggy like input range
 *
 *
 * return: None
 */

void get_vol_values(SensorData* data, Config* loggyConfig)
{
    // first address and CN1
    uint16_t config1
        = ADC_CONF_MUX1 | ADC_CONF_PGA | ADC_CONF_MODE | ADC_CONF_DR;
    select_adc_channel(ADC_ADDRESS_1, config1);
    wait_adc_chip1();
    int16_t adcOneRead = read_adc_channel(ADC_ADDRESS_1);
    if (loggyConfig->InputRange == RANGE_10V) {
        data->adc[0] = ADC_CALC_10V_SCALE_CHAN1_3(adcOneRead);
    } else {
        data->adc[0] = ADC_CALC_1V_SCALE_CHAN1_3(adcOneRead);
    }

    // first address and CN2
    uint16_t config2 = ADC_CONF_MUX2 | ADC_CONF_PGA | ADC_CONF_MODE
        | ADC_CONF_DR; // first address and
    select_adc_channel(ADC_ADDRESS_1, config2);
    wait_adc_chip1();
    int16_t adcTwoRead = read_adc_channel(ADC_ADDRESS_1);
    if (loggyConfig->InputRange == RANGE_10V) {
        data->adc[1] = ADC_CALC_10V_SCALE_CHAN2_4(adcTwoRead);
    } else {
        data->adc[1] = ADC_CALC_1V_SCALE_CHAN2_4(adcTwoRead);
    }

    // second address and CN3
    uint16_t config3 = ADC_CONF_MUX1 | ADC_CONF_PGA | ADC_CONF_MODE
        | ADC_CONF_DR; // second address and CN3
    select_adc_channel(ADC_ADDRESS_2, config3);
    wait_adc_chip2();
    int16_t adcThreeRead = read_adc_channel(ADC_ADDRESS_2);
    if (loggyConfig->InputRange == RANGE_10V) {
        data->adc[2] = ADC_CALC_10V_SCALE_CHAN1_3(adcThreeRead);
    } else {
        data->adc[2] = ADC_CALC_1V_SCALE_CHAN1_3(adcThreeRead);
    }

    // second address and CN4
    uint16_t config4 = ADC_CONF_MUX2 | ADC_CONF_PGA | ADC_CONF_MODE
        | ADC_CONF_DR; // second address and CN4
    select_adc_channel(ADC_ADDRESS_2, config4);
    wait_adc_chip2();
    int16_t adcFourRead = read_adc_channel(ADC_ADDRESS_2);
    if (loggyConfig->InputRange == RANGE_10V) {
        data->adc[3] = ADC_CALC_10V_SCALE_CHAN2_4(adcFourRead);
    } else {
        data->adc[3] = ADC_CALC_1V_SCALE_CHAN2_4(adcFourRead);
    }
}
