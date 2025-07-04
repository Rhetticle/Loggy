/** 
 * ---------------------------------------------------------------+ 
 * @desc        HD44780 LCD Driver 
 * ---------------------------------------------------------------+ 
 *              Copyright (C) 2020 Marian Hrinko.
 *              Written by Marian Hrinko (mato.hrinko@gmail.com)
 *
 * @author      Marian Hrinko
 * @datum       18.11.2020
 * @file        hd44780.c
 * @tested      AVR Atmega16a
 *
 * @depend      
 * ---------------------------------------------------------------+
 * @usage       default set 16x2 LCD
 *              4-bit with 3 control wires (RW, RS, E)
 * 
 * This driver has been modified by ENGG2800 TEAM 3 to suit the 4x20 LCD
 */
#ifndef __HD44780_H__
#define __HD44780_H__

// Success
#ifndef SUCCESS
#define SUCCESS 0
#endif

// Error
#ifndef ERROR
#define ERROR 1
#endif

// E port
// --------------------------------------
#define HD44780_E 0
#define HD44780_PORT_E PORTB
#define HD44780_DDR_E DDRB
// RW port
// --------------------------------------
#define HD44780_RW 1
#define HD44780_PORT_RW PORTB
#define HD44780_DDR_RW DDRB
// RS port
// --------------------------------------
#define HD44780_RS 2
#define HD44780_PORT_RS PORTB
#define HD44780_DDR_RS DDRB
// DATA port / pin
// --------------------------------------
#define HD44780_DDR_DATA DDRD
#define HD44780_PORT_DATA PORTD
#define HD44780_PIN_DATA PIND
// pins
#define HD44780_DATA7 5 // LCD PORT DB7
#define HD44780_DATA6 6 // LCD PORT DB6
#define HD44780_DATA5 7 // LCD PORT DB5
#define HD44780_DATA4 4 // LCD PORT DB4
#define HD44780_DATA3 3 // LCD PORT DB3
#define HD44780_DATA2 2 // LCD PORT DB2
#define HD44780_DATA1 1 // LCD PORT DB1
#define HD44780_DATA0 0 // LCD PORT DB0

#define BIT7 0x80
#define BIT6 0x40
#define BIT5 0x20
#define BIT4 0x10
#define BIT3 0x08
#define BIT2 0x04
#define BIT1 0x02
#define BIT0 0x01

#define HD44780_BUSY_FLAG HD44780_DATA7
#define HD44780_INIT_SEQ 0x30
#define HD44780_DISP_CLEAR 0x01
#define HD44780_DISP_OFF 0x08
#define HD44780_DISP_ON 0x0C
#define HD44780_CURSOR_ON 0x0E
#define HD44780_CURSOR_OFF 0x0C
#define HD44780_CURSOR_BLINK 0x0F
#define HD44780_RETURN_HOME 0x02
#define HD44780_ENTRY_MODE 0x06
#define HD44780_4BIT_MODE 0x20
#define HD44780_8BIT_MODE 0x30
#define HD44780_2_ROWS 0x08
#define HD44780_FONT_5x8 0x00
#define HD44780_FONT_5x10 0x04
#define HD44780_POSITION 0x80
#define HD44780_SET_CGRAM 0x40

#define HD44780_SHIFT 0x10
#define HD44780_CURSOR 0x00
#define HD44780_DISPLAY 0x08
#define HD44780_LEFT 0x00
#define HD44780_RIGHT 0x04

#define HD44780_ROWS 2
#define HD44780_COLS 40

#define HD44780_ROW1_START 0x00
#define HD44780_ROW1_END HD44780_COLS
#define HD44780_ROW2_START 0x40
#define HD44780_ROW2_END HD44780_COLS

