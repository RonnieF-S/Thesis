"""
Project Configuration
Hardware ports and communication settings
"""

# Hardware Port Configurations
GPS_PORT = '/dev/ttyAMA5'
GPS_BAUDRATE = 9600

WIND_VANE_PORT = '/dev/ttyUSB0'
WIND_VANE_BAUDRATE = 4800

LORA_PORT = '/dev/ttyAMA3'
LORA_BAUDRATE = 115200

CO2_PORT = '/dev/ttyAMA5'
CO2_BAUDRATE = 9600

COMPASS_I2C_BUS = 1
COMPASS_I2C_ADDRESS = 0x1E

# Communication Settings
WIND_PACKET_INTERVAL = 10  # seconds
LORA_TIMEOUT = 5          # seconds
GPS_TIMEOUT = 60          # seconds for fix
SENSOR_READ_INTERVAL = 0.1  # seconds

# System Settings
LOG_LEVEL = 'INFO'
DEBUG_MODE = False
