/*
 * twi_hal.h
 *
 * Created: 2020/11/01 18:07:26
 *  Author: DevilBinder
 */

#ifndef TWI_HAL_H_
#define TWI_HAL_H_

#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define TWI_TIMEOUT 1600

#define TWI_START 0x08
#define TWI_RSTART 0x10
#define TWIT_ADDR_ACK 0x18
#define TWIT_ADDR_NACK 0x20
#define TWIT_DATA_ACK 0x28
#define TWIT_DATA_NACK 0x30

#define TWIR_ADDR_ACK 0x40
#define TWIR_ADDR_NACK 0x48
#define TWIR_DATA_ACK 0x50
#define TWIR_DATA_NACK 0x58

#define TWI_ERROR 0x38
#define TWI_NONE 0xF8

#define I2C_CLOCK 50000

enum {
    TWI_OK,
    TWI_ERROR_START,
    TWI_ERROR_RSTART,
    TWI_NACK
};

void hal_i2c_init(uint32_t speed);
uint8_t hal_i2c_write(uint8_t addr, uint8_t reg, uint8_t* data, uint16_t len);
uint8_t hal_i2c_read(uint8_t addr, uint8_t reg, uint8_t* data, uint16_t len);

#endif /* TWI_HAL_H_ */