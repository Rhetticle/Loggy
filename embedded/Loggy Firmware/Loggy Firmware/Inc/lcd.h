#ifndef LCD_H
#define LCD_H
#include "alarm.h"
#include "eeprom.h"
#include "hd44780.h"
#include <stdbool.h>

extern int alarmStatus[ALARM_COUNT];

// buffer size for writing strings to LCD (max line length is 20 so 25 should be
// enough)
#define BUFF_SIZE 25

// channel reading X,Y positions on LCD
#define CH1_X 0
#define CH1_Y 0
#define CH2_X 0
#define CH2_Y 1
#define CH3_X 20
#define CH3_Y 0
#define CH4_X 20
#define CH4_Y 1
#define CH5_X 0
#define CH5_Y 0
#define CH6_X 0
#define CH6_Y 1
#define CH7_X 20
#define CH7_Y 0
#define CH8_X 20
#define CH8_Y 1

// X,Y positions for range setting on LCD
#define RANGE1_X 18
#define RANGE1_Y 0
#define RANGE10_X 17
#define RANGE10_Y 0

// X,Y positions for connected symbol
#define CONNECT_X 38
#define CONNECT_Y1 0
#define CONNECT_Y2 1

// addresses of special characters used for disconnect/connect symbol
#define FIRST_CHAR 0X00
#define SECOND_CHAR 0X01
#define THIRD_CHAR 0X02
#define FOURTH_CHAR 0X03
#define FIFTH_CHAR 0X04
#define SIXTH_CHAR 0x05
#define SEVENTH_CHAR 0x06

// indeces for each alarm in alarm_status array
#define ALARM1_INDEX 0
#define ALARM2_INDEX 1
#define ALARM3_INDEX 2
#define ALARM4_INDEX 3
#define ALARM5_INDEX 4
#define ALARM6_INDEX 5
#define ALARM7_INDEX 6
#define ALARM8_INDEX 7

void HD44780_ClearDDR_DATA4to7(void);

void HD44780_create_icons(void);

void HD44780_draw_connected(void);

void HD44780_draw_disconnected(void);

void Display_ac_tem_value(float acceler1, float acceler2, float acceler3,
    float temperature, int alarm_status[]);

void Display_ADC_Values(
    float adc1, float adc2, float adc3, float adc4, int alarm_status[]);

void Display_range_value(Config* loggy_config);

void show_connected_icon(bool connected);

extern Config LoggyConfig;

void show_lcd(int page, SensorData data, int alarm_status[]);

#endif
