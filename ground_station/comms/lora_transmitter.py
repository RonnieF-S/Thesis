"""
LoRa Transmitter for Ground Station
Handles sending packets to UAV and receiving responses
"""

import serial
import time
import threading
from typing import Optional

class LoRaTransmitter:
    def __init__(self, port='/dev/ttyAMA2', baudrate=115200):
        """
        Initialize LoRa transmitter
        
        Args:
            port: Serial port for Heltec LoRa module (UART3: GPIO4/5)
            baudrate: Communication speed with Heltec module
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.response_buffer = []
        self.buffer_lock = threading.Lock()
        self.listening = False
        
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
            
            # Start background listening thread
            self.listening = True
            self.listen_thread = threading.Thread(target=self._background_listen)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            
            print(f"LoRa transmitter connected on {self.port}")
            
        except Exception as e:
            print(f"Failed to connect to LoRa module: {e}")
            raise
    
    def _background_listen(self):
        """Background thread to continuously listen for responses"""
        while self.listening and self.serial_conn:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode().strip()
                    
                    if line:
                        with self.buffer_lock:
                            self.response_buffer.append({
                                'data': line,
                                'timestamp': time.time()
                            })
                        
                        print(f"LoRa received: {line}")
                
                time.sleep(0.01)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                print(f"Error in background listen: {e}")
                time.sleep(1)
    
    def send_packet(self, packet: str) -> bool:
        """
        Send packet via LoRa
        
        Args:
            packet: Packet string to send
            
        Returns:
            True if sent successfully
        """
        if not self.serial_conn:
            return False
        
        try:
            # Clear any old responses
            with self.buffer_lock:
                self.response_buffer.clear()
            
            # Ensure packet ends with newline
            if not packet.endswith('\n'):
                packet += '\n'
            
            self.serial_conn.write(packet.encode())
            self.serial_conn.flush()
            
            print(f"LoRa sent: {packet.strip()}")
            return True
            
        except Exception as e:
            print(f"Error sending LoRa packet: {e}")
            return False
    
    def wait_for_response(self, timeout=10.0) -> Optional[str]:
        """
        Wait for response packet from UAV
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Response packet string or None on timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self.buffer_lock:
                if self.response_buffer:
                    # Return the oldest response
                    response = self.response_buffer.pop(0)
                    return response['data']
            
            time.sleep(0.01)
        
        print("Timeout waiting for LoRa response")
        return None
    
    def get_last_response(self) -> Optional[str]:
        """Get the most recent response without waiting"""
        with self.buffer_lock:
            if self.response_buffer:
                return self.response_buffer[-1]['data']
        return None
    
    def clear_response_buffer(self):
        """Clear the response buffer"""
        with self.buffer_lock:
            self.response_buffer.clear()
    
    def send_and_wait(self, packet: str, timeout=10.0) -> Optional[str]:
        """
        Send packet and wait for response in one call
        
        Args:
            packet: Packet to send
            timeout: Maximum wait time for response
            
        Returns:
            Response packet or None
        """
        if self.send_packet(packet):
            return self.wait_for_response(timeout)
        return None
    
    def test_connection(self) -> bool:
        """Test LoRa module connection"""
        if not self.serial_conn:
            return False
        
        try:
            # Send test packet
            test_packet = "TEST_CONNECTION\n"
            self.serial_conn.write(test_packet.encode())
            time.sleep(0.1)
            
            # Check if we can communicate (basic test)
            return True
            
        except Exception as e:
            print(f"LoRa connection test failed: {e}")
            return False
    
    def get_signal_strength(self) -> Optional[int]:
        """Get LoRa signal strength (RSSI)"""
        # TODO: Implement if Heltec firmware supports RSSI reporting
        # This would require custom firmware commands
        return None
    
    def set_transmit_power(self, power_dbm: int) -> bool:
        """Set LoRa transmit power"""
        # TODO: Implement if Heltec firmware supports power control
        # This would require custom firmware commands
        return False
    
    def close(self):
        """Close LoRa connection"""
        self.listening = False
        
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join(timeout=2)
        
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
        
        print("LoRa transmitter connection closed")

# Test code
if __name__ == "__main__":
    try:
        lora = LoRaTransmitter()
        
        print("Testing LoRa communication...")
        
        # Test sending packets
        test_packets = [
            "TEST,12345.67,270.5,3.2",
            "WIND,12346.78,280.1,4.1",
            "INIT,12347.89,-31.9510,115.8570"
        ]
        
        for packet in test_packets:
            print(f"\nSending: {packet}")
            success = lora.send_packet(packet)
            
            if success:
                response = lora.wait_for_response(timeout=5.0)
                if response:
                    print(f"Response: {response}")
                else:
                    print("No response received")
            else:
                print("Failed to send packet")
            
            time.sleep(2)
        
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        lora.close()
