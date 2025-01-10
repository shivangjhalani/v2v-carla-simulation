import carla
import random
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
import numpy as np
import logging

class ScenarioType(Enum):
    URBAN_DRIVING = "urban_driving"
    HIGHWAY = "highway"
    INTERSECTION = "intersection"
    OVERTAKING = "overtaking"
    EMERGENCY_BRAKING = "emergency_braking"

@dataclass
class ScenarioConfig:
    type: ScenarioType
    num_vehicles: int
    weather: str
    time_of_day: str
    traffic_density: float  # 0.0 to 1.0

class ScenarioManager:
    def __init__(self, world: carla.World, vehicle_manager, sensor_manager):
        self.world = world
        self.vehicle_manager = vehicle_manager
        self.sensor_manager = sensor_manager
        self.active_scenario = None
        
        # Define weather presets
        self.weather_presets = {
            'Clear': carla.WeatherParameters.ClearNoon,
            'Rain': carla.WeatherParameters.HardRainNoon,
            'Fog': carla.WeatherParameters.SoftRainSunset,
            'Night': carla.WeatherParameters.ClearNight
        }
    
    def setup_scenario(self, config: ScenarioConfig):
        """Setup a new scenario based on configuration"""
        self.active_scenario = config
        
        # Set weather
        if config.weather in self.weather_presets:
            self.world.set_weather(self.weather_presets[config.weather])
        
        # Setup specific scenario
        if config.type == ScenarioType.URBAN_DRIVING:
            self._setup_urban_scenario(config)
        elif config.type == ScenarioType.HIGHWAY:
            self._setup_highway_scenario(config)
        elif config.type == ScenarioType.INTERSECTION:
            self._setup_intersection_scenario(config)
        
    def _setup_urban_scenario(self, config: ScenarioConfig):
        """Setup an urban driving scenario with optimized spawning"""
        # Pre-filter spawn points once
        spawn_points = np.array(self.world.get_map().get_spawn_points())
        urban_mask = np.array([self._is_urban_location(p) for p in spawn_points])
        urban_points = spawn_points[urban_mask]
        
        if len(urban_points) < config.num_vehicles:
            logging.warning(f"Only {len(urban_points)} urban spawn points available for {config.num_vehicles} vehicles")
        
        # Batch spawn vehicles
        vehicles = self.vehicle_manager.spawn_vehicles(
            min(config.num_vehicles, len(urban_points)),
            spawn_points=urban_points
        )
        
        # Batch configure traffic manager
        tm = self.vehicle_manager.traffic_manager
        tm.global_percentage_speed_difference(10.0)
        tm.global_distance_to_leading_vehicle(5.0)
        
        # Only set individual parameters when needed
        for vehicle in vehicles:
            tm.set_desired_speed(vehicle, 30.0)  # Urban speed limit
    
    def _setup_highway_scenario(self, config: ScenarioConfig):
        """Setup a highway scenario with optimized spawning"""
        spawn_points = self.world.get_map().get_spawn_points()
        
        # Batch spawn vehicles
        vehicles = self.vehicle_manager.spawn_vehicles(config.num_vehicles)
        
        # Batch configure traffic manager
        tm = self.vehicle_manager.traffic_manager
        tm.global_percentage_speed_difference(-10.0)
        tm.global_distance_to_leading_vehicle(10.0)
        
        # Only set individual parameters when needed
        for vehicle in vehicles:
            tm.set_desired_speed(vehicle, 90.0)  # Highway speed
    
    def _setup_intersection_scenario(self, config: ScenarioConfig):
        """Setup an intersection scenario"""
        # Find intersection points
        intersections = self._find_intersections()
        if not intersections:
            raise RuntimeError("No suitable intersections found")
            
        vehicles = self.vehicle_manager.spawn_vehicles(config.num_vehicles)
        
        tm = self.vehicle_manager.traffic_manager
        for vehicle in vehicles:
            tm.vehicle_percentage_speed_difference(vehicle, 0.0)
            tm.distance_to_leading_vehicle(vehicle, 3.0)
            tm.set_desired_speed(vehicle, 20.0)
    
    def _is_urban_location(self, transform: carla.Transform) -> bool:
        """Check if a location is in an urban area"""
        # This is a simple implementation - could be made more sophisticated
        waypoint = self.world.get_map().get_waypoint(transform.location)
        return waypoint.lane_type == carla.LaneType.Driving and waypoint.road_id < 100
    
    def _find_intersections(self) -> List[carla.Transform]:
        """Find intersection points in the map"""
        waypoints = self.world.get_map().generate_waypoints(2.0)
        return [w.transform for w in waypoints if w.is_intersection]
    
    def cleanup_scenario(self):
        """Clean up the current scenario"""
        if self.active_scenario:
            # Reset weather
            self.world.set_weather(self.weather_presets['Clear'])
            self.active_scenario = None 