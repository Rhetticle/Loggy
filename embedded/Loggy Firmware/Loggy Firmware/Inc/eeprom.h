/*
 * eeprom.h
 *
 * Created: 2025/3/31 19:13:00
 *  Author: Zhe Gao
 */

#ifndef EEPROM_H_
#define EEPROM_H_
#include "accelerometer.h"

typedef enum {
    RANGE_1V = 0, // ±1V
    RANGE_10V = 1 // ±10V
} InputRange_t;

typedef enum {
    ALARM_DISABLED = 0,
    ALARM_LIVE = 1,
    ALARM_LATCHING = 2
} AlarmType_t;

typedef enum {
    CHANNEL_1 = 1,
    CHANNEL_2 = 2,
    CHANNEL_3 = 3,
    CHANNEL_4 = 4
} ChannelId_t;

typedef enum {
    CURRENT_10UA = 4,
    CURRENT_200UA = 5,
} CurrentSource_t;

typedef enum {
    RESISTOR_THERMISTOR = 2,
    RESISTOR_RTD = 3,
} ResistorType_t;

typedef enum {
    TEMP_MODE_DISABLED = 0,
    TEMP_MODE_ENABLED = 1,
} TempMode_t;

typedef struct {
    ChannelId_t channel;
    CurrentSource_t current_source;
    ResistorType_t resistor_type;
    TempMode_t temp_mode;
} ChannelConfig_t;

typedef struct {
    float highThreshold[8]; // 0-3 is voltage 0 - 3. 4-6 is acc xyz. 7 is
        // temperature
    float lowThreshold[8]; //
    AlarmType_t AlarmType[8]; // alarm mode
    InputRange_t InputRange;
    ChannelConfig_t TempChannel[4];
} Config;

typedef struct {
    float adc[4];
    AccelData Acc;
    float temp;
} SensorData;

extern SensorData sensor;

extern volatile uint8_t scaleMode;

extern volatile uint8_t alarmMode;

extern Config LoggyConfig;

void save_config_to_eeprom(Config* config);

void load_config_from_eeprom(Config* config);

/*void clear_eeprom(void);*/

#endif /* INCFILE1_H_ */
