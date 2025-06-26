/*
 * accelerometer.c
 *
 * Created: 26/03/2025 2:27:30 PM
 *  Author: rhett
 *    PART: LIS3DHTR
 */
#include "accelerometer.h"
#include "twi_hal.h"
#include <avr/io.h>
#include <stdint.h>
#include <util/delay.h>

/**
 * Initialise accelerometer
 *
 * Initialises accelerometer to 16G range with max data rate
 */
uint8_t accelerometer_init(void)
{
    uint8_t ctr1Data = (0 << ODR2) | (1 << ODR1) | (0 << ODR0) | (1 << ZEN)
        | (1 << YEN) | (1 << XEN); // 10HZ
    uint8_t ctr4Data = (0 << FS1) | (0 << FS0)
        | (1 << HR); // 2g range and high resolution

    if (hal_i2c_write(ACC_I2C_ADDR, CTRL_REG_1, &ctr1Data, 1) != 0) {
        // error
        return ACC_WRITE_ERROR;
    }

    if (hal_i2c_write(ACC_I2C_ADDR, CTRL_REG_4, &ctr4Data, 1) != 0) {
        // error
        return ACC_WRITE_ERROR;
    }
    return ACC_OK;
}

/**
 * Read data from accelerometer (All 3 axes)
 *
 * data: AccelData struct to store axis acceleration
 */
uint8_t accelerometer_read(AccelData* data)
{
    // six byte array to store acceleration data
    uint8_t accRaw[ACC_DATA_BYTE_COUNT] = { 0 };
    int16_t xAcc, yAcc, zAcc;

    for (uint8_t i = 0; i < ACC_DATA_BYTE_COUNT; i++) {
        hal_i2c_read(ACC_I2C_ADDR, i + ACC_ADDR, &accRaw[i], 1);
        _delay_us(100);
    }
    xAcc = (((int16_t)accRaw[1]) << 8) | accRaw[0];
    yAcc = (((int16_t)accRaw[3]) << 8) | accRaw[2];
    zAcc = (((int16_t)accRaw[5]) << 8) | accRaw[4];

    xAcc >>= RIGHT_SHIFT;
    yAcc >>= RIGHT_SHIFT;
    zAcc >>= RIGHT_SHIFT;

    data->x = ((float)xAcc) * 0.001f * G_CONVERSION;
    data->y = ((float)yAcc) * 0.001f * G_CONVERSION;
    data->z = ((float)zAcc) * 0.001f * G_CONVERSION;

    return ACC_OK;
}

/**
 * Set accelerometer range
 *
 * range: Range to set accelerometer (ACC_RANGE_2G etc)
 */
uint8_t accelerometer_set_range(uint8_t range)
{
    uint8_t ctr4Reg;

    if (hal_i2c_read(ACC_I2C_ADDR, CTRL_REG_4, &ctr4Reg, sizeof(uint8_t))
        != 0) {
        return ACC_READ_ERROR;
    }
    ctr4Reg &= ~(FS_MASK);
    ctr4Reg |= range;

    if (hal_i2c_write(ACC_I2C_ADDR, CTRL_REG_4, &ctr4Reg, sizeof(uint8_t))
        != 0) {
        return ACC_WRITE_ERROR;
    }
    return ACC_OK;
}

/**
 * Set data rate of accelerometer
 *
 * rate: Rate to set too (ACC_RATE_100HZ etc)
 */
uint8_t accelerometer_set_data_rate(uint8_t rate)
{
    uint8_t ctr1Reg;

    if (hal_i2c_read(ACC_I2C_ADDR, CTRL_REG_1, &ctr1Reg, sizeof(uint8_t))
        != 0) {
        return ACC_READ_ERROR;
    }
    ctr1Reg &= ~(ODR_MASK);
    ctr1Reg |= rate;

    if (hal_i2c_write(ACC_I2C_ADDR, CTRL_REG_1, &ctr1Reg, sizeof(uint8_t))
        != 0) {
        return ACC_WRITE_ERROR;
    }
    return ACC_OK;
}

/**
 * Simple self test for accelerometer. Reads the whoAmI register from the
 * accelerometer Who am I register should be set to 0x33 by default
 *
 * Returns ACC_OK if whoAmI register value read matched the expected 0x33
 */
uint8_t accelerometer_self_test(void)
{
    uint8_t whoAmI;

    if (hal_i2c_read(ACC_I2C_ADDR, WHO_AM_I_ADDR, &whoAmI, sizeof(uint8_t))
        != 0) {
        return ACC_READ_ERROR;
    }

    if (whoAmI != WHO_AM_I_VALUE) {
        // whoAmI value we read did not match the expected 0x33
        return ACC_WHO_AM_I_ERROR;
    }
    return ACC_OK;
}
