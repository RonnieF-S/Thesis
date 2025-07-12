# UAV-Based Gas Source Localisation System

This project implements an autonomous UAV-based system to localise the emission source of a gas (e.g. CO₂). 

## Architecture
- **UAV**: Raspberry Pi 4B on DJI M350 RTK
- **Ground Station**: Raspberry Pi 4B with LoRa communication
- **Communication**: LoRa via Heltec WiFi LoRa32 V3.2 modules
- **Sensors**: SprintIR-WF-20 CO₂ sensor on UAV

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure UART ports on Raspberry Pi
3. Upload Heltec firmware to LoRa modules
4. Run ground station: `python ground_station/main.py`
5. Run UAV system: `python UAV/main.py`

## Communication Protocol
- Ground station sends WIND packets every 10 seconds
- UAV responds with GPS and CO₂ data
- CSV format over LoRa for lightweight transmission

## Project Structure
- `UAV/` - UAV control system
- `ground_station/` - Ground station system  
- `heltec_firmware/` - Arduino firmware for LoRa modules
- `docs/` - Documentation
