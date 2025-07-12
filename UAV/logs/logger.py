"""
UAV Logger - Structured logging for UAV operations
"""

import json
import time
from datetime import datetime
from typing import Dict, Any
import os

class UAVLogger:
    def __init__(self, log_dir="/var/log/uav", log_file="uav_flight.jsonl"):
        """Initialize UAV logger"""
        self.log_dir = log_dir
        self.log_file = log_file
        self.log_path = os.path.join(log_dir, log_file)
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Log startup
        self.log_info("UAV Logger initialized")
    
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
    
    def log_sensor_data(self, sensor_type: str, data: Dict[str, Any]):
        """Log sensor reading"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "SENSOR",
            "sensor_type": sensor_type,
            "data": data
        }
        
        self._write_log_entry(entry)
    
    def log_communication(self, direction: str, packet: str, success: bool = True):
        """Log communication event"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "COMM",
            "direction": direction,  # "RX" or "TX"
            "packet": packet,
            "success": success
        }
        
        self._write_log_entry(entry)
        print(f"COMM {direction}: {packet}")
    
    def log_flight_command(self, command_type: str, parameters: Dict[str, Any], success: bool = True):
        """Log flight command"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "FLIGHT",
            "command_type": command_type,
            "parameters": parameters,
            "success": success
        }
        
        self._write_log_entry(entry)
        print(f"FLIGHT {command_type}: {parameters}")

# Test code
if __name__ == "__main__":
    logger = UAVLogger(log_dir="./test_logs")
    
    # Test different log types
    logger.log_info("Starting UAV test")
    
    logger.log_sensor_data("co2", {"ppm": 425.6, "temp": 22.1})
    
    logger.log_communication("RX", "WIND,172347.20,238.5,4.2")
    
    logger.log_flight_command("waypoint", {"lat": -31.9502, "lon": 115.8563, "alt": 50.0})
    
    logger.log_event({
        "event": "RECV_WIND",
        "packet": "WIND,172347.20,238.5,4.2",
        "wind_direction_deg": 238.5,
        "wind_speed_mps": 4.2,
        "co2_ppm": 425.6,
        "response_sent": True
    })
    
    logger.log_warning("Low battery detected")
    logger.log_error("Sensor communication failed")
    
    print("Test logging completed. Check ./test_logs/uav_flight.jsonl")
