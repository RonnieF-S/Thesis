#!/usr/bin/env python3
"""
Test script for GPS reader
Use this to verify GPS antenna is working correctly
"""

import sys
import os
import time

# Add ground_station directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ground_station'))

from sensors.gps_reader import GPSReader

class GPSTest:
    def __init__(self, port='/dev/ttyUSB0'):
        self.gps = GPSReader(port=port)
        
    def continuous_reading(self, duration=60):
        """Read GPS continuously for specified duration"""
        print(f"Reading GPS for {duration} seconds...")
        print("Waiting for GPS fix...")
        
        fix_acquired = self.gps.wait_for_fix(30)
        if fix_acquired:
            print("✓ GPS fix acquired!")
        else:
            print("⚠ GPS fix timeout - showing available data")
        
        start_time = time.time()
        readings = []
        
        while time.time() - start_time < duration:
            position = self.gps.get_position()
            status = self.gps.get_status()
            
            if position['valid']:
                readings.append(position)
                print(f"GPS: {position['lat']:.6f}, {position['lon']:.6f}, {position['alt']:.1f}m")
                print(f"     Sats: {position['satellites']}, HDOP: {position['hdop']:.1f}, Speed: {position['speed']:.1f} m/s")
            else:
                print(f"GPS: No fix - Sats: {position['satellites']}, HDOP: {position['hdop']:.1f}")
            
            time.sleep(1)
        
        if readings:
            self._print_summary(readings)
    
    def _print_summary(self, readings):
        """Print GPS summary statistics"""
        lats = [r['lat'] for r in readings]
        lons = [r['lon'] for r in readings]
        alts = [r['alt'] for r in readings]
        
        print(f"\nGPS Summary:")
        print(f"  Valid readings: {len(readings)}")
        print(f"  Latitude range: {min(lats):.6f} to {max(lats):.6f}")
        print(f"  Longitude range: {min(lons):.6f} to {max(lons):.6f}")
        print(f"  Altitude range: {min(alts):.1f}m to {max(alts):.1f}m")
        
        # Calculate approximate position accuracy
        lat_spread = (max(lats) - min(lats)) * 111000  # meters
        lon_spread = (max(lons) - min(lons)) * 111000 * abs(sum(lats)/len(lats))/90  # rough correction
        print(f"  Position spread: ±{max(lat_spread, lon_spread):.1f}m")
    
    def status_check(self):
        """Check GPS status and capabilities"""
        print("GPS Status Check")
        print("=" * 40)
        
        status = self.gps.get_status()
        position = self.gps.get_position()
        
        print(f"Connection: {'✓ Connected' if status['connected'] else '✗ Disconnected'}")
        print(f"Fix Status: {'✓ Valid' if status['fix_valid'] else '✗ Invalid'}")
        print(f"Fix Quality: {position['fix_quality']} (0=none, 1=GPS, 2=DGPS)")
        print(f"Satellites: {status['satellites']}")
        print(f"HDOP: {status['hdop']:.1f} ({'Good' if status['hdop'] < 2 else 'Fair' if status['hdop'] < 5 else 'Poor'})")
        print(f"Data Age: {status['age_seconds']:.1f} seconds")
        
        if position['valid']:
            print(f"\nCurrent Position:")
            print(f"  Latitude: {position['lat']:.6f}°")
            print(f"  Longitude: {position['lon']:.6f}°")
            print(f"  Altitude: {position['alt']:.1f}m")
            print(f"  Speed: {position['speed']:.1f} m/s")
            print(f"  Course: {position['course']:.1f}°")
    
    def wait_for_fix_test(self, timeout=60):
        """Test GPS fix acquisition"""
        print(f"Testing GPS fix acquisition (timeout: {timeout}s)")
        
        start_time = time.time()
        fix_acquired = self.gps.wait_for_fix(timeout)
        elapsed = time.time() - start_time
        
        if fix_acquired:
            print(f"✓ GPS fix acquired in {elapsed:.1f} seconds")
            position = self.gps.get_position()
            print(f"  Position: {position['lat']:.6f}, {position['lon']:.6f}")
            print(f"  Satellites: {position['satellites']}")
        else:
            print(f"✗ GPS fix timeout after {elapsed:.1f} seconds")
            status = self.gps.get_status()
            print(f"  Satellites visible: {status['satellites']}")
    
    def nmea_raw_output(self, duration=10):
        """Show raw NMEA sentences (requires direct serial access)"""
        print(f"Showing raw NMEA output for {duration} seconds...")
        print("Note: This shows parsed data, not raw NMEA sentences")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            position = self.gps.get_position()
            if position['timestamp'] > 0:
                print(f"Parsed: LAT={position['lat']:.6f} LON={position['lon']:.6f} "
                      f"ALT={position['alt']:.1f} SAT={position['satellites']} "
                      f"HDOP={position['hdop']:.1f}")
            time.sleep(1)
    
    def close(self):
        """Close GPS connection"""
        self.gps.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_gps.py <mode> [port]")
        print("Modes:")
        print("  read      - Continuous readings for 60 seconds")
        print("  status    - Check GPS status and current position")
        print("  fix       - Test GPS fix acquisition")
        print("  raw       - Show parsed GPS data stream")
        print("Default port: /dev/ttyUSB0")
        return
    
    mode = sys.argv[1]
    port = sys.argv[2] if len(sys.argv) > 2 else '/dev/ttyUSB0'
    
    tester = GPSTest(port)
    
    try:
        if mode == 'read':
            tester.continuous_reading(60)
        elif mode == 'status':
            tester.status_check()
        elif mode == 'fix':
            tester.wait_for_fix_test(60)
        elif mode == 'raw':
            tester.nmea_raw_output(10)
        else:
            print(f"Unknown mode: {mode}")
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        tester.close()

if __name__ == "__main__":
    main()
