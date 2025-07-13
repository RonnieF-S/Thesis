#!/usr/bin/env python3
"""
List Compass Calibrations
Simple script to list all available compass calibrations
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from sensors.compass_calibration import CompassCalibrationManager

def main():
    """List all compass calibrations"""
    print("Compass Calibrations")
    print("=" * 40)
    
    cal_manager = CompassCalibrationManager()
    cal_manager.list_calibrations()
    
    print("=" * 40)
    print("To calibrate compass: python3 calibrate_compass.py [location_name]")

if __name__ == "__main__":
    main()
