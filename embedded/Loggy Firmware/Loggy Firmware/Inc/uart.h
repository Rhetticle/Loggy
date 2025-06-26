/*
 * uart.h
 *
 * Created: 2025/3/18 16:41:14
 *  Author:Zhe Gao
 */

#ifndef UART_H_
#define UART_H_

#include "accelerometer.h"
#include "eeprom.h"
#include <stdbool.h>

#define BAUD 103

// the buffer size of sending data
#define DATA_BUFFER 110

// the buffer size of sending config
#define CONFIG_BUFFER 100

// the buffer size of receive cmd from GUI
#define UART_BUFFER_SIZE 255

// the buffer size of sending the alarm
#define ALARM_BUFFER 50

// the length of queue receive cmd
#define UART_QUEUE_LENGTH 5

// the max char string length of received cmd
#define UART_QUEUE_STR_LENGTH 25

void USART_Init(unsigned int ubrr);

unsigned char USART_Receive(void);

void USART_Transmit(unsigned char data);

void uart_send_string(char* str);

void com_send_data(const SensorData* data);

void send_config(Config* config);

void process_command(char* cmd, Config* loggy_config);

extern Config LoggyConfig;

extern volatile uint8_t uartIndex;

extern volatile char uartBuffer[255];

extern volatile bool onReplay;

#endif /* UART_H_ */
