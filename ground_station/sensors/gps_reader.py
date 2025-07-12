"""
BN-880 GPS Module Reader for Ground Station
Basic GPS positioning only (no compass)
NMEA protocol interface
"""

import serial
import time
import threading
from typing import Dict

class GPSReader:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        """Initialize BN-880 GPS reader"""
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        
        # Latest GPS data
        self.latest_position = {
            'lat': 0.0,
            'lon': 0.0,
            'alt': 0.0,
            'satellites': 0,
            'valid': False,
            'timestamp': 0.0
        }
        
        self.lock = threading.Lock()
        self.connect()
    
    def connect(self):
        """Connect to BN-880 GPS module"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            
            # Start reading thread
            self.running = True
            self.read_thread = threading.Thread(target=self._read_gps)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            print(f"BN-880 GPS module connected on {self.port}")
            
        except Exception as e:
            print(f"BN-880 GPS connection failed: {e}")
    
    def _read_gps(self):
        """Read GPS data continuously from BN-880"""
        while self.running and self.serial_conn:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
                    if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                        self._parse_gga(line)
                        
            except Exception:
                pass
            
            time.sleep(0.1)
    
    def _parse_gga(self, sentence):
        """Parse GGA sentence for position data (BN-880 GPS only)"""
        try:
            parts = sentence.split(',')
            if len(parts) < 15:
                return
            
            with self.lock:
                # Latitude
                if parts[2] and parts[3]:
                    lat = self._convert_coordinate(parts[2], parts[3])
                    self.latest_position['lat'] = lat
                
                # Longitude
                if parts[4] and parts[5]:
                    lon = self._convert_coordinate(parts[4], parts[5])
                    self.latest_position['lon'] = lon
                
                # Altitude
                if parts[9]:
                    self.latest_position['alt'] = float(parts[9])
                
                # Satellites
                if parts[7]:
                    self.latest_position['satellites'] = int(parts[7])
                
                # Fix quality
                fix_quality = int(parts[6]) if parts[6] else 0
                self.latest_position['valid'] = fix_quality > 0 and self.latest_position['satellites'] >= 4
                self.latest_position['timestamp'] = time.time()
                
        except (ValueError, IndexError):
            pass
    
    def _convert_coordinate(self, coord_str, direction):
        """Convert NMEA coordinate to decimal degrees"""
        if not coord_str or not direction:
            return 0.0
        
        try:
            if '.' in coord_str:
                dot_pos = coord_str.index('.')
                if dot_pos >= 4:  # Longitude
                    degrees = float(coord_str[:3])
                    minutes = float(coord_str[3:])
                else:  # Latitude
                    degrees = float(coord_str[:2])
                    minutes = float(coord_str[2:])
                
                decimal = degrees + minutes / 60.0
                
                if direction in ['S', 'W']:
                    decimal = -decimal
                
                return decimal
        except:
            pass
        
        return 0.0
    
    def get_position(self) -> Dict[str, float]:
        """Get current GPS position"""
        with self.lock:
            return self.latest_position.copy()
    
    def wait_for_fix(self, timeout=60) -> bool:
        """Wait for GPS fix"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            position = self.get_position()
            if position['valid']:
                return True
            time.sleep(1)
        
        return False
    
    def get_status(self) -> Dict:
        """Get BN-880 GPS status"""
        position = self.get_position()
        return {
            'connected': self.serial_conn is not None,
            'fix_valid': position['valid'],
            'satellites': position['satellites']
        }
    
    def close(self):
        """Close GPS connection"""
        self.running = False
        
        if hasattr(self, 'read_thread') and self.read_thread.is_alive():
            self.read_thread.join(timeout=1)
        
        if self.serial_conn:
            self.serial_conn.close()
            
        print("GPS reader closed")
