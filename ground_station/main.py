#!/usr/bin/env python3
"""
Ground Station Main Control Loop
Sends wind data to UAV via LoRa and logs responses
"""

import time
import sys
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ground_station.sensors.wind_vane_reader import WindVaneReader
from sensors.gps_reader import GPSReader
from comms.lora_transmitter import LoRaTransmitter
from shared import SimpleLogger as logger

class GroundStationController:
    def __init__(self, use_gps=True):
        """Initialize ground station controller"""
        self.wind_sensor = WindVaneReader()
        self.lora = LoRaTransmitter(port='/dev/ttyAMA2')  # UART3 (GPIO4/5)
        
        # GPS setup
        self.use_gps = use_gps
        self.gps = None
        
        if self.use_gps:
            try:
                self.gps = GPSReader(port='/dev/ttyUSB0')
                logger.info("GPS reader initialized")
            except Exception as e:
                logger.warning(f"GPS initialization failed: {e}, using static coordinates")
                self.use_gps = False
        
        # Ground station GPS coordinates (static fallback)
        self.static_lat = -31.9510
        self.static_lon = 115.8570
        
        # Communication settings
        self.transmission_interval = 10.0  # seconds
        self.response_timeout = 10.0       # seconds
        self.max_retries = 3
        
        logger.info("Ground Station Controller initialized")
    
    def get_ground_station_coordinates(self) -> tuple:
        """Get current ground station coordinates (GPS or static)"""
        if self.use_gps and self.gps:
            position = self.gps.get_position()
            if position['valid']:
                return position['lat'], position['lon']
            else:
                logger.warning("GPS fix not available, using static coordinates")
        
        return self.static_lat, self.static_lon
    
    def send_init_packet(self) -> bool:
        """Send initial packet with ground station location"""
        try:
            timestamp = time.time()
            lat, lon = self.get_ground_station_coordinates()
            
            init_packet = f"INIT,{timestamp:.2f},{lat:.6f},{lon:.6f}"
            
            success = self.lora.send_packet(init_packet)
            
            if success:
                logger.info("TX", init_packet, True)
                
                # Wait for UAV acknowledgment
                response = self.lora.wait_for_response(timeout=self.response_timeout)
                
                if response:
                    logger.info("RX", response, True)
                    logger.info("INIT packet acknowledged by UAV")
                    return True
                else:
                    logger.warning("No response to INIT packet")
                    return False
            else:
                logger.error("Failed to send INIT packet")
                return False
                
        except Exception as e:
            logger.error(f"Error sending INIT packet: {e}")
            return False
    
    def send_wind_data(self) -> dict:
        """Send wind data packet and wait for response"""
        result = {
            'packet_sent': False,
            'response_received': False,
            'retries': 0,
            'round_trip_ms': None,
            'response_packet': None
        }
        
        try:
            # Read wind data
            wind_data = self.wind_sensor.read_wind()
            
            # Create wind packet
            timestamp = time.time()
            wind_packet = f"WIND,{timestamp:.2f},{wind_data['direction']:.1f},{wind_data['speed']:.1f}"
            
            # Send with retries
            for attempt in range(self.max_retries + 1):
                start_time = time.time()
                
                success = self.lora.send_packet(wind_packet)
                result['packet_sent'] = success
                result['retries'] = attempt
                
                if not success:
                    logger.error(f"Failed to send wind packet (attempt {attempt + 1})")
                    if attempt < self.max_retries:
                        time.sleep(2)  # Wait before retry
                        continue
                    else:
                        break
                
                logger.info("TX", wind_packet, True)
                
                # Wait for UAV response
                response = self.lora.wait_for_response(timeout=self.response_timeout)
                
                if response:
                    end_time = time.time()
                    result['response_received'] = True
                    result['response_packet'] = response
                    result['round_trip_ms'] = int((end_time - start_time) * 1000)
                    
                    logger.info("RX", response, True)
                    
                    # Log successful transaction
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "event": "TX_WIND",
                        "packet": wind_packet,
                        "retries": attempt,
                        "response_received": True,
                        "response_packet": response,
                        "round_trip_ms": result['round_trip_ms'],
                        "wind_data": wind_data
                    }
                    logger.info(log_entry)
                    
                    break
                else:
                    logger.warning(f"No response to wind packet (attempt {attempt + 1})")
                    if attempt < self.max_retries:
                        time.sleep(2)  # Wait before retry
            
            # Log failed transaction if no response received
            if not result['response_received']:
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "event": "TX_WIND",
                    "packet": wind_packet,
                    "retries": result['retries'],
                    "response_received": False,
                    "response_packet": None,
                    "round_trip_ms": None,
                    "wind_data": wind_data
                }
                logger.info(log_entry)
            
        except Exception as e:
            logger.error(f"Error in wind data transmission: {e}")
        
        return result
    
    def run(self):
        """Main ground station control loop"""
        logger.info("Starting ground station control loop")
        
        try:
            # Send initial packet
            init_success = self.send_init_packet()
            if not init_success:
                logger.warning("Failed to initialize communication with UAV")
            
            # Main transmission loop
            last_transmission = 0
            
            while True:
                current_time = time.time()
                
                # Check if it's time to send wind data
                if current_time - last_transmission >= self.transmission_interval:
                    result = self.send_wind_data()
                    last_transmission = current_time
                    
                    # Print summary
                    if result['response_received']:
                        print(f"Wind data sent successfully (RTT: {result['round_trip_ms']}ms, Retries: {result['retries']})")
                    else:
                        print(f"Wind data transmission failed after {result['retries']} retries")
                
                # Small delay to prevent CPU overload
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Ground station stopped by user")
        except Exception as e:
            logger.error(f"Ground station control loop error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of ground station"""
        logger.info("Shutting down ground station")
        
        try:
            self.wind_sensor.close()
            if self.gps:
                self.gps.close()
            self.lora.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    controller = GroundStationController()
    try:
        controller.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
