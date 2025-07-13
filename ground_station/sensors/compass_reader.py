"""
HMC5883L Compass Reader for Ground Station
Compass heading via I2C (separate from GPS)
"""

import time
import threading
import math
from typing import Dict, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import COMPASS_I2C_BUS, COMPASS_I2C_ADDRESS, SENSOR_READ_INTERVAL
from shared import SimpleLogger as logger
from .compass_calibration import CompassCalibrationManager

try:
    import smbus
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    logger.warning("smbus not available, compass functionality disabled")

class CompassReader:
    def __init__(self, i2c_bus=COMPASS_I2C_BUS, compass_addr=COMPASS_I2C_ADDRESS):
        """Initialize compass reader"""
        self.i2c_bus = i2c_bus
        self.compass_addr = compass_addr
        self.i2c_conn = None
        self.running = False
        
        # Data storage
        self.latest_compass = {
            'heading': 0.0,
            'valid': False,
            'timestamp': 0.0
        }
        
        # Calibration values (defaults - load externally)
        self.mag_offset = {'x': 0, 'y': 0, 'z': 0}
        self.mag_scale = {'x': 1.0, 'y': 1.0, 'z': 1.0}
        self.declination = 0.0
        
        self.lock = threading.Lock()
        self.cal_manager = CompassCalibrationManager()
        
        if I2C_AVAILABLE:
            self.connect()
    
    def connect(self):
        """Connect to compass via I2C"""
        try:
            self.i2c_conn = smbus.SMBus(self.i2c_bus)
            self._init_compass()
            logger.info(f"Compass connected on I2C bus {self.i2c_bus}")
            
            # Start background reading thread
            if self.i2c_conn:
                self.running = True
                threading.Thread(target=self._read_compass, daemon=True).start()
                
        except Exception as e:
            logger.error(f"Compass connection failed: {e}")
            self.i2c_conn = None
    
    def _init_compass(self):
        """Initialize HMC5883L compass"""
        self.i2c_conn.write_byte_data(self.compass_addr, 0x00, 0x70)  # Config A
        self.i2c_conn.write_byte_data(self.compass_addr, 0x01, 0x20)  # Config B
        self.i2c_conn.write_byte_data(self.compass_addr, 0x02, 0x00)  # Mode
        time.sleep(0.1)
        print("Compass initialized")
    
    def _read_compass(self):
        """Read compass data continuously"""
        while self.running and self.i2c_conn:
            try:
                heading = self._get_compass_heading()
                with self.lock:
                    self.latest_compass.update({
                        'heading': heading if heading is not None else 0.0,
                        'valid': heading is not None,
                        'timestamp': time.time()
                    })
            except Exception as e:
                with self.lock:
                    self.latest_compass['valid'] = False
            time.sleep(0.2)  # Read every 200ms
    
    def _get_compass_heading(self) -> Optional[float]:
        """Get calibrated compass heading"""
        try:
            # Read raw magnetometer data
            data = [self.i2c_conn.read_byte_data(self.compass_addr, 0x03 + i) for i in range(6)]
            
            # Convert to signed 16-bit values (X, Z, Y order for HMC5883L)
            x = (data[0] << 8) | data[1]
            if x > 32767: x -= 65536
            y = (data[4] << 8) | data[5]  # Y is at offset 4,5
            if y > 32767: y -= 65536
            
            # Apply calibration
            x_cal = (x - self.mag_offset['x']) * self.mag_scale['x']
            y_cal = (y - self.mag_offset['y']) * self.mag_scale['y']
            
            # Calculate heading
            heading = math.atan2(y_cal, x_cal) * 180.0 / math.pi + self.declination
            
            # Normalize to 0-360
            return heading % 360
        except:
            return None
    
    def load_calibration(self, location_id: str = None, lat: float = None, lon: float = None) -> bool:
        """Load compass calibration"""
        try:
            calibration = self.cal_manager.load_calibration(location_id, lat, lon)
            
            self.mag_offset = calibration['offset']
            self.mag_scale = calibration['scale'] 
            self.declination = calibration['declination']
            
            print("Compass calibration loaded")
            return True
        except Exception as e:
            print(f"Failed to load calibration: {e}")
            return False
    
    def get_compass(self) -> Dict:
        """Get current compass heading"""
        with self.lock:
            return self.latest_compass.copy()
    
    def get_raw_magnetometer(self) -> Optional[Dict]:
        """Get raw magnetometer readings for calibration"""
        if not self.i2c_conn:
            return None
            
        try:
            data = [self.i2c_conn.read_byte_data(self.compass_addr, 0x03 + i) for i in range(6)]
            
            # Convert to signed values
            x = (data[0] << 8) | data[1]
            if x > 32767: x -= 65536
            y = (data[4] << 8) | data[5]
            if y > 32767: y -= 65536
            z = (data[2] << 8) | data[3]
            if z > 32767: z -= 65536
            
            return {'x': x, 'y': y, 'z': z}
        except:
            return None
    
    def get_status(self) -> Dict:
        """Get compass status"""
        compass_data = self.get_compass()
        return {
            'connected': self.i2c_conn is not None,
            'running': self.running,
            'valid': compass_data['valid'],
            'i2c_bus': self.i2c_bus,
            'address': f"0x{self.compass_addr:02x}",
            'calibrated': any(self.mag_offset.values()) or any(v != 1.0 for v in self.mag_scale.values())
        }
    
    def close(self):
        """Close compass connection"""
        self.running = False
        if self.i2c_conn:
            self.i2c_conn.close()
        logger.info("Compass reader closed")

# Test script
if __name__ == "__main__":
    try:
        print("=== Compass Reader Test ===")
        compass = CompassReader()
        
        if compass.i2c_conn:
            print("Compass connected. Reading for 30 seconds...")
            print("-" * 40)
            
            start_time = time.time()
            while time.time() - start_time < 30:
                compass_data = compass.get_compass()
                status = "Valid" if compass_data['valid'] else "Invalid"
                
                print(f"Heading: {compass_data['heading']:6.1f}° - {status}")
                time.sleep(2)
        else:
            print("Failed to connect to compass")
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        compass.close()
