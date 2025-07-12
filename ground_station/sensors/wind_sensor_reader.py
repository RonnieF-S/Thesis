"""
Wind Sensor Reader
Interface for wind speed and direction sensor
Currently configured for placeholder - update with actual sensor interface
"""

import time
import math
from typing import Dict

class WindSensorReader:
    def __init__(self):
        """Initialize wind sensor reader"""
        # TODO: Initialize actual wind sensor hardware connection
        # This could be I2C, UART, or analog inputs depending on sensor type
        
        print("Wind sensor reader initialized (hardware interface needed)")
    
    def read_wind(self) -> Dict[str, float]:
        """
        Read current wind conditions
        
        Returns:
            Dictionary with direction (degrees) and speed (m/s)
        """
        return self._read_real_sensor()
    
    def _read_real_sensor(self) -> Dict[str, float]:
        """Read from actual wind sensor hardware"""
        # TODO: Implement actual sensor reading
        # Examples of wind sensor interfaces:
        # - Ultrasonic: I2C or UART communication
        # - Cup anemometer: Pulse counting for speed
        # - Wind vane: Analog voltage or resistance measurement
        
        try:
            # Placeholder values - replace with actual sensor readings
            # For now, return static values to allow system testing
            direction = 270.0  # Degrees (0=North, 90=East, 180=South, 270=West)
            speed = 3.5        # m/s
            
            return {
                'direction': direction,
                'speed': speed,
                'timestamp': time.time()
            }
        except Exception as e:
            print(f"Error reading wind sensor: {e}")
            # Return safe default values on error
            return {
                'direction': 0.0,
                'speed': 0.0,
                'timestamp': time.time()
            }
    
    def calibrate(self):
        """Calibrate wind sensor"""
        try:
            # TODO: Implement calibration procedure for actual hardware
            print("Starting wind sensor calibration...")
            time.sleep(2)  # Simulate calibration time
            print("Wind sensor calibration complete")
            return True
        except Exception as e:
            print(f"Wind sensor calibration failed: {e}")
            return False
    
    def get_wind_average(self, duration_seconds=30) -> Dict[str, float]:
        """Get averaged wind reading over specified duration"""
        readings = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            reading = self.read_wind()
            readings.append(reading)
            time.sleep(1)  # 1-second intervals
        
        if not readings:
            return {'direction': 0.0, 'speed': 0.0, 'timestamp': time.time()}
        
        # Calculate average direction (accounting for circular nature)
        # Convert to vectors, average, then back to angle
        x_sum = sum(math.cos(math.radians(r['direction'])) for r in readings)
        y_sum = sum(math.sin(math.radians(r['direction'])) for r in readings)
        avg_direction = math.degrees(math.atan2(y_sum, x_sum)) % 360
        
        # Calculate average speed
        avg_speed = sum(r['speed'] for r in readings) / len(readings)
        
        return {
            'direction': avg_direction,
            'speed': avg_speed,
            'timestamp': time.time(),
            'sample_count': len(readings)
        }
    
    def close(self):
        """Close wind sensor connection"""
        # TODO: Close actual sensor connection when hardware is connected
        print("Wind sensor reader closed")

# Test code
if __name__ == "__main__":
    try:
        wind_sensor = WindSensorReader()
        
        print("Reading wind for 10 seconds...")
        for i in range(10):
            wind_data = wind_sensor.read_wind()
            print(f"Wind: {wind_data['direction']:.1f}° @ {wind_data['speed']:.1f} m/s")
            time.sleep(1)
        
        print("\nGetting 5-second average...")
        avg_data = wind_sensor.get_wind_average(5)
        print(f"Average wind: {avg_data['direction']:.1f}° @ {avg_data['speed']:.1f} m/s")
        
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        wind_sensor.close()