// **********************************************
//                      !!!
//      MODE DEFINITION - CORRECTLY DEFINED
//
// ----------------------------------------------
//
//  HD44780_4BIT_MODE - 4 bit mode / 4 data wires
//  HD44780_8BIT_MODE - 8 bit mode / 8 data wires
//
// **********************************************
#define HD44780_MODE HD44780_4BIT_MODE

// set bit
#define SETBIT(REG, BIT) (REG |= (1 << BIT))
// clear bit
#define CLRBIT(REG, BIT) (REG &= ~(1 << BIT))
// set port / pin if bit is set
#define SET_IF_BIT_IS_SET(REG, PORT, DATA, BIT) \
    {                                           \
        if ((DATA & BIT) > 0) {                 \
            SETBIT(REG, PORT);                  \
        }                                       \
    }

/************************************ ICON ADDRESSES ***************************************/

/**
   * @desc    LCD init - initialisation routine
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_Init(void);

/**
   * @desc    LCD display clear
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_DisplayClear(void);

/**
   * @desc    LCD display on
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_DisplayOn(void);

/**
   * @desc    LCD cursor on, display on
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_CursorOn(void);

/**
   * @desc    LCD cursor off
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_CursorOff(void);

/**
   * @desc    LCD cursor blink, cursor on, display on
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_CursorBlink(void);

/**
   * @desc    LCD draw char
   *
   * @param  char
   * @return  void
   */
void HD44780_DrawChar(char character);

/**
   * @desc    LCD draw string
   *
   * @param   char *
   *
   * @return  void
   */
void HD44780_DrawString(char* str);

/**
   * @desc    Got to position x,y
   *
   * @param   char
   * @param   char
   *
   * @return  char
   */
char HD44780_PositionXY(char x, char y);

/**
   * @desc    Shift cursor / display to left / right
   *
   * @param   char item {HD44780_CURSOR; HD44780_DISPLAY}
   * @param   char direction {HD44780_RIGHT; HD44780_LEFT}
   *
   * @return  char
   */
char HD44780_Shift(char item, char direction);

/**
   * @desc    Check Busy Flag (BF) in 8 bit mode
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_CheckBFin8bitMode(void);

/**
   * @desc    Check Busy Flag (BF) in 4 bit mode
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_CheckBFin4bitMode(void);

/**
   * @desc    LCD send instruction
   *
   * @param   unsigned short int
   *
   * @return  void
   */
void HD44780_SendInstruction(unsigned short int);

/**
   * @desc    LCD send data
   *
   * @param   unsigned short int
   *
   * @return  void
   */
void HD44780_SendData(unsigned short int);

/**
   * @desc    LCD send 4bits instruction in 4 bit mode
   *
   * @param   unsigned short int
   *
   * @return  void
   */
void HD44780_Send4bitsIn4bitMode(unsigned short int);

/**
   * @desc    LCD send 8bits instruction in 4 bit mode
   *
   * @param   unsigned short int
   *
   * @return  void
   */
void HD44780_Send8bitsIn4bitMode(unsigned short int);

/**
   * @desc    LCD send 8bits instruction in 8 bit mode
   *
   * @param   unsigned short int
   *
   * @return  void
   */
void HD44780_Send8bitsIn8bitMode(unsigned short int);

/**
   * @desc    LCD send upper nibble
   *
   * @param   unsigned short int
   *
   * @return  void
   */
void HD44780_SetUppNibble(unsigned short int);

/**
   * @desc    LCD send lower nibble
   *
   * @param   unsigned short int
   *
   * @return  void
   */
void HD44780_SetLowNibble(unsigned short int);

/**
   * @desc    LCD pulse E
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_PulseE(void);

/**
   * @desc    Set PORT DB4 to DB7
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_SetPORT_DATA4to7(void);

/**
   * @desc    Clear DDR DB4 to DB7
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_ClearDDR_DATA4to7(void);

/**
   * @desc    Set DDR DB4 to DB7
   *
   * @param   void
   *
   * @return  void
   */
void HD44780_SetDDR_DATA4to7(void);

#endif