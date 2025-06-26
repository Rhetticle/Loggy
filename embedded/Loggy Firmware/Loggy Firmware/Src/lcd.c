#include "lcd.h"
#include "alarm.h"
#include "hd44780.h"

// Disconnect/connect icon bitmaps
static const uint8_t connectedTopLeft[]
    = { 0x01, 0x01, 0x03, 0x07, 0x0D, 0x09, 0x09, 0x09 };
static const uint8_t connectedTopRight[]
    = { 0x10, 0x10, 0x10, 0x10, 0x18, 0x1C, 0x16, 0x12 };
static const uint8_t connectedBotLeft[]
    = { 0x1D, 0x1D, 0x01, 0x01, 0x01, 0x01, 0x03, 0x01 };
static const uint8_t connectedBotRight[]
    = { 0x12, 0x12, 0x17, 0x17, 0x17, 0x10, 0x18, 0x10 };
static const uint8_t disconnectedTopRight[]
    = { 0x10, 0x11, 0x13, 0x16, 0x1C, 0x1C, 0x16, 0x12 };
static const uint8_t disconnectedBotLeft[]
    = { 0x1D, 0x1D, 0x03, 0x07, 0x0D, 0x19, 0x13, 0x01 };
static const uint8_t alarmIcon[]
    = { 0x04, 0x0E, 0x11, 0x11, 0x11, 0x1F, 0x04, 0x00 };

/**
 * Inittialise the custom icon by writing the icon's bitmap
 * into the LCD's CGRAM (Character generator RAM).
 */
void HD44780_write_custom_char(const uint8_t* bitmap, uint8_t addr)
{
    HD44780_SendInstruction(HD44780_SET_CGRAM + (8 * addr));

    for (uint8_t i = 0; i < 8; i++) {
        HD44780_SendData(bitmap[i]);
    }
}

/**
 * Write all custom characters to LCD on startup
 *
 */
void HD44780_create_icons(void)
{
    HD44780_write_custom_char(connectedTopLeft, 0);
    HD44780_write_custom_char(connectedTopRight, 1);
    HD44780_write_custom_char(connectedBotLeft, 2);
    HD44780_write_custom_char(connectedBotRight, 3);
    HD44780_write_custom_char(disconnectedTopRight, 4);
    HD44780_write_custom_char(disconnectedBotLeft, 5);
    HD44780_write_custom_char(alarmIcon, 6);
}

/**
 * Draw connected icon onto display
 *
 */
void HD44780_draw_connected(void)
{ // the connected icon
    // HD44780_DisplayClear();
    HD44780_PositionXY(CONNECT_X, CONNECT_Y1);
    HD44780_DrawChar(FIRST_CHAR);
    HD44780_DrawChar(SECOND_CHAR);
    HD44780_PositionXY(CONNECT_X, CONNECT_Y2);
    HD44780_DrawChar(THIRD_CHAR);
    HD44780_DrawChar(FOURTH_CHAR);
}

/**
 * Draw disconnected icon onto display
 *
 */
void HD44780_draw_disconnected(void)
{ // the disconnected icon
    HD44780_PositionXY(CONNECT_X, CONNECT_Y1);
    HD44780_DrawChar(FIRST_CHAR);
    HD44780_DrawChar(FIFTH_CHAR);
    HD44780_PositionXY(CONNECT_X, CONNECT_Y2);
    HD44780_DrawChar(SIXTH_CHAR);
    HD44780_DrawChar(FOURTH_CHAR);
}

/*
 * show ADC value in
 */
void Display_ADC_Values(
    float adc1, float adc2, float adc3, float adc4, int alarmStatus[])
{
    HD44780_DisplayClear();
    char buffer1[BUFF_SIZE];
    HD44780_PositionXY(CH1_X, CH1_Y);
    sprintf(buffer1, "CH1:%.3fV", adc1);
    HD44780_DrawString(buffer1);
    if (alarmStatus[ALARM1_INDEX] == 1) {
        HD44780_DrawChar(SEVENTH_CHAR);
    }

    char buffer2[BUFF_SIZE];
    HD44780_PositionXY(CH2_X, CH2_Y);
    sprintf(buffer2, "CH2:%.3fV", adc2);
    HD44780_DrawString(buffer2);
    if (alarmStatus[ALARM2_INDEX] == 1) {
        HD44780_DrawChar(SEVENTH_CHAR);
    }

    char buffer3[BUFF_SIZE];
    HD44780_PositionXY(CH3_X, CH3_Y);
    sprintf(buffer3, "CH3:%.3fV", adc3);
    HD44780_DrawString(buffer3);
    if (alarmStatus[ALARM3_INDEX] == 1) {
        HD44780_DrawChar(SEVENTH_CHAR);
    }

    char buffer4[BUFF_SIZE];
    HD44780_PositionXY(CH4_X, CH4_Y);
    sprintf(buffer4, "CH4:%.3fV", adc4);
    HD44780_DrawString(buffer4);
    if (alarmStatus[ALARM4_INDEX] == 1) {
        HD44780_DrawChar(SEVENTH_CHAR);
    }
}

