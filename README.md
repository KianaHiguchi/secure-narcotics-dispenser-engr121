# Secure Dispensing Prototype - ENGR 121

An embedded systems prototype developed for ENGR 121 that automates controlled dispensing using sensor inputs and a self-hosted web interface. Built in a 3-person team. 

## Overview
The system runs MicroPython on a Raspberry Pi Pico W and makes use of IR motion, ambient light, and temperature sensors. A web UI (HTML/CSS) is served directly from the device, enabling dispensing actions and real-time status feedback.

## Features
- Sensor integration via ADC
- Threshold-based detection and LED status indicators 
- On-device Wi-Fi access point with HTTP server
- Web-based UI for dispensing and monitoring 
- Real-time temperature tracking

## Notes
Educational prototype for a design course centered around hospital optimization
