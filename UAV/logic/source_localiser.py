"""
Gas Source Localisation Algorithm
Estimates gas source location using concentration, wind, and GPS data
"""

import numpy as np
import time
import math
from typing import Dict, List, Optional, Tuple

class SourceLocaliser:
    def __init__(self):
        """Initialize source localisation algorithm"""
        self.measurements = []
        self.ground_station_pos = None
        self.estimated_source = None
        self.search_pattern = "expanding_spiral"
        self.search_radius = 50.0  # meters
        self.confidence_threshold = 0.7
        
        print("Source localiser initialized")
    
    def set_ground_station_location(self, lat: float, lon: float):
        """Set ground station GPS coordinates"""
        self.ground_station_pos = {'lat': lat, 'lon': lon}
        print(f"Ground station location set: {lat:.6f}, {lon:.6f}")
    
    def update_measurement(self, lat: float, lon: float, alt: float, 
                          co2_ppm: float, wind_dir: float, wind_speed: float):
        """
        Add new measurement for source estimation
        
        Args:
            lat, lon, alt: UAV position
            co2_ppm: CO₂ concentration
            wind_dir: Wind direction in degrees (0=North, 90=East)
            wind_speed: Wind speed in m/s
        """
        measurement = {
            'timestamp': time.time(),
            'lat': lat,
            'lon': lon,
            'alt': alt,
            'co2_ppm': co2_ppm,
            'wind_dir': wind_dir,
            'wind_speed': wind_speed
        }
        
        self.measurements.append(measurement)
        
        # Keep only recent measurements (last 10 minutes)
        cutoff_time = time.time() - 600
        self.measurements = [m for m in self.measurements if m['timestamp'] > cutoff_time]
        
        # Update source estimate
        self._update_source_estimate()
        
        print(f"Measurement added: CO₂={co2_ppm:.1f}ppm, Wind={wind_dir:.1f}°@{wind_speed:.1f}m/s")
    
    def _update_source_estimate(self):
        """Update estimated source location based on all measurements"""
        if len(self.measurements) < 3:
            return  # Need minimum measurements
        
        try:
            # Simple back-tracking algorithm
            # Assume gas travels downwind from source
            
            candidate_sources = []
            
            for measurement in self.measurements[-10:]:  # Use last 10 measurements
                if measurement['co2_ppm'] > 410:  # Above background (≈410ppm)
                    
                    # Calculate upwind direction (opposite to wind)
                    upwind_dir = (measurement['wind_dir'] + 180) % 360
                    
                    # Estimate distance based on concentration and wind speed
                    # Higher concentration = closer to source
                    concentration_factor = max(0.1, (measurement['co2_ppm'] - 410) / 100)
                    estimated_distance = 50.0 / concentration_factor  # Rough estimate
                    
                    # Calculate candidate source position
                    source_lat, source_lon = self._move_position(
                        measurement['lat'], measurement['lon'],
                        upwind_dir, estimated_distance
                    )
                    
                    candidate_sources.append({
                        'lat': source_lat,
                        'lon': source_lon,
                        'confidence': concentration_factor,
                        'distance': estimated_distance
                    })
            
            if candidate_sources:
                # Average the candidate positions weighted by confidence
                total_weight = sum(c['confidence'] for c in candidate_sources)
                
                if total_weight > 0:
                    avg_lat = sum(c['lat'] * c['confidence'] for c in candidate_sources) / total_weight
                    avg_lon = sum(c['lon'] * c['confidence'] for c in candidate_sources) / total_weight
                    
                    self.estimated_source = {
                        'lat': avg_lat,
                        'lon': avg_lon,
                        'confidence': min(1.0, total_weight / len(candidate_sources)),
                        'timestamp': time.time()
                    }
                    
                    print(f"Source estimate updated: {avg_lat:.6f}, {avg_lon:.6f} (confidence: {self.estimated_source['confidence']:.2f})")
        
        except Exception as e:
            print(f"Error updating source estimate: {e}")
    
    def get_next_waypoint(self) -> Optional[Dict]:
        """
        Calculate next waypoint for search pattern
        
        Returns:
            Dictionary with lat, lon, alt for next waypoint
        """
        if not self.measurements:
            return None
        
        current_measurement = self.measurements[-1]
        current_lat = current_measurement['lat']
        current_lon = current_measurement['lon']
        current_alt = current_measurement['alt']
        
        # If we have a high-confidence source estimate, navigate towards it
        if (self.estimated_source and 
            self.estimated_source['confidence'] > self.confidence_threshold):
            
            target_lat = self.estimated_source['lat']
            target_lon = self.estimated_source['lon']
            
            # Maintain current altitude
            return {
                'lat': target_lat,
                'lon': target_lon,
                'alt': current_alt
            }
        
        # Otherwise, continue search pattern
        return self._generate_search_waypoint(current_lat, current_lon, current_alt)
    
    def _generate_search_waypoint(self, current_lat: float, current_lon: float, 
                                current_alt: float) -> Dict:
        """Generate waypoint for search pattern"""
        
        if self.search_pattern == "expanding_spiral":
            # Simple expanding spiral search
            measurement_count = len(self.measurements)
            angle = (measurement_count * 45) % 360  # 45° increments
            radius = min(self.search_radius, 10 + measurement_count * 2)  # Expanding radius
            
            target_lat, target_lon = self._move_position(
                current_lat, current_lon, angle, radius
            )
            
        elif self.search_pattern == "crosswind":
            # Search perpendicular to wind direction
            if self.measurements:
                wind_dir = self.measurements[-1]['wind_dir']
                crosswind_dir = (wind_dir + 90) % 360  # Perpendicular to wind
                
                target_lat, target_lon = self._move_position(
                    current_lat, current_lon, crosswind_dir, 30
                )
            else:
                target_lat, target_lon = current_lat, current_lon
        
        else:
            # Default: stay in place
            target_lat, target_lon = current_lat, current_lon
        
        return {
            'lat': target_lat,
            'lon': target_lon,
            'alt': current_alt
        }
    
    def _move_position(self, lat: float, lon: float, bearing: float, 
                      distance: float) -> Tuple[float, float]:
        """
        Calculate new position given bearing and distance
        
        Args:
            lat, lon: Starting position
            bearing: Direction in degrees (0=North)
            distance: Distance in meters
            
        Returns:
            New (lat, lon) position
        """
        # Convert to radians
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        bearing_rad = math.radians(bearing)
        
        # Earth radius in meters
        R = 6371000
        
        # Calculate new position
        new_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(distance / R) +
            math.cos(lat_rad) * math.sin(distance / R) * math.cos(bearing_rad)
        )
        
        new_lon_rad = lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(distance / R) * math.cos(lat_rad),
            math.cos(distance / R) - math.sin(lat_rad) * math.sin(new_lat_rad)
        )
        
        return math.degrees(new_lat_rad), math.degrees(new_lon_rad)
    
    def get_source_estimate(self) -> Optional[Dict]:
        """Get current source location estimate"""
        return self.estimated_source.copy() if self.estimated_source else None
    
    def get_search_statistics(self) -> Dict:
        """Get statistics about the search"""
        if not self.measurements:
            return {}
        
        co2_values = [m['co2_ppm'] for m in self.measurements]
        
        return {
            'total_measurements': len(self.measurements),
            'max_co2': max(co2_values),
            'min_co2': min(co2_values),
            'avg_co2': sum(co2_values) / len(co2_values),
            'search_time_minutes': (time.time() - self.measurements[0]['timestamp']) / 60,
            'source_confidence': self.estimated_source['confidence'] if self.estimated_source else 0.0
        }

# Test code
if __name__ == "__main__":
    localiser = SourceLocaliser()
    
    # Simulate some measurements
    localiser.set_ground_station_location(-31.9510, 115.8570)
    
    # Test measurements with increasing CO₂ as we approach source
    test_data = [
        (-31.9502, 115.8563, 50.0, 415.0, 270, 3.5),  # Slightly elevated CO₂
        (-31.9500, 115.8565, 50.0, 425.0, 270, 3.5),  # Higher CO₂
        (-31.9498, 115.8567, 50.0, 445.0, 270, 3.5),  # Much higher CO₂
    ]
    
    for lat, lon, alt, co2, wind_dir, wind_speed in test_data:
        localiser.update_measurement(lat, lon, alt, co2, wind_dir, wind_speed)
        
        waypoint = localiser.get_next_waypoint()
        if waypoint:
            print(f"Next waypoint: {waypoint['lat']:.6f}, {waypoint['lon']:.6f}")
        
        time.sleep(1)
    
    # Print final statistics
    stats = localiser.get_search_statistics()
    print(f"Search statistics: {stats}")
    
    source = localiser.get_source_estimate()
    if source:
        print(f"Estimated source: {source['lat']:.6f}, {source['lon']:.6f}")
