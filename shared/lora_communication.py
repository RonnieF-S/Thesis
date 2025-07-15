"""
LoRa Communication Module
Universal LoRa communication interface for both ground station and UAV
"""

import serial
import time
import threading
from typing import Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import LORA_PORT, LORA_BAUDRATE
from shared import SimpleLogger as logger

class LoRaCommunication:
    def __init__(self, port=LORA_PORT, baudrate=LORA_BAUDRATE):
        """
        Initialize LoRa communication
        
        Args:
            port: Serial port for Heltec LoRa module
            baudrate: Communication speed with Heltec module
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.lock = threading.Lock()
        self.last_message_time = 0
        
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
                timeout=1
            )
            
            logger.info(f"LoRa module connected on {self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to LoRa module: {e}")
            raise
    
    def send_message(self, message: str) -> bool:
        """
        Send message via LoRa
        
        Args:
            message: Message string to send
            
        Returns:
            True if sent successfully
        """
        if not self.serial_conn:
            return False
        
        try:
            with self.lock:
                if not message.endswith('\n'):
                    message += '\n'
                
                self.serial_conn.write(message.encode())
                self.serial_conn.flush()
                logger.info(f"LoRa sent: {message.strip()}")
                return True
            
        except Exception as e:
            logger.error(f"Error sending LoRa message: {e}")
            return False
    
    def receive_message(self, timeout=1.0) -> Optional[str]:
        """
        Receive message from LoRa
        
        Args:
            timeout: Maximum time to wait for message
            
        Returns:
            Received message string or None if timeout
        """
        if not self.serial_conn:
            return None
        
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.serial_conn.in_waiting > 0:
                    with self.lock:
                        message = self.serial_conn.readline().decode().strip()
                        if message:
                            logger.info(f"LoRa received: {message}")
                            self.last_message_time = time.time()
                            return message
                time.sleep(0.01)  # Prevent CPU spinning
            
        except Exception as e:
            logger.error(f"Error receiving LoRa message: {e}")
        
        return None
    
    def is_connected(self) -> bool:
        """Check if LoRa module is connected and ready"""
        return self.serial_conn is not None and self.serial_conn.is_open
    
    def get_last_message_time(self) -> float:
        """Get timestamp of last received message"""
        return self.last_message_time
    
    def is_peer_connected(self, timeout=30) -> bool:
        """Check if peer responded within timeout period"""
        return (time.time() - self.last_message_time) < timeout
    
    def close(self):
        """Close LoRa connection"""
        if self.serial_conn and self.serial_conn.is_open:
            with self.lock:
                self.serial_conn.close()
                self.serial_conn = None
                logger.info("LoRa communication connection closed")
        else:
            logger.warning("LoRa connection already closed or was never opened")

# Embedded test
if __name__ == "__main__":
    print("LoRa communication - use test files for testing")
