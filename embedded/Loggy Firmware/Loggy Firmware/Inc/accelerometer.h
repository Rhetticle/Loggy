/*
 * accelerometer.h
 *
 * Created: 26/03/2025 2:27:45 PM
 *  Author: rhett
 */

#ifndef ACCELEROMETER_H
#define ACCELEROMETER_H

#include <stdint.h>
// I2C address of accelerometer is 0x18
#define ACC_I2C_ADDR 0b00011000

/*************************** REGISTER ADDRESSES *****************************/

// Who am I register address
#define WHO_AM_I_ADDR 0x0F
// Who am I register value (fixed to 0x33 from factory)
#define WHO_AM_I_VALUE 0x33
// acceleration data output registers
#define OUT_X_L 0x28
#define OUT_X_H 0x29
#define OUT_Y_L 0x2A
#define OUT_Y_H 0x2B
#define OUT_Z_L 0x2C
#define OUT_Z_H 0x2D
// address of first acceleration data register (OUT_X_L)
#define ACC_DATA_START_ADDR 0x28

// Control registers
#define CTRL_REG_0 0x1E
#define CTRL_REG_1 0x20
#define CTRL_REG_2 0x21
#define CTRL_REG_3 0x22
#define CTRL_REG_4 0x23
#define CTRL_REG_5 0x24
#define CTRL_REG_6 0x25

// Status regsiter
#define STATUS_REG 0x27

// CTRL_REG_1 bit positions
#define ODR0 4
#define ODR1 5
#define ODR2 6
#define ODR3 7
#define ZEN 2
#define YEN 1
#define XEN 0
#define ODR_MASK 0x0F

// CTRL_REG_4 bit positions
#define FS1 5
#define FS0 4
#define HR 3
#define ST1 2
#define ST0 1
#define SIM 0

#define FS_POS 4
#define FS_MASK 0x30

// Measurement range modes
#define ACC_RANGE_2G 0x00
#define ACC_RANGE_4G 0x01
#define ACC_RANGE_8G 0x02
#define ACC_RANGE_16G 0x03

// Measurement data rate modes
#define ACC_RATE_1HZ 0x01
#define ACC_RATE_10HZ 0x02
#define ACC_RATE_25HZ 0x03
#define ACC_RATE_50HZ 0x04
#define ACC_RATE_100HZ 0x05
#define ACC_RATE_200HZ 0x06
#define ACC_RATE_400HZ 0x07

// Acceleration status's
#define ACC_OK 0
#define ACC_WRITE_ERROR 1
#define ACC_READ_ERROR 2
#define ACC_WHO_AM_I_ERROR 3

#define ACC_DATA_BYTE_COUNT 6 // 2 bytes for each axis, 3 axes

// conversion rate from raw acceleration to g's
#define ACC_CONV_RATE 0.001

#define RIGHT_SHIFT 4

#define ACC_ADDR 0X28

#define G_CONVERSION 9.8f

typedef struct {
    float x;
    float y;
    float z;
} AccelData;

uint8_t accelerometer_init(void);
uint8_t accelerometer_read(AccelData* data);
uint8_t accelerometer_self_test(void);
#endif /* LIS3DHTR_H_ */