/**
 * Display accelerometer and ambient temperature values on LCD
 *
 * acceler1: X axis
 * acceler2: y axis
 * acceler3: z axis
 * temperature: Ambient temp reading
 * alarm_status: Array of alarm statuses
 *
 * Return: None
 */
void Display_ac_tem_value(float acceler1, float acceler2, float acceler3,
    float temperature, int alarmStatus[])
{
    // clear display for new data
    HD44780_DisplayClear();

    // write x,y,z axis readings
    char buffer1[BUFF_SIZE] = { 0 };
    HD44780_PositionXY(CH5_X, CH5_Y);
    sprintf(buffer1, "CH5:%.3fm/s^2", acceler1);
    HD44780_DrawString(buffer1);
    if (alarmStatus[ALARM5_INDEX] == 1) {
        HD44780_DrawChar(SEVENTH_CHAR);
    }

    char buffer2[BUFF_SIZE] = { 0 };
    HD44780_PositionXY(CH6_X, CH6_Y);
    sprintf(buffer2, "CH6:%.3fm/s^2", acceler2);
    HD44780_DrawString(buffer2);
    if (alarmStatus[ALARM6_INDEX] == 1) {
        HD44780_DrawChar(SEVENTH_CHAR);
    }

    char buffer3[BUFF_SIZE] = { 0 };
    HD44780_PositionXY(CH7_X, CH7_Y);
    sprintf(buffer3, "CH7:%.3fm/s^2", acceler3);
    HD44780_DrawString(buffer3);
    if (alarmStatus[ALARM7_INDEX] == 1) {
        HD44780_DrawChar(SEVENTH_CHAR);
    }
    // write ambient temperature reading
    char buffer4[BUFF_SIZE] = { 0 };
    HD44780_PositionXY(CH8_X, CH8_Y);
    sprintf(buffer4, "CH8:%.3fC", temperature);
    HD44780_DrawString(buffer4);
    if (alarmStatus[ALARM8_INDEX] == 1) {
        HD44780_DrawChar(SEVENTH_CHAR);
    }
}

/**
 * Display the range setting on LCD
 *
 * loggy_config: Loggy config struct loaded from eeprom
 *
 * Return: None
 */
void Display_range_value(Config* loggyConfig)
{
    if (loggyConfig->InputRange == RANGE_1V) {
        HD44780_PositionXY(RANGE1_X, RANGE1_Y);
        HD44780_DrawString("1V");
    } else {
        HD44780_PositionXY(RANGE10_X, RANGE10_Y);
        HD44780_DrawString("10V");
    }
}

/**
 * Show connected/disconnected icon on LCD
 *
 * connectFlag: True if GUI is connected to board false otherwise
 *
 * Return: None
 */
void show_connected_icon(bool connectFlag)
{
    if (connectFlag) {
        HD44780_draw_connected();
    } else {
        HD44780_draw_disconnected();
    }
}

/**
 * Show all paramemters for current LCD page
 *
 * page: 1 for CH1-CH4 readings, 0 for CH5-CH8 readings
 * data: Data struct containing most recent readings
 * alarm_status: Array of alarm statuses
 *
 * Return: None
 */
void show_lcd(int page, SensorData data, int alarmStatus[])
{
    if (page == 1) {
        Display_ADC_Values(data.adc[0], data.adc[1], data.adc[2], data.adc[3],
            alarmStatus);
    } else {
        Display_ac_tem_value(
            data.Acc.x, data.Acc.y, data.Acc.z, data.temp, alarmStatus);
    }
}
