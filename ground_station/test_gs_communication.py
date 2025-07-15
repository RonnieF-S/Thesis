"""
Ground Station LoRa Communication Test
Tests LoRa transmitter functionality with ping/pong communication
"""

import sys
import os
import time

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.lora_communication import LoRaCommunication
from config import TEST_PING_MSG, TEST_PONG_MSG
from shared import SimpleLogger as logger

def test_ping_pong():
    """Test basic ping/pong communication with UAV"""
    try:
        print("Ground Station LoRa Communication Test")
        print("=====================================")
        
        # Initialize LoRa communication
        lora = LoRaCommunication()
        print(f"Connected to LoRa module on {lora.port}")
        
        test_count = 0
        successful_pings = 0
        
        print("\nStarting ping/pong test... (Ctrl+C to stop)")
        print("Make sure UAV test is running: python UAV/test_uav_communication.py")
        print("-" * 50)
        
        while True:
            test_count += 1
            
            # Send ping message
            timestamp = int(time.time())
            ping_msg = f"{TEST_PING_MSG},{test_count},{timestamp}"
            
            print(f"[{test_count}] Sending: {ping_msg}")
            success = lora.send_message(ping_msg)
            
            if not success:
                print("Failed to send message")
                continue
            
            # Wait for pong response
            response = lora.receive_message(timeout=3.0)
            
            if response:
                if response.startswith(TEST_PONG_MSG):
                    print(f"[{test_count}] Received: {response}")
                    successful_pings += 1
                    print(f"[{test_count}] SUCCESS - Round trip completed")
                else:
                    print(f"[{test_count}] Unexpected response: {response}")
            else:
                print(f"[{test_count}] TIMEOUT - No response from UAV")
            
            # Show statistics
            success_rate = (successful_pings / test_count) * 100
            print(f"[{test_count}] Stats: {successful_pings}/{test_count} successful ({success_rate:.1f}%)")
            print("-" * 50)
            
            # Wait before next ping
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        if 'lora' in locals():
            lora.close()
            print("LoRa communication closed")

if __name__ == "__main__":
    test_ping_pong()
