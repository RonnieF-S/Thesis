#!/usr/bin/env python3
"""
Test script for SprintIR CO2 sensor
Use this to verify CO2 sensor is working correctly
"""

import serial
import time
import sys

class CO2SensorTest:
    def __init__(self, port='/dev/ttyAMA1', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        
    def connect(self):
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=2
            )
            print(f"Connected to CO2 sensor on {self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def read_co2(self):
        if not self.serial_conn:
            return None
        
        try:
            # Send command to request CO2 reading
            self.serial_conn.write(b'Z\r\n')
            
            # Read response
            response = self.serial_conn.readline().decode().strip()
            
            if response.startswith('z'):
                # Parse CO2 value from response (format: "z 00412")
                co2_str = response[2:].strip()
                return float(co2_str)
            else:
                print(f"Unexpected response: {response}")
                return None
                
        except Exception as e:
            print(f"Read error: {e}")
            return None
    
    def continuous_reading(self, duration=30):
        print(f"Reading CO2 for {duration} seconds...")
        start_time = time.time()
        readings = []
        
        while time.time() - start_time < duration:
            co2_value = self.read_co2()
            
            if co2_value is not None:
                readings.append(co2_value)
                print(f"CO2: {co2_value:.1f} ppm")
            else:
                print("Failed to read CO2")
            
            time.sleep(1)  # 1-second intervals
        
        if readings:
            avg_co2 = sum(readings) / len(readings)
            min_co2 = min(readings)
            max_co2 = max(readings)
            
            print(f"\nSummary:")
            print(f"  Readings: {len(readings)}")
            print(f"  Average: {avg_co2:.1f} ppm")
            print(f"  Range: {min_co2:.1f} - {max_co2:.1f} ppm")
    
    def calibrate_zero(self):
        """Perform zero calibration in clean air"""
        print("Starting zero calibration...")
        print("Make sure sensor is in clean air!")
        
        for i in range(5, 0, -1):
            print(f"Calibrating in {i}...")
            time.sleep(1)
        
        try:
            self.serial_conn.write(b'G\r\n')
            response = self.serial_conn.readline().decode().strip()
            print(f"Calibration response: {response}")
            return True
        except Exception as e:
            print(f"Calibration failed: {e}")
            return False
    
    def sensor_info(self):
        """Get sensor information"""
        print("Requesting sensor information...")
        
        # Try different info commands
        commands = [
            (b'Y\r\n', "Firmware version"),
            (b'S\r\n', "Serial number"),
            (b'?\r\n', "Help")
        ]
        
        for cmd, desc in commands:
            try:
                self.serial_conn.write(cmd)
                response = self.serial_conn.readline().decode().strip()
                print(f"{desc}: {response}")
            except Exception as e:
                print(f"Error getting {desc}: {e}")
            
            time.sleep(0.5)
    
    def close(self):
        if self.serial_conn:
            self.serial_conn.close()
            print("Connection closed")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_co2.py <mode> [port]")
        print("Modes: read, calibrate, info")
        print("Default port: /dev/ttyAMA1")
        return
    
    mode = sys.argv[1]
    port = sys.argv[2] if len(sys.argv) > 2 else '/dev/ttyAMA1'
    
    tester = CO2SensorTest(port)
    
    if not tester.connect():
        return
    
    try:
        if mode == 'read':
            tester.continuous_reading(30)
        elif mode == 'calibrate':
            tester.calibrate_zero()
        elif mode == 'info':
            tester.sensor_info()
        else:
            print(f"Unknown mode: {mode}")
    
    finally:
        tester.close()

if __name__ == "__main__":
    main()
