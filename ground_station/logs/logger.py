"""
Ground Station Logger - Structured logging for ground station operations
"""

import json
import time
from datetime import datetime
from typing import Dict, Any
import os

class GroundStationLogger:
    def __init__(self, log_dir="/var/log/ground_station", log_file="ground_station.jsonl"):
        """Initialize ground station logger"""
        self.log_dir = log_dir
        self.log_file = log_file
        self.log_path = os.path.join(log_dir, log_file)
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Log startup
        self.log_info("Ground Station Logger initialized")
    
    def _write_log_entry(self, entry: Dict[str, Any]):
        """Write log entry to file"""
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def log_event(self, event_data: Dict[str, Any]):
        """Log a structured event"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "EVENT",
            **event_data
        }
        
        self._write_log_entry(entry)
        print(f"EVENT: {event_data.get('event', 'Unknown')}")
    
    def log_info(self, message: str, **kwargs):
        """Log informational message"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "INFO",
            "message": message,
            **kwargs
        }
        
        self._write_log_entry(entry)
        print(f"INFO: {message}")
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "WARNING",
            "message": message,
            **kwargs
        }
        
        self._write_log_entry(entry)
        print(f"WARNING: {message}")
    
    def log_error(self, message: str, **kwargs):
        """Log error message"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "ERROR",
            "message": message,
            **kwargs
        }
        
        self._write_log_entry(entry)
        print(f"ERROR: {message}")
    
    def log_communication(self, direction: str, packet: str, success: bool = True):
        """Log communication event"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "COMM",
            "direction": direction,  # "TX" or "RX"
            "packet": packet,
            "success": success
        }
        
        self._write_log_entry(entry)
        print(f"COMM {direction}: {packet}")
    
    def log_wind_data(self, wind_data: Dict[str, Any]):
        """Log wind sensor reading"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "SENSOR",
            "sensor_type": "wind",
            "data": wind_data
        }
        
        self._write_log_entry(entry)
    
    def log_transmission_summary(self, total_sent: int, total_responses: int, 
                                avg_rtt_ms: float, error_rate: float):
        """Log transmission statistics summary"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "STATS",
            "total_packets_sent": total_sent,
            "total_responses_received": total_responses,
            "average_rtt_ms": avg_rtt_ms,
            "packet_loss_rate": error_rate,
            "success_rate": 1.0 - error_rate
        }
        
        self._write_log_entry(entry)
        print(f"STATS: {total_sent} sent, {total_responses} responses, {avg_rtt_ms:.1f}ms RTT, {error_rate:.1%} loss")

# Test code
if __name__ == "__main__":
    logger = GroundStationLogger(log_dir="./test_logs")
    
    # Test different log types
    logger.log_info("Starting ground station test")
    
    logger.log_wind_data({"direction": 270.5, "speed": 3.2, "temperature": 22.1})
    
    logger.log_communication("TX", "WIND,172347.20,238.5,4.2")
    logger.log_communication("RX", "UAV,172347.45,-31.9502,115.8563,42.1,412.8")
    
    logger.log_event({
        "event": "TX_WIND",
        "packet": "WIND,172347.20,238.5,4.2",
        "retries": 0,
        "response_received": True,
        "response_packet": "UAV,172347.45,-31.9502,115.8563,42.1,412.8",
        "round_trip_ms": 250,
        "wind_data": {"direction": 238.5, "speed": 4.2}
    })
    
    logger.log_transmission_summary(100, 95, 245.6, 0.05)
    
    logger.log_warning("High packet loss detected")
    logger.log_error("LoRa communication failed")
    
    print("Test logging completed. Check ./test_logs/ground_station.jsonl")
