#!/usr/bin/env python3
"""
Test script for Wind sensor
Use this to verify wind sensor is working correctly
"""

import sys
import os
import time

# Add ground_station directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ground_station'))

from sensors.wind_sensor_reader import WindSensorReader

class WindSensorTest:
    def __init__(self):
        self.wind_sensor = WindSensorReader()
        
    def continuous_reading(self, duration=30):
        """Read wind continuously for specified duration"""
        print(f"Reading wind for {duration} seconds...")
        start_time = time.time()
        readings = []
        
        while time.time() - start_time < duration:
            wind_data = self.wind_sensor.read_wind()
            
            if wind_data:
                readings.append(wind_data)
                direction = wind_data['direction']
                speed = wind_data['speed']
                print(f"Wind: {direction:.1f}° @ {speed:.1f} m/s")
            else:
                print("Failed to read wind sensor")
            
            time.sleep(1)  # 1-second intervals
        
        if readings:
            self._print_summary(readings)
    
    def _print_summary(self, readings):
        """Print summary statistics"""
        speeds = [r['speed'] for r in readings]
        directions = [r['direction'] for r in readings]
        
        avg_speed = sum(speeds) / len(speeds)
        min_speed = min(speeds)
        max_speed = max(speeds)
        
        print(f"\nSummary:")
        print(f"  Readings: {len(readings)}")
        print(f"  Speed - Avg: {avg_speed:.1f} m/s, Range: {min_speed:.1f} - {max_speed:.1f} m/s")
        print(f"  Direction - Range: {min(directions):.1f}° - {max(directions):.1f}°")
    
    def averaged_reading(self, duration=10):
        """Get averaged wind reading"""
        print(f"Getting {duration}-second averaged reading...")
        avg_data = self.wind_sensor.get_wind_average(duration)
        
        print(f"Average wind: {avg_data['direction']:.1f}° @ {avg_data['speed']:.1f} m/s")
        print(f"Based on {avg_data.get('sample_count', 'unknown')} samples")
    
    def calibrate_sensor(self):
        """Calibrate the wind sensor"""
        print("Calibrating wind sensor...")
        success = self.wind_sensor.calibrate()
        
        if success:
            print("Calibration completed successfully")
        else:
            print("Calibration failed")
    
    def sensor_info(self):
        """Display sensor information"""
        print("Wind Sensor Information:")
        print("  Status: Ready for hardware integration")
        print("  Interface: TODO - Implement actual sensor interface")
        print("  Current mode: Placeholder values")
        print("  Notes: Update wind_sensor_reader.py with actual hardware interface")
    
    def close(self):
        """Close sensor connection"""
        self.wind_sensor.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_wind.py <mode>")
        print("Modes:")
        print("  read      - Continuous readings for 30 seconds")
        print("  average   - 10-second averaged reading")
        print("  calibrate - Calibrate sensor")
        print("  info      - Show sensor information")
        return
    
    mode = sys.argv[1]
    
    tester = WindSensorTest()
    
    try:
        if mode == 'read':
            tester.continuous_reading(30)
        elif mode == 'average':
            tester.averaged_reading(10)
        elif mode == 'calibrate':
            tester.calibrate_sensor()
        elif mode == 'info':
            tester.sensor_info()
        else:
            print(f"Unknown mode: {mode}")
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        tester.close()

if __name__ == "__main__":
    main()
