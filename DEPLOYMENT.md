# Deployment Guide - UAV Gas Source Localisation System

## Overview
This guide covers deploying the UAV gas source localisation system to Raspberry Pi devices for both the UAV and ground station.

## Prerequisites

### Hardware Required
- 2x Raspberry Pi 4B
- 2x MicroSD cards (32GB+ Class 10)
- 2x Heltec WiFi LoRa 32 V3.2 modules
- 1x SprintIR-WF-20 CO₂ sensor
- 1x DJI M350 RTK drone

### Software Required
- Raspberry Pi OS (64-bit recommended)
- Arduino IDE (for Heltec firmware upload)
- SSH access to Raspberry Pi devices

## Step 1: Raspberry Pi Setup

### 1.1 Flash Raspberry Pi OS
1. Download Raspberry Pi Imager
2. Flash Raspberry Pi OS to both SD cards
3. Enable SSH in imager or add `ssh` file to boot partition
4. Configure WiFi in imager or add `wpa_supplicant.conf`

### 1.2 Initial Pi Configuration
```bash
# SSH into each Pi
ssh pi@<pi-ip-address>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip python3-venv git -y
```

### 1.3 Download Project Code
```bash
# Clone or copy project to Pi
git clone <your-repo-url> uav-gas-localisation
# OR copy files via SCP:
# scp -r /path/to/project pi@<pi-ip>:~/uav-gas-localisation

cd uav-gas-localisation
```

### 1.4 Run Pi Setup Script
```bash
# Run the setup script (creates UART config, installs dependencies)
./setup_pi.sh

# Reboot to apply UART changes
sudo reboot
```

## Step 2: Hardware Connections

### 2.1 UAV Raspberry Pi Connections
```
SprintIR CO₂ Sensor → Pi UART5
  VCC → 5V
  GND → GND  
  TX  → GPIO12 (Pi RX)
  RX  → GPIO13 (Pi TX)

Heltec LoRa Module → Pi UART3
  VCC → 3.3V
  GND → GND
  TX  → GPIO4 (Pi RX)
  RX  → GPIO5 (Pi TX)
```

### 2.2 Ground Station Pi Connections
```
Heltec LoRa Module → Pi UART3
  VCC → 3.3V
  GND → GND
  TX  → GPIO4 (Pi RX)  
  RX  → GPIO5 (Pi TX)

Future: Wind sensor connections TBD
```

## Step 3: Heltec LoRa Firmware Upload

### 3.1 Arduino IDE Setup
1. Install Arduino IDE on your computer
2. Add Heltec ESP32 board package:
   - File → Preferences → Additional Board Manager URLs
   - Add: `https://github.com/Heltec-Aaron-Lee/WiFi_Kit_series/releases/download/0.0.7/package_heltec_esp32_index.json`
3. Install "RadioLib" library from Library Manager

### 3.2 Upload Firmware
1. Connect Heltec module via USB-C
2. Select board: "Heltec WiFi LoRa 32(V3)"
3. Open `heltec_firmware/lora_bridge.ino`
4. Upload to both LoRa modules (identical firmware)

### 3.3 Verify LoRa Communication
```bash
# Test LoRa modules (run on both Pis)
./test_lora.py listen

# From one Pi, send test packet
./test_lora.py interactive
> TEST,12345,Hello World
```

## Step 4: Sensor Testing

### 4.1 Test CO₂ Sensor (UAV Pi only)
```bash
# Test CO₂ sensor connection
./test_co2.py info

# Read CO₂ values for 30 seconds
./test_co2.py read

# Calibrate in clean air (optional)
./test_co2.py calibrate
```

### 4.2 Test Wind Sensor (Ground Station Pi)
```bash
# Currently simulated - no hardware test needed
cd ground_station
python3 -c "
from sensors.wind_sensor_reader import WindSensorReader
w = WindSensorReader()
print(w.read_wind())
"
```

## Step 5: System Integration Testing

### 5.1 Ground Station Test
```bash
cd ground_station
python3 main.py
# Should show:
# - LoRa connection established
# - Sending INIT packet
# - Periodic wind data transmission
```

### 5.2 UAV System Test
```bash
cd UAV
python3 main.py
# Should show:
# - CO₂ sensor connected
# - LoRa responder active
# - Receiving ground station packets
# - Sending UAV telemetry responses
```

## Step 6: DJI Integration (UAV Only)

### 6.1 Install DJI Payload SDK
```bash
# Follow DJI SDK installation guide
# This requires DJI developer account and SDK access
sudo apt install cmake build-essential
# Download and build DJI SDK
```

### 6.2 Configure DJI Connection
```bash
# Configure DJI SDK credentials
# Update UAV/dji_sdk/ modules with actual SDK calls
# Test GPS reading and waypoint commands
```

## Step 7: Production Deployment

### 7.1 Create System Services
```bash
# Create systemd service for auto-start
sudo tee /etc/systemd/system/uav-localisation.service > /dev/null << EOF
[Unit]
Description=UAV Gas Localisation System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/uav-gas-localisation/UAV
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl enable uav-localisation.service
sudo systemctl start uav-localisation.service
```

### 7.2 Log Monitoring
```bash
# View logs
sudo journalctl -u uav-localisation.service -f

# Check log files
tail -f /var/log/uav/uav_flight.jsonl
tail -f /var/log/ground_station/ground_station.jsonl
```

## Step 8: Field Testing

### 8.1 Pre-flight Checklist
- [ ] Both Pis powered and systems running
- [ ] LoRa communication established
- [ ] CO₂ sensor reading valid values
- [ ] DJI drone connected and armed
- [ ] GPS lock acquired
- [ ] Log files being written

### 8.2 Test Flight Procedure
1. Start ground station system
2. Verify INIT packet exchange
3. Start UAV system on drone
4. Arm drone and takeoff manually
5. Enable autonomous mode
6. Monitor telemetry and source estimation
7. Verify waypoint commands being sent to drone

## Troubleshooting

### Common Issues

**LoRa not communicating:**
- Check UART connections and permissions
- Verify identical firmware on both modules
- Check frequency settings for your region

**CO₂ sensor not responding:**
- Verify UART5 configuration
- Check baud rate (9600)
- Try sensor info command

**Permission denied on serial ports:**
- Add user to dialout group: `sudo usermod -a -G dialout pi`
- Reboot after group change

**High packet loss:**
- Adjust LoRa power settings
- Check antenna connections
- Reduce transmission frequency

### Log Analysis
```bash
# Parse JSON logs for analysis
cat /var/log/uav/uav_flight.jsonl | jq '.event' | sort | uniq -c

# Check communication statistics  
grep "TX_WIND" /var/log/ground_station/ground_station.jsonl | wc -l
```

## Performance Optimization

### LoRa Range Extension
- Increase spreading factor (7→12) for longer range
- Reduce bandwidth (125→62.5 kHz) 
- Increase TX power (within legal limits)

### System Reliability
- Implement watchdog timers
- Add heartbeat monitoring
- Configure automatic log rotation
- Set up remote monitoring via cellular/WiFi

### Power Management
- Configure Pi for low power mode
- Optimize CPU governor settings
- Use USB power monitoring
- Implement battery backup

## Maintenance

### Regular Tasks
- Check log disk usage
- Verify sensor calibration
- Test emergency stop procedures
- Update system packages
- Backup configuration files

### Sensor Maintenance
- Clean CO₂ sensor periodically
- Recalibrate in known clean air
- Check LoRa antenna connections
- Verify GPS accuracy

This completes the deployment guide. The system should now be ready for field testing and operation.
