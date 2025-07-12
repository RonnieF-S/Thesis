#!/usr/bin/env python3
"""
Test script for LoRa communication
Use this to verify LoRa modules are working correctly
"""

import serial
import time
import threading
import sys

class LoRaTest:
    def __init__(self, port='/dev/ttyAMA2', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        
    def connect(self):
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            print(f"Connected to LoRa module on {self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def send_test_packet(self, message):
        if not self.serial_conn:
            return False
        
        try:
            packet = f"{message}\n"
            self.serial_conn.write(packet.encode())
            print(f"Sent: {message}")
            return True
        except Exception as e:
            print(f"Send error: {e}")
            return False
    
    def listen_for_packets(self, duration=10):
        if not self.serial_conn:
            return
        
        print(f"Listening for {duration} seconds...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode().strip()
                    if line:
                        print(f"Received: {line}")
            except Exception as e:
                print(f"Receive error: {e}")
            
            time.sleep(0.1)
    
    def interactive_test(self):
        print("Interactive LoRa Test Mode")
        print("Type messages to send, 'listen' to listen, 'quit' to exit")
        
        while True:
            try:
                command = input("> ").strip()
                
                if command.lower() == 'quit':
                    break
                elif command.lower() == 'listen':
                    self.listen_for_packets(10)
                elif command:
                    self.send_test_packet(command)
                    
            except KeyboardInterrupt:
                break
    
    def automated_test(self):
        print("Running automated LoRa test...")
        
        # Test packet transmission
        test_packets = [
            "TEST,12345.67,Hello",
            "WIND,12346.78,270.5,3.2",
            "UAV,12347.89,-31.9502,115.8563,42.1,412.8"
        ]
        
        for packet in test_packets:
            self.send_test_packet(packet)
            time.sleep(1)
        
        # Listen for responses
        self.listen_for_packets(5)
    
    def close(self):
        if self.serial_conn:
            self.serial_conn.close()
            print("Connection closed")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_lora.py <mode> [port]")
        print("Modes: interactive, auto, listen")
        print("Default port: /dev/ttyAMA2")
        return
    
    mode = sys.argv[1]
    port = sys.argv[2] if len(sys.argv) > 2 else '/dev/ttyAMA2'
    
    tester = LoRaTest(port)
    
    if not tester.connect():
        return
    
    try:
        if mode == 'interactive':
            tester.interactive_test()
        elif mode == 'auto':
            tester.automated_test()
        elif mode == 'listen':
            tester.listen_for_packets(30)
        else:
            print(f"Unknown mode: {mode}")
    
    finally:
        tester.close()

if __name__ == "__main__":
    main()
