# Loggy
Four input channel data acquisition device as part of UQ's ENGG2800 Team Project I course.
![image5](https://github.com/user-attachments/assets/c2652dec-ee7c-4f25-ba55-043b2a7cf990)
![image2](https://github.com/user-attachments/assets/86f580f2-da47-4894-a557-aa4461093b21)

## Overview
Loggy is a four input channel data acquisition device operating at 168 Samples/second with input channels being rated to +/- 12V. Loggy also has four extra channel (CH5 -> CH8) with CH5,CH6,CH7 being the x,y,z acceleration values from the on board accelerometer respectively and CH8 being the ambient temperature.
Loggy also features two on board current sources (10uA and 200uA) for general use . As part of the project a complete GUI was required which would interface to the PCB via USB to allow users to view live data from their computer as well as configure the device. 

## Hardware
All hardware design was done by Rhett Humphreys. This included designing the digital and analog sections of the device as well as performing the layout, routing and assembly of the PCB.

## Firmware
Firmware was written by Zhe Gao. This included writing low level drivers for on board devices such as the ADCs, accelerometers and LED driver for alarms as well combining these drivers within the application code for Loggy.

## Software
The GUI software was jointly written by Luke Pidgeon and Sithika Mannakkara. The GUI was written in python and allows the user to view live plots of data read by Loggy as well as configure parameters of the device such as alarm thresholds and alarm types.
