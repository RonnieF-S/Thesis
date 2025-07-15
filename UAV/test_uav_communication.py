"""
UAV LoRa Communication Test
Tests LoRa responder functionality with ping/pong communication
"""

import sys
import os
import time

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.lora_communication import LoRaCommunication
from config import TEST_PING_MSG, TEST_PONG_MSG
from shared import SimpleLogger as logger

def generate_test_response(message: str) -> str:
    """
    Generate test-specific responses for LoRa communication
    
    Args:
        message: Received message
        
    Returns:
        Response string
    """
    timestamp = int(time.time())
    
    # Parse message type
    if message.startswith(TEST_PING_MSG):
        # Handle test ping messages: TEST_PING,74,1752578431
        parts = message.split(',')
        if len(parts) >= 3:
            test_num = parts[1]
            orig_timestamp = parts[2]
            return f"{TEST_PONG_MSG},{test_num},{timestamp},UAV_OK"
        else:
            return f"{TEST_PONG_MSG},{timestamp},UAV_OK"
    
    elif message.startswith("PING"):
        # Respond to regular ping with pong
        return f"PONG,{timestamp},UAV_ONLINE"
    
    elif message.startswith("STATUS"):
        # Respond with UAV status
        return f"STATUS,{timestamp},FLYING,GPS_OK,CO2_OK"
    
    elif message.startswith("COMMAND"):
        # Acknowledge command receipt
        return f"CMD_ACK,{timestamp},RECEIVED"
    
    else:
        # Generic acknowledgment
        return f"ACK,{timestamp},RECEIVED"

def test_ping_pong_responder():
    """Test ping/pong response functionality"""
    try:
        print("UAV LoRa Communication Test")
        print("===========================")
        
        # Initialize LoRa communication
        lora = LoRaCommunication()
        print(f"Connected to LoRa module on {lora.port}")
        
        message_count = 0
        
        print("\nListening for ping messages... (Ctrl+C to stop)")
        print("Make sure Ground Station test is running: python ground_station/test_gs_communication.py")
        print("-" * 60)
        
        while True:
            # Listen for incoming message
            message = lora.receive_message(timeout=1.0)
            
            if message:
                message_count += 1
                print(f"[{message_count}] Received: {message}")
                
                # Generate test response
                response = generate_test_response(message)
                print(f"[{message_count}] Sending: {response}")
                
                # Send response
                success = lora.send_message(response)
                
                if success:
                    print(f"[{message_count}] SUCCESS - Response sent")
                else:
                    print(f"[{message_count}] FAILED - Could not send response")
                
                print("-" * 60)
            
            # Small delay to prevent CPU spinning
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        if 'lora' in locals():
            lora.close()
            print("LoRa communication closed")

if __name__ == "__main__":
    test_ping_pong_responder()
