/*
 * uart.c
 *
 * Created: 2025/3/18 16:06:10
 *  Author: Zhe Gao
 */

#include "uart.h"
#include "accelerometer.h"
#include "alarm.h"
#include "button.h"
#include "eeprom.h"
#include <avr/interrupt.h>
#include <avr/io.h>
#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <util/delay.h>
//
//

// Queue to store commands from GUI for Loggy to process
volatile char cmdsToProcess[UART_QUEUE_LENGTH][UART_QUEUE_STR_LENGTH];
// Number of commands in cmdsToProcess
volatile uint8_t cmdsWaiting;
// Buffer to use to receive chars from GUI
volatile char uartBuffer[UART_BUFFER_SIZE];
// current index to write to for uart_buffer
volatile uint8_t uartIndex = 0;
// flag to show whether recording is on or off
volatile bool offRec = true;
// Flag to show GUI is connected (true when connected, false otherwise)
volatile bool contSending;
// Flag to stop send the data and set when replay
volatile bool onReplay = false;

/*
 * init the uart baud rate
 *
 * ubrr: this value is to set the baud rate
 *
 *
 * return: None
 */

void USART_Init(unsigned int ubrr)
{
    UBRR0H = (unsigned char)(ubrr >> 8);
    UBRR0L = (unsigned char)ubrr;
    UCSR0B = (1 << RXEN0) | (1 << TXEN0) | (1 << RXCIE0);
    UCSR0C = (1 << UCSZ01) | (1 << UCSZ00); // 8 data bits, 1 stop bits
}

/**
 * receive the byte and return it
 *
 *
 * return: the byte we receive
 */
unsigned char USART_Receive(void)
{
    while (!(UCSR0A & (1 << RXC0))) // Wait for data to be received
        ;
    return UDR0; // Get and return received data from the buffer
}

/**
 * transmit the byte we want to send
 *
 *
 * data:  what we want to send
 *
 * return: None
 *
 */
void USART_Transmit(unsigned char data)
{

    // Wait for the transmit buffer to be empty
    while (!(UCSR0A & (1 << UDRE0)))
        ;
    UDR0 = data; // Send data
}

/**
 * this function is to send the string
 *
 *
 * return: None
 *
 */
void uart_send_string(char* str)
{
    while (*str) {
        USART_Transmit(*(str++));
    }
}

/**
 * this function is to process the cmd from the GUI
 *
 * cmd: the cmd we receive
 * loggy_config: the basic config from the loggy might be changed in processing
 *
 *
 * return: None
 *
 */
void process_command(char* cmd, Config* loggyConfig)
{
    // receive start cont
    if (strncmp(cmd, "START CONT", 10) == 0) {
        uart_send_string("RECEIVED\r\n");
        load_config_from_eeprom(loggyConfig);
        // send the config
        send_config(loggyConfig);
        reset_alarm();
        onReplay = false;
        uart_send_string("END CONT\r\n");
        contSending = true;
        return;
    }
    // receive stop cont
    if (strncmp(cmd, "STOP CONT", 9) == 0) {
        contSending = false;
        return;
    }

    // receive stop cont
    if (strncmp(cmd, "RPY ON", 6) == 0) {
        onReplay = true;
        return;
    }

    // range change request
    if ((strncmp(cmd, "V0", 2) == 0) || (strncmp(cmd, "V1", 2) == 0)) {
        change_scale(loggyConfig);
        return;
    }
    if (strncmp(cmd, "AHT CH", 6) == 0) {
        char* param = cmd + 6;
        int channel = 0;
        if (*param && isdigit((unsigned char)*param)) {
            channel = *param - '0';
            param++; // pass the channel number
            param++; // pass the space after the channel number
        }
        float value = atof(param); // convert char to float
        if (channel >= 1 && channel <= 8) {
            loggyConfig->highThreshold[channel - 1] = value;
            save_config_to_eeprom(loggyConfig); // put it into save
            char buff[ALARM_BUFFER];
            sprintf(buff, "AHT CH%d %.3f\r\n", channel, value);
            uart_send_string(buff);
            reset_latched_alarm(channel);
        } else {
            uart_send_string("Invalid parameter\n");
        }
    }
    if (strncmp(cmd, "ALT CH", 6) == 0) {
        char* param = cmd + 6;
        int channel = 0;
        if (*param && isdigit((unsigned char)*param)) {
            channel = *param - '0';
            param++; // pass the channel number
            param++; // pass the space after the channel number
        } else {
            uart_send_string("not digit or param error\r\n");
        }
        float value = atof(param);
        if (channel >= 1 && channel <= 8) {
            loggyConfig->lowThreshold[channel - 1] = value;
            save_config_to_eeprom(loggyConfig);
            char buff[ALARM_BUFFER];
            sprintf(buff, "ALT CH%d %.3f\r\n", channel, value);
            uart_send_string(buff);
            reset_latched_alarm(channel);
        } else {
            uart_send_string("Invalid parameter\r\n");
        }
    }
    if (strncmp(cmd, "AM CH", 5) == 0) {
        char* param = cmd + 5;
        int channel = 0;
        if (*param && isdigit((unsigned char)*param)) {
            channel = *param - '0';
            param++; // pass the channel number
            param++; // pass the space after the channel number
        }
        int alarmMode = atoi(param);
        if ((alarmMode >= ALARM_DISABLED) && (alarmMode <= ALARM_LATCHING)) {
            loggyConfig->AlarmType[channel - 1] = (AlarmType_t)alarmMode;
        }
    }

    if (strncmp(cmd, "REC ON", 6) == 0) {
        offRec = false;
    }

    if (strncmp(cmd, "REC OFF", 7) == 0) {
        offRec = true;
    }
    save_config_to_eeprom(loggyConfig);
}

