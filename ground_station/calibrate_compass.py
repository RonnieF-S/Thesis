#!/usr/bin/env python3
"""
Standalone Compass Calibration Script
Simple script to calibrate HMC5883L compass on BN-880 GPS module
"""

import sys
import os
import time

# Add ground_station directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import smbus
except ImportError:
    print("Error: smbus not available. Install with: sudo apt install python3-smbus")
    sys.exit(1)

from sensors.compass_calibration import CompassCalibrationManager, CompassCalibrator

def main():
    """Simple compass calibration"""
    if len(sys.argv) > 1:
        location_id = sys.argv[1]
    else:
        location_id = input("Enter location name (or press Enter for auto): ").strip()
        if not location_id:
            location_id = None
    
    print("Compass Calibration")
    print("=" * 40)
    
    # Connect to I2C
    try:
        i2c_conn = smbus.SMBus(1)  # I2C bus 1
        print("Connected to I2C bus")
    except Exception as e:
        print(f"I2C connection failed: {e}")
        return
    
    # Initialize compass
    try:
        COMPASS_ADDR = 0x1E
        i2c_conn.write_byte_data(COMPASS_ADDR, 0x00, 0x70)  # Config A
        i2c_conn.write_byte_data(COMPASS_ADDR, 0x01, 0x20)  # Config B  
        i2c_conn.write_byte_data(COMPASS_ADDR, 0x02, 0x00)  # Mode
        time.sleep(0.1)
        print("Compass initialized")
    except Exception as e:
        print(f"Compass initialization failed: {e}")
        return
    
    # Create calibration objects
    cal_manager = CompassCalibrationManager()
    calibrator = CompassCalibrator(i2c_conn, COMPASS_ADDR)
    
    # Perform calibration
    print("\nStarting calibration...")
    offset, scale = calibrator.calibrate(30)
    
    # Save calibration
    declination = 0.0  # Default, can be set later
    success = cal_manager.save_calibration(
        offset, scale, declination,
        location_id or f"auto_{int(time.time())}"
    )
    
    if success:
        print("\nCalibration completed and saved!")
        if location_id:
            print(f"Location: {location_id}")
        print("Use 'python3 list_calibrations.py' to view all calibrations")
    else:
        print("\nCalibration failed to save")
    
    # Close connection
    i2c_conn.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCalibration cancelled")
    except Exception as e:
        print(f"\nError: {e}")
