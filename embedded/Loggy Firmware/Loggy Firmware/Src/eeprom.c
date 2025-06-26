/*
 * eeprom.c
 *
 * Created: 2025/3/31 19:12:19
 *  Author: Zhe Gao
 */

#include "eeprom.h"
#include "accelerometer.h"
#include "uart.h"
#include <avr/eeprom.h>
#include <util/delay.h>

// use EEMEM macro here to give stored_config the "eeprom" section attribute
Config EEMEM StoredConfig;

/**
 * Save a Loggy configuration to eeprom
 *
 * config: Configuration struct to save to eeprom
 *
 * Return: None
 */
void save_config_to_eeprom(Config* config)
{
    eeprom_write_block(
        (const void*)config, (void*)&StoredConfig, sizeof(Config));
}

/**
 * Read a Loggy configuration from eeprom
 *
 * config: Configuration struct to save to
 *
 * Return: None
 */
void load_config_from_eeprom(Config* config)
{
    eeprom_read_block(
        (void*)config, (const void*)&StoredConfig, sizeof(Config));
}