/**
 * this function is to send the data to the GUI
 *
 * data: all eight channels data need to send
 *
 * return:None
 */
void com_send_data(const SensorData* data)
{
    if (contSending && (!onReplay)) {
        char buffer[DATA_BUFFER];
        // THE COMMAND "D" SHOULD NOT BE USED IN OTHER COMMAND
        sprintf(buffer, "D:%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\r\n",
            data->adc[0], data->adc[1], data->adc[2], data->adc[3],
            data->Acc.x, data->Acc.y, data->Acc.z, data->temp);
        uart_send_string(buffer);
    }
}

/**
 *
 *this function is to send the basic eeprom config to the GUI when start
 *
 * config: the basic config for the loggy
 *
 */
void send_config(Config* config)
{
    char buffer[CONFIG_BUFFER];
    sprintf(buffer,
        "HT: CH1:%.3f CH2:%.3f CH3:%.3f CH4:%.3f CH5:%.3f CH6:%.3f "
        "CH7:%.3f CH8:%.3f\r\n",
        config->highThreshold[0], config->highThreshold[1],
        config->highThreshold[2], config->highThreshold[3],
        config->highThreshold[4], config->highThreshold[5],
        config->highThreshold[6], config->highThreshold[7]);
    uart_send_string(buffer);

    sprintf(buffer,
        "LT: CH1:%.3f CH2:%.3f CH3:%.3f CH4:%.3f CH5:%.3f CH6:%.3f "
        "CH7:%.3f CH8:%.3f\r\n",
        config->lowThreshold[0], config->lowThreshold[1],
        config->lowThreshold[2], config->lowThreshold[3],
        config->lowThreshold[4], config->lowThreshold[5],
        config->lowThreshold[6], config->lowThreshold[7]);
    uart_send_string(buffer);

    for (int i = 0; i < ALARM_COUNT; i++) {
        sprintf(buffer, "AM CH%d %d\r\n", i + 1, config->AlarmType[i]);
        uart_send_string(buffer);
    }

    if (config->InputRange == RANGE_10V) {
        sprintf(buffer, "V1\r\n");
    } else {
        sprintf(buffer, "V0\r\n");
    }
    uart_send_string(buffer);
}

// interrupt function
ISR(USART_RX_vect)
{
    char receivedChar = UDR0;
    // receive a full command
    if (receivedChar == '#') {
        uartBuffer[uartIndex] = '\0';
        // if the cmd is STOP CONT then disconnected dis cont_sending
        if (!strcmp("STOP CONT", (char*)uartBuffer)) {
            contSending = false;
            uartIndex = 0;
            return;
        } else {
            // if the cmd is not OK
            strcpy((char*)cmdsToProcess[cmdsWaiting], (char*)uartBuffer);
            // put the cmd in to a 2-D string to store it to prevent so fast to
            // ignore something
            cmdsWaiting++;
            // flat to record the waiting cmd number
        }
        uartIndex = 0;
    } else if (uartIndex < UART_BUFFER_SIZE - 1) {
        uartBuffer[uartIndex++] = receivedChar;
    }
}
