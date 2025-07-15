"""
SprintIR-WF-20 CO₂ Sensor Reader
UART interface to read filtered CO₂ concentrations in ppm
"""

import serial
import time
import threading
from typing import Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import CO2_PORT, CO2_BAUDRATE, SENSOR_READ_INTERVAL
from shared import SimpleLogger as logger

class CO2Reader:
    def __init__(self, port=CO2_PORT, baudrate=CO2_BAUDRATE):
        """
        Initialize SprintIR CO₂ sensor
        
        Args:
            port: Serial port (UART5: GPIO12/13)
            baudrate: Communication speed
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.latest_co2 = 0.0
        self.running = False
        self.lock = threading.Lock()
        
        self.connect()
    
    def connect(self):
        """Establish serial connection to sensor"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1
            )
            
            # Start continuous reading thread
            self.running = True
            self.read_thread = threading.Thread(target=self._continuous_read)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            logger.info(f"CO2 sensor connected on {self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to CO2 sensor: {e}")
            raise
    
    def _continuous_read(self):
        """Continuously read CO₂ values in background thread"""
        while self.running and self.serial_conn:
            try:
                # Send command to request CO₂ reading
                self.serial_conn.write(b'Z\r\n')
                
                # Read response
                response = self.serial_conn.readline().decode().strip()
                
                # Parse response format: "Z 00680 z 00659"
                # We want the filtered value (z), which is the second value
                if 'z' in response:
                    parts = response.split()
                    for i, part in enumerate(parts):
                        if part == 'z' and i + 1 < len(parts):
                            try:
                                co2_value = float(parts[i + 1])
                                with self.lock:
                                    self.latest_co2 = co2_value
                                break
                            except ValueError:
                                continue
                
                time.sleep(0.05)  # 20 Hz maximum reading rate
                
            except Exception as e:
                logger.error(f"Error reading from SprintIR sensor: {e}")
                time.sleep(1)  # Wait before retrying
    
    def read_co2(self) -> float:
        """
        Get latest CO₂ reading
        
        Returns:
            CO₂ concentration in ppm
        """
        with self.lock:
            return self.latest_co2
    
    def read_co2_sync(self) -> Optional[float]:
        """
        Synchronously read CO₂ value (blocking)
        
        Returns:
            CO₂ concentration in ppm or None on error
        """
        if not self.serial_conn:
            return None
        
        try:
            # Send command
            self.serial_conn.write(b'Z\r\n')
            
            # Read response with timeout
            response = self.serial_conn.readline().decode().strip()
            
            # Parse response format: "Z 00680 z 00659"
            # Extract the filtered value (z)
            if 'z' in response:
                parts = response.split()
                for i, part in enumerate(parts):
                    if part == 'z' and i + 1 < len(parts):
                        try:
                            return float(parts[i + 1])
                        except ValueError:
                            continue
            
        except Exception as e:
            print(f"Error in synchronous CO₂ read: {e}")
        
        return None
    
    def calibrate_zero(self):
        """Perform zero calibration (use in clean air)"""
        if not self.serial_conn:
            return False
        
        try:
            self.serial_conn.write(b'G\r\n')
            response = self.serial_conn.readline().decode().strip()
            print(f"Zero calibration response: {response}")
            return True
        except Exception as e:
            print(f"Zero calibration failed: {e}")
            return False
    
    def close(self):
        """Close serial connection"""
        self.running = False
        
        if hasattr(self, 'read_thread'):
            self.read_thread.join(timeout=2)
        
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
        
        logger.info("CO2 sensor connection closed")

# Test code
if __name__ == "__main__":
    try:
        sensor = CO2Reader()
        
        print("Reading CO₂ for 10 seconds...")
        for i in range(100):
            co2 = sensor.read_co2()
            print(f"CO₂: {co2:.1f} ppm")
            time.sleep(0.1)
        
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        sensor.close()
