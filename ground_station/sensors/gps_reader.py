"""
BN-880 GPS Module Reader for Ground Station
GPS positioning via UART (Serial connection only)
"""

import serial
import time
import threading
from typing import Dict
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import GPS_PORT, GPS_BAUDRATE, GPS_TIMEOUT, SENSOR_READ_INTERVAL
from shared import SimpleLogger as logger

class GPSReader:
    def __init__(self, port=GPS_PORT, baudrate=GPS_BAUDRATE):
        """Initialize GPS reader"""
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        
        # Data storage
        self.latest_position = {
            'lat': 0.0, 'lon': 0.0, 'alt': 0.0, 'satellites': 0, 'hdop': 0.0,
            'valid': False, 'timestamp': 0.0, 'utc_time': None
        }
        
        self.lock = threading.Lock()
        self.connect()
    
    def connect(self):
        """Connect to GPS via serial"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            logger.info(f"GPS connected on {self.port}")
            
            # Start background reading thread
            if self.serial_conn:
                self.running = True
                threading.Thread(target=self._read_gps, daemon=True).start()
                
        except Exception as e:
            logger.error(f"GPS connection failed: {e}")
            self.serial_conn = None
    
    
    def _read_gps(self):
        """Read GPS data continuously"""
        while self.running and self.serial_conn:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
                    if line.startswith(('$GPGGA', '$GNGGA')):
                        self._parse_gga(line)
            except:
                pass
            time.sleep(SENSOR_READ_INTERVAL)
    
    def _parse_gga(self, sentence):
        """Parse GGA sentence for position and time"""
        try:
            parts = sentence.split(',')
            if len(parts) < 15:
                return
            
            # Extract time
            time_str = parts[1]
            utc_time = None
            if time_str:
                h, m, s = int(time_str[:2]), int(time_str[2:4]), float(time_str[4:])
                utc_time = f"{h:02d}:{m:02d}:{s:05.2f}"
            
            # Extract position data
            lat_str, lat_dir = parts[2], parts[3]
            lon_str, lon_dir = parts[4], parts[5]
            fix_quality = int(parts[6]) if parts[6] else 0
            satellites = int(parts[7]) if parts[7] else 0
            hdop = float(parts[8]) if parts[8] else 0.0
            altitude = float(parts[9]) if parts[9] else 0.0
            
            with self.lock:
                if lat_str and lon_str and fix_quality > 0:
                    # Valid fix - update position
                    lat = self._convert_to_decimal(lat_str, lat_dir)
                    lon = self._convert_to_decimal(lon_str, lon_dir)
                    self.latest_position.update({
                        'lat': lat, 'lon': lon, 'alt': altitude, 'hdop': hdop,
                        'satellites': satellites, 'valid': True,
                        'utc_time': utc_time, 'timestamp': time.time()
                    })
                else:
                    # Invalid fix - keep position, update status
                    self.latest_position.update({
                        'satellites': satellites, 'valid': False,
                        'utc_time': utc_time, 'timestamp': time.time()
                    })
        except:
            with self.lock:
                self.latest_position.update({'valid': False, 'timestamp': time.time()})
    
    def _convert_to_decimal(self, coord_str, direction):
        """Convert NMEA coordinate to decimal degrees"""
        try:
            dot_pos = coord_str.index('.')
            if dot_pos >= 4:  # Longitude
                degrees, minutes = float(coord_str[:3]), float(coord_str[3:])
            else:  # Latitude
                degrees, minutes = float(coord_str[:2]), float(coord_str[2:])
            
            decimal = degrees + minutes / 60.0
            return -decimal if direction in ['S', 'W'] else decimal
        except:
            return 0.0
    
    
    def get_position(self) -> Dict:
        """Get current GPS position"""
        with self.lock:
            return self.latest_position.copy()
    
    def get_gps_time(self) -> Dict:
        """Get GPS UTC time"""
        pos = self.get_position()
        return {
            'utc_time': pos.get('utc_time'),
            'valid': pos.get('utc_time') is not None,
            'timestamp': pos.get('timestamp', time.time())
        }
    
    def wait_for_fix(self, timeout=GPS_TIMEOUT) -> bool:
        """Wait for GPS fix"""
        start = time.time()
        while time.time() - start < timeout:
            if self.get_position()['valid']:
                return True
            time.sleep(1)
        return False
    
    def get_status(self) -> Dict:
        """Get GPS status"""
        pos = self.get_position()
        return {
            'connected': self.serial_conn is not None,
            'running': self.running,
            'fix_valid': pos['valid'],
            'satellites': pos['satellites'],
            'hdop': pos.get('hdop', 0.0),
            'port': self.port
        }
    
    def close(self):
        """Close GPS connection"""
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()
        logger.info("GPS reader closed")

# Test script
if __name__ == "__main__":
    try:
        print("=== GPS Reader Test ===")
        gps = GPSReader()
        
        if gps.serial_conn:
            print("Connected! Reading GPS data...")
            
            while True:
                pos_data = gps.get_position()
                
                if pos_data['valid']:
                    lat = pos_data['lat']
                    lon = pos_data['lon']
                    sats = pos_data['satellites']
                    print(f"GPS: {lat:.6f}, {lon:.6f} ({sats} sats)")
                else:
                    print(f"No fix ({pos_data['satellites']} sats)")
                
                time.sleep(2)
        else:
            print("Failed to connect to GPS")
        
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        gps.close()
