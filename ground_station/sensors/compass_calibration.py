"""
Simple Compass Calibration Manager for HMC5883L
Handles calibration storage and retrieval with proximity tolerance
"""

import json
import time
import os
import glob
from typing import Dict, Optional, Tuple

# Proximity tolerance for finding nearby calibrations
PROXIMITY_TOLERANCE_DEGREES = 0.005  # ~500m at equator
CALIBRATION_DIR = '/home/pi/Desktop/gps_calibrations'

class CompassCalibrationManager:
    def __init__(self):
        self.calibration_dir = CALIBRATION_DIR
        os.makedirs(self.calibration_dir, exist_ok=True)
    
    def load_calibration(self, location_id: str = None, current_lat: float = None, current_lon: float = None) -> Dict:
        """Load calibration with proximity tolerance"""
        # Try exact location match first
        if location_id:
            cal_file = self._get_calibration_file(location_id)
            if os.path.exists(cal_file):
                return self._load_file(cal_file, f"exact match: {location_id}")
        
        # Try GPS proximity match
        if current_lat is not None and current_lon is not None:
            nearby_file = self._find_nearby_calibration(current_lat, current_lon)
            if nearby_file:
                return self._load_file(nearby_file, "nearby location")
        
        # Default values
        print("No calibration found - using defaults")
        return {
            'offset': {'x': 0, 'y': 0, 'z': 0},
            'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0},
            'declination': 0.0
        }
    
    def save_calibration(self, offset: Dict, scale: Dict, declination: float, 
                        location_id: str, lat: float = None, lon: float = None) -> bool:
        """Save calibration data"""
        cal_data = {
            'offset': offset,
            'scale': scale,
            'declination': declination,
            'location': {'id': location_id, 'lat': lat or 0.0, 'lon': lon or 0.0},
            'timestamp': time.time()
        }
        
        try:
            cal_file = self._get_calibration_file(location_id)
            with open(cal_file, 'w') as f:
                json.dump(cal_data, f, indent=2)
            print(f"Calibration saved: {location_id}")
            return True
        except Exception as e:
            print(f"Save failed: {e}")
            return False
    
    def _find_nearby_calibration(self, lat: float, lon: float) -> Optional[str]:
        """Find calibration within proximity tolerance"""
        cal_files = glob.glob(f"{self.calibration_dir}/compass_cal_*.json")
        
        for cal_file in cal_files:
            try:
                with open(cal_file, 'r') as f:
                    cal_data = json.load(f)
                    location = cal_data.get('location', {})
                    cal_lat = location.get('lat')
                    cal_lon = location.get('lon')
                    
                    if cal_lat is not None and cal_lon is not None:
                        # Check if within tolerance
                        lat_diff = abs(lat - cal_lat)
                        lon_diff = abs(lon - cal_lon)
                        
                        if lat_diff <= PROXIMITY_TOLERANCE_DEGREES and lon_diff <= PROXIMITY_TOLERANCE_DEGREES:
                            distance_m = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111000
                            print(f"Found nearby calibration ({distance_m:.0f}m away)")
                            return cal_file
            except:
                continue
        
        return None
    
    def _load_file(self, cal_file: str, source: str) -> Dict:
        """Load calibration from file"""
        try:
            with open(cal_file, 'r') as f:
                cal_data = json.load(f)
                print(f"Loaded calibration from {source}")
                return {
                    'offset': cal_data.get('offset', {'x': 0, 'y': 0, 'z': 0}),
                    'scale': cal_data.get('scale', {'x': 1.0, 'y': 1.0, 'z': 1.0}),
                    'declination': cal_data.get('declination', 0.0)
                }
        except Exception as e:
            print(f"Failed to load calibration: {e}")
            return {
                'offset': {'x': 0, 'y': 0, 'z': 0},
                'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0},
                'declination': 0.0
            }
    
    def list_calibrations(self) -> None:
        """List all calibrations"""
        cal_files = glob.glob(f"{self.calibration_dir}/compass_cal_*.json")
        
        if not cal_files:
            print("No calibrations found")
            return
        
        print("Available calibrations:")
        for cal_file in sorted(cal_files):
            try:
                with open(cal_file, 'r') as f:
                    cal_data = json.load(f)
                    location = cal_data.get('location', {})
                    timestamp = cal_data.get('timestamp', 0)
                    
                    print(f"  {location.get('id', 'Unknown')}")
                    if location.get('lat') and location.get('lon'):
                        print(f"    GPS: {location['lat']:.4f}, {location['lon']:.4f}")
                    print(f"    Date: {time.ctime(timestamp)}")
                    print()
            except:
                print(f"  {os.path.basename(cal_file)} - Error reading file")
    
    def _get_calibration_file(self, location_id: str) -> str:
        """Get calibration file path"""
        return os.path.join(self.calibration_dir, f"compass_cal_{location_id}.json")


class CompassCalibrator:
    """Handles compass calibration process"""
    
    def __init__(self, i2c_conn, compass_addr=0x1E):
        self.i2c_conn = i2c_conn
        self.compass_addr = compass_addr
    
    def calibrate(self, duration: int = 30) -> Tuple[Dict, Dict]:
        """Perform compass calibration"""
        print(f"Calibrating for {duration}s - rotate module in all directions")
        print("3... 2... 1... GO!")
        time.sleep(3)
        
        min_vals = [32767, 32767, 32767]
        max_vals = [-32768, -32768, -32768]
        start_time = time.time()
        samples = 0
        
        while time.time() - start_time < duration:
            try:
                # Read magnetometer data
                data = [self.i2c_conn.read_byte_data(self.compass_addr, 0x03 + i) for i in range(6)]
                
                # Convert to signed values (X, Y, Z)
                xyz = []
                for i in range(0, 6, 2):
                    val = (data[i] << 8) | data[i+1]
                    if val > 32767: val -= 65536
                    xyz.append(val)
                
                # Track min/max
                for i in range(3):
                    min_vals[i] = min(min_vals[i], xyz[i])
                    max_vals[i] = max(max_vals[i], xyz[i])
                
                samples += 1
                if samples % 50 == 0:
                    remaining = duration - (time.time() - start_time)
                    print(f"Calibrating... {remaining:.1f}s remaining")
                    
            except:
                pass
            time.sleep(0.1)
        
        # Calculate calibration
        offset = {}
        scale = {}
        for i, axis in enumerate(['x', 'y', 'z']):
            offset[axis] = (max_vals[i] + min_vals[i]) / 2
            range_val = max_vals[i] - min_vals[i]
            if range_val > 0:
                avg_range = sum(max_vals[j] - min_vals[j] for j in range(3)) / 3
                scale[axis] = avg_range / range_val
            else:
                scale[axis] = 1.0
        
        print(f"Calibration complete! {samples} samples")
        return offset, scale
