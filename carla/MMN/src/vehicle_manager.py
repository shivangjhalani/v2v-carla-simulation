import carla
import random
from typing import List, Dict, Optional
import time
from .data_structures import VehicleState
import logging

class VehicleManager:
    def __init__(self, world: carla.World, client: carla.Client):
        self.world = world
        self.client = client
        self.vehicles: Dict[int, carla.Vehicle] = {}
        self.blueprint_library = self.world.get_blueprint_library()
        self.sequential_mapping = {}  # Maps CARLA ID to sequential ID
        self.next_sequential_id = 1
        
        # Initialize traffic manager
        self.traffic_manager = self.client.get_trafficmanager()
        self.traffic_manager.set_global_distance_to_leading_vehicle(2.5)
        self.traffic_manager.set_synchronous_mode(True)
        self.traffic_manager.global_percentage_speed_difference(10.0)
        
    def spawn_vehicles(self, num_vehicles: int) -> List[carla.Vehicle]:
        """Spawn the specified number of vehicles"""
        spawn_points = self.world.get_map().get_spawn_points()
        spawned_vehicles = []
        max_attempts = num_vehicles * 2
        attempts = 0
        
        while len(spawned_vehicles) < num_vehicles and attempts < max_attempts:
            blueprint = random.choice(self.blueprint_library.filter('vehicle.*'))
            spawn_point = random.choice(spawn_points)
            
            try:
                vehicle = self.world.spawn_actor(blueprint, spawn_point)
                seq_id = self.next_sequential_id
                self.sequential_mapping[vehicle.id] = seq_id
                self.vehicles[seq_id] = vehicle
                self.next_sequential_id += 1
                
                # Configure autopilot for this vehicle
                vehicle.set_autopilot(True, self.traffic_manager.get_port())
                self.traffic_manager.auto_lane_change(vehicle, True)
                self.traffic_manager.random_left_lanechange_percentage(vehicle, 10)
                self.traffic_manager.random_right_lanechange_percentage(vehicle, 10)
                
                spawned_vehicles.append(vehicle)
            except RuntimeError as e:
                logging.warning(f"Failed to spawn vehicle: {e}")
            
            attempts += 1
        
        if len(spawned_vehicles) < num_vehicles:
            logging.warning(f"Only spawned {len(spawned_vehicles)}/{num_vehicles} vehicles after {attempts} attempts")
        
        return spawned_vehicles
        
    def get_vehicles(self) -> List[carla.Vehicle]:
        """Get list of all managed vehicles"""
        return list(self.vehicles.values())
        
    def get_sequential_ids(self) -> List[int]:
        """Get list of sequential IDs for all managed vehicles"""
        return sorted(list(self.vehicles.keys()))
        
    def cleanup(self):
        """Cleanup all spawned vehicles"""
        for vehicle in self.vehicles.values():
            if vehicle.is_alive:
                vehicle.destroy()
        self.vehicles.clear()
        self.sequential_mapping.clear()
        self.next_sequential_id = 1
        
    def get_sequential_id(self, carla_id: int) -> Optional[int]:
        """Get sequential ID for a given CARLA vehicle ID"""
        return self.sequential_mapping.get(carla_id)
