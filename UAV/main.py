#!/usr/bin/env python3
"""
UAV Main Control Loop
Handles LoRa communication, sensor reading, GPS, and flight control
"""

import time
import json
import sys
import threading
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sensors.sprintir_reader import SprintIRReader
from comms.lora_responder import LoRaResponder
from dji_sdk.position_reader import PositionReader
from dji_sdk.flight_commander import FlightCommander
from logic.source_localiser import SourceLocaliser
from shared import SimpleLogger as logger

class UAVController:
    def __init__(self):
        """Initialize UAV controller with all subsystems"""
        self.co2_sensor = SprintIRReader(port='/dev/ttyAMA1')  # UART5 (GPIO12/13)
        self.lora = LoRaResponder(port='/dev/ttyAMA2')         # UART3 (GPIO4/5)
        self.gps = PositionReader()
        self.flight_controller = FlightCommander()
        self.localiser = SourceLocaliser()
        self.running = False
        
        logger.info("UAV Controller initialized")
    
    def handle_wind_packet(self, packet_data):
        """Process incoming wind data and respond with UAV telemetry"""
        try:
            # Parse wind packet: WIND,timestamp,wind_direction_deg,wind_speed_mps
            parts = packet_data.strip().split(',')
            if len(parts) != 4 or parts[0] != 'WIND':
                raise ValueError(f"Invalid wind packet format: {packet_data}")
            
            timestamp = float(parts[1])
            wind_direction = float(parts[2])
            wind_speed = float(parts[3])
            
            # Read current sensor data
            co2_ppm = self.co2_sensor.read_co2()
            gps_data = self.gps.get_position()
            
            # Update source estimation
            self.localiser.update_measurement(
                gps_data['lat'], gps_data['lon'], gps_data['alt'],
                co2_ppm, wind_direction, wind_speed
            )
            
            # Get new target waypoint
            target = self.localiser.get_next_waypoint()
            if target:
                self.flight_controller.send_waypoint(target['lat'], target['lon'], target['alt'])
            
            # Create response packet: UAV,timestamp,lat,lon,alt_m,co2_ppm
            response_timestamp = time.time()
            response = f"UAV,{response_timestamp:.2f},{gps_data['lat']:.6f},{gps_data['lon']:.6f},{gps_data['alt']:.1f},{co2_ppm:.1f}"
            
            # Log the interaction
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "event": "RECV_WIND",
                "packet": packet_data.strip(),
                "wind_direction_deg": wind_direction,
                "wind_speed_mps": wind_speed,
                "co2_ppm": co2_ppm,
                "gps": gps_data,
                "response_packet": response,
                "response_sent": True
            }
            logger.info(log_entry)
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling wind packet: {e}")
            return None
    
    def handle_init_packet(self, packet_data):
        """Process initialization packet from ground station"""
        try:
            # Parse init packet: INIT,timestamp,ground_lat,ground_lon
            parts = packet_data.strip().split(',')
            if len(parts) != 4 or parts[0] != 'INIT':
                raise ValueError(f"Invalid init packet format: {packet_data}")
            
            timestamp = float(parts[1])
            ground_lat = float(parts[2])
            ground_lon = float(parts[3])
            
            # Store ground station location for source localisation
            self.localiser.set_ground_station_location(ground_lat, ground_lon)
            
            logger.info(f"Received ground station location: {ground_lat:.6f}, {ground_lon:.6f}")
            
            # Send acknowledgment
            response_timestamp = time.time()
            gps_data = self.gps.get_position()
            response = f"UAV,{response_timestamp:.2f},{gps_data['lat']:.6f},{gps_data['lon']:.6f},{gps_data['alt']:.1f},0.0"
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling init packet: {e}")
            return None
    
    def run(self):
        """Main UAV control loop"""
        self.running = True
        logger.info("Starting UAV control loop")
        
        try:
            while self.running:
                # Check for incoming LoRa packets
                packet = self.lora.receive_packet(timeout=1.0)
                
                if packet:
                    response = None
                    
                    if packet.startswith('WIND'):
                        response = self.handle_wind_packet(packet)
                    elif packet.startswith('INIT'):
                        response = self.handle_init_packet(packet)
                    else:
                        logger.warning(f"Unknown packet type: {packet}")
                    
                    # Send response if generated
                    if response:
                        self.lora.send_response(response)
                
                # Small delay to prevent CPU overload
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("UAV control loop stopped by user")
        except Exception as e:
            logger.error(f"UAV control loop error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of all subsystems"""
        self.running = False
        logger.info("Shutting down UAV controller")
        
        try:
            self.co2_sensor.close()
            self.lora.close()
            self.gps.close()
            self.flight_controller.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    controller = UAVController()
    try:
        controller.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
