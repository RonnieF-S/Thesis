"""
Wind Vane Reader - RS485 Modbus RTU
Lightweight implementation with background threading
"""

import time
import serial
import threading
from typing import Dict, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import WIND_VANE_PORT, WIND_VANE_BAUDRATE, SENSOR_READ_INTERVAL
from shared import SimpleLogger as logger

class WindSensorReader:
    def __init__(self, port=WIND_VANE_PORT, device_address=1):
        """Initialize wind vane reader for USB RS485 adapter"""
        self.port = port
        self.device_address = device_address
        self.serial_conn = None
        
        # Threading support
        self.running = False
        self.lock = threading.Lock()
        
        # Latest wind data storage
        self.latest_wind = {
            'direction': 0.0,
            'direction_name': 'Unknown',
            'speed': 0.0,
            'timestamp': 0.0,
            'valid': False
        }
        
        # Valid wind angles for 8-position wind vane
        self.valid_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        
        # Connect and start thread
        self.connect()
    
    def connect(self):
        """Connect to wind vane and start background thread"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=WIND_VANE_BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )
            logger.info(f"Wind vane connected on {self.port}")
            
            # Start background reading thread
            if self.serial_conn:
                self.running = True
                threading.Thread(target=self._read_wind_loop, daemon=True).start()
                
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.serial_conn = None
    
    
    def _read_wind_loop(self):
        """Background thread for continuous wind reading"""
        while self.running and self.serial_conn:
            try:
                direction = self._read_wind_direction()
                direction_name = self._get_direction_name(direction) if direction is not None else 'Unknown'
                
                with self.lock:
                    self.latest_wind.update({
                        'direction': direction if direction is not None else 0.0,
                        'direction_name': direction_name,
                        'speed': 0.0,  # Wind vane only measures direction
                        'timestamp': time.time(),
                        'valid': direction is not None
                    })
                    
            except Exception as e:
                print(f"Wind reading error: {e}")
                with self.lock:
                    self.latest_wind['valid'] = False
            
            time.sleep(2.0)  # Read every 2 seconds
    
    def _get_direction_name(self, degrees):
        """Convert degrees to compass direction name"""
        if degrees is None:
            return 'Unknown'
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = int((degrees + 22.5) / 45) % 8
        return directions[index]
    
    def _read_wind_direction(self) -> Optional[float]:
        """Read wind direction from register 1 (degree orientation)"""
        if not self.serial_conn:
            return None
            
        try:
            # Modbus RTU: Read register 1 (holding register) - contains degree orientation
            request = bytes([self.device_address, 0x03, 0x00, 0x01, 0x00, 0x01])
            
            crc = self._calculate_crc16(request)
            request += crc.to_bytes(2, 'little')
            
            self.serial_conn.flushInput()
            self.serial_conn.write(request)
            
            response = self.serial_conn.read(7)  # Expected: addr + func + bytes + data + crc
            
            if len(response) >= 7:
                # Parse response: [addr][func][byte_count][data_h][data_l][crc_l][crc_h]
                angle = (response[3] << 8) | response[4]
                
                # Validate that angle is one of the 8 valid directions
                if angle in self.valid_angles:
                    return float(angle)
                else:
                    print(f"Invalid wind angle: {angle} (expected one of {self.valid_angles})")
                    return None
            else:
                return None
                
        except Exception as e:
            return None
    
    
    def _calculate_crc16(self, data):
        """Calculate Modbus CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    def read_wind(self) -> Dict[str, any]:
        """Get latest wind data (non-blocking)"""
        with self.lock:
            return self.latest_wind.copy()
    
    def get_status(self) -> Dict[str, any]:
        """Get wind vane connection status"""
        return {
            'connected': self.serial_conn is not None,
            'running': self.running,
            'port': self.port,
            'device_address': self.device_address
        }
    
    def close(self):
        """Close wind vane connection"""
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()
            logger.info("Wind vane connection closed")

# Test script
if __name__ == "__main__":
    try:
        print("=== Wind Vane Reader Test ===")
        wind_sensor = WindSensorReader('/dev/ttyUSB0')
        
        if wind_sensor.serial_conn:
            print("Wind vane connected. Reading for 30 seconds...")
            print("Direction will update every 2 seconds in background thread")
            print("-" * 50)
            
            start_time = time.time()
            while time.time() - start_time < 30:
                wind_data = wind_sensor.read_wind()
                status = "Valid" if wind_data['valid'] else "Invalid"
                
                print(f"Wind: {wind_data['direction']:3.0f}° ({wind_data['direction_name']}) - {status}")
                time.sleep(3)  # Display update interval
        else:
            print("Failed to connect to wind vane")
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        wind_sensor.close()
