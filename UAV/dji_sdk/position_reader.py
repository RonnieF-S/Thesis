"""
DJI SDK Position Reader
Interfaces with DJI M350 RTK to get GPS position
"""

import time
from typing import Dict, Optional

class PositionReader:
    def __init__(self):
        """Initialize GPS position reader for DJI M350 RTK"""
        self.last_position = {
            'lat': -31.9502,  # Default Perth coordinates
            'lon': 115.8563,
            'alt': 50.0,
            'timestamp': time.time()
        }
        
        # TODO: Initialize actual DJI SDK connection
        print("DJI Position Reader initialized - ready for SDK integration")
    
    def get_position(self) -> Dict[str, float]:
        """
        Get current GPS position from DJI M350 RTK
        
        Returns:
            Dictionary with lat, lon, alt, timestamp
        """
        try:
            # TODO: Replace with actual DJI SDK call
            # For now, simulate slight movement for testing
            current_time = time.time()
            
            # Simulate small GPS drift for testing
            drift_lat = 0.0001 * (current_time % 10 - 5) / 5  # ±0.0001 degrees
            drift_lon = 0.0001 * ((current_time * 1.3) % 10 - 5) / 5
            
            position = {
                'lat': self.last_position['lat'] + drift_lat,
                'lon': self.last_position['lon'] + drift_lon,
                'alt': self.last_position['alt'] + 2.0 * (time.time() % 20 - 10) / 10,  # ±2m altitude variation
                'timestamp': current_time
            }
            
            self.last_position = position.copy()
            return position
            
        except Exception as e:
            print(f"Error reading GPS position: {e}")
            # Return last known position on error
            return self.last_position.copy()
    
    def get_altitude(self) -> float:
        """Get current altitude only"""
        position = self.get_position()
        return position['alt']
    
    def get_coordinates(self) -> tuple:
        """Get current lat/lon as tuple"""
        position = self.get_position()
        return (position['lat'], position['lon'])
    
    def is_position_valid(self) -> bool:
        """Check if current position is valid"""
        try:
            position = self.get_position()
            
            # Basic validity checks
            if not (-90 <= position['lat'] <= 90):
                return False
            if not (-180 <= position['lon'] <= 180):
                return False
            if position['alt'] < -100 or position['alt'] > 1000:  # Reasonable altitude range
                return False
            
            return True
            
        except Exception:
            return False
    
    def wait_for_valid_position(self, timeout=30.0) -> Optional[Dict[str, float]]:
        """
        Wait for a valid GPS position
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Valid position dict or None on timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_position_valid():
                return self.get_position()
            
            time.sleep(0.5)
        
        print("Timeout waiting for valid GPS position")
        return None
    
    def close(self):
        """Close GPS connection"""
        # TODO: Cleanup DJI SDK resources
        print("GPS position reader closed")

# Test code
if __name__ == "__main__":
    try:
        gps = PositionReader()
        
        print("Reading GPS position for 10 seconds...")
        for i in range(20):
            position = gps.get_position()
            print(f"GPS: {position['lat']:.6f}, {position['lon']:.6f}, {position['alt']:.1f}m")
            time.sleep(0.5)
        
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        gps.close()
