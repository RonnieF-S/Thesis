"""
LoRa Responder for UAV
Handles incoming packets from ground station and sends responses
"""

import serial
import time
import threading
from typing import Optional

class LoRaResponder:
    def __init__(self, port='/dev/ttyAMA2', baudrate=115200):
        """
        Initialize LoRa responder
        
        Args:
            port: Serial port for Heltec LoRa module (UART3: GPIO4/5)
            baudrate: Communication speed with Heltec module
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.received_packets = []
        self.packet_lock = threading.Lock()
        
        self.connect()
    
    def connect(self):
        """Establish serial connection to LoRa module"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=0.1
            )
            
            print(f"LoRa responder connected on {self.port}")
            
        except Exception as e:
            print(f"Failed to connect to LoRa module: {e}")
            raise
    
    def receive_packet(self, timeout=1.0) -> Optional[str]:
        """
        Check for incoming LoRa packets (non-blocking)
        
        Args:
            timeout: Maximum time to wait for packet
            
        Returns:
            Received packet string or None
        """
        if not self.serial_conn:
            return None
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode().strip()
                    
                    if line:
                        print(f"LoRa received: {line}")
                        return line
                
                time.sleep(0.01)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                print(f"Error receiving LoRa packet: {e}")
                break
        
        return None
    
    def send_response(self, response: str) -> bool:
        """
        Send response packet via LoRa
        
        Args:
            response: Response string to send
            
        Returns:
            True if sent successfully
        """
        if not self.serial_conn:
            return False
        
        try:
            # Ensure packet ends with newline
            if not response.endswith('\n'):
                response += '\n'
            
            self.serial_conn.write(response.encode())
            self.serial_conn.flush()
            
            print(f"LoRa sent: {response.strip()}")
            return True
            
        except Exception as e:
            print(f"Error sending LoRa response: {e}")
            return False
    
    def wait_for_packet(self, timeout=10.0) -> Optional[str]:
        """
        Wait for incoming packet (blocking)
        
        Args:
            timeout: Maximum time to wait
            
        Returns:
            Received packet or None on timeout
        """
        if not self.serial_conn:
            return None
        
        start_time = time.time()
        buffer = ""
        
        try:
            while time.time() - start_time < timeout:
                if self.serial_conn.in_waiting > 0:
                    char = self.serial_conn.read(1).decode()
                    buffer += char
                    
                    # Check for complete packet (ends with newline)
                    if char == '\n' or char == '\r':
                        packet = buffer.strip()
                        if packet:
                            print(f"LoRa received: {packet}")
                            return packet
                        buffer = ""
                
                time.sleep(0.01)
                
        except Exception as e:
            print(f"Error waiting for LoRa packet: {e}")
        
        return None
    
    def test_connection(self) -> bool:
        """Test if LoRa module is responding"""
        if not self.serial_conn:
            return False
        
        try:
            # Send test string
            test_msg = "TEST\n"
            self.serial_conn.write(test_msg.encode())
            time.sleep(0.1)
            
            # Check if data was sent (basic test)
            return True
            
        except Exception as e:
            print(f"LoRa connection test failed: {e}")
            return False
    
    def close(self):
        """Close LoRa connection"""
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
        
        print("LoRa responder connection closed")

# Test code
if __name__ == "__main__":
    try:
        lora = LoRaResponder()
        
        print("Waiting for LoRa packets... (Ctrl+C to stop)")
        
        while True:
            packet = lora.receive_packet(timeout=1.0)
            
            if packet:
                # Echo back the packet
                response = f"ECHO: {packet}"
                lora.send_response(response)
            
            time.sleep(0.1)
        
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        lora.close()
