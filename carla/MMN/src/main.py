import carla
import signal
import time
import logging
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .vehicle_manager import VehicleManager
from .sensor_manager import SensorManager
from .data_structures import VehicleState, PointCloudData
from .utils.logger import VehicleLogger
from .utils.config_loader import load_config
from .scenario_manager import ScenarioType, ScenarioConfig
from .communication import Communication
from .dashboard_app import DashboardApplication
import keyboard
import numpy as np
import numpy.typing as npt
from datetime import datetime
from .utils.point_cloud_merger import PointCloudMerger

@dataclass
class SimulationConfig:
    num_vehicles: int
    tick_rate: float
    port: int = 2000
    timeout: float = 10.0
    scenario: ScenarioType = ScenarioType.URBAN_DRIVING
    weather: str = 'Clear'
    time_of_day: str = 'Noon'
    traffic_density: float = 0.5

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'SimulationConfig':
        sim_config = config['simulation']
        return cls(**{
            k: sim_config.get(k, v.default)
            for k, v in cls.__dataclass_fields__.items()
        })

    def to_scenario_config(self) -> ScenarioConfig:
        """Convert to ScenarioConfig for ScenarioManager"""
        return ScenarioConfig(
            type=self.scenario,
            num_vehicles=self.num_vehicles,
            weather=self.weather,
            time_of_day=self.time_of_day,
            traffic_density=self.traffic_density
        )

    def validate(self):
        """Validate configuration values"""
        if self.num_vehicles < 1:
            raise ValueError("num_vehicles must be at least 1")
        if not 0.016 <= self.tick_rate <= 0.1:
            raise ValueError("tick_rate must be between 0.016 and 0.1")
        if self.port < 0:
            raise ValueError("port must be positive")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

class SimulationManager:
    def __init__(self, config_path: Optional[str] = None):
        # Use default config path if none provided
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), 
            '..', 'config',  # Go up one level to find config directory
            'settings.yaml'  # Use settings.yaml instead of simulation_config.yaml
        )
        
        # Load and validate config
        try:
            self.config = load_config(self.config_path)
            self.sim_config = SimulationConfig.from_dict(self.config)
            self.sim_config.validate()
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            raise
        
        # Initialize CARLA client with config values
        self.client = carla.Client('localhost', self.sim_config.port)
        self.client.set_timeout(self.sim_config.timeout)
        self.world = self.client.get_world()
        
        # Set up world settings
        self._setup_world()
        
        # Initialize components
        self._init_components()
        
        # Setup state variables
        self.running = True
        self.following_vehicle_id = None
        self.spectator = self.world.get_spectator()
        
        # Register interrupt handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Initialize dashboard
        self.dashboard_app = DashboardApplication(self)

    def _setup_world(self):
        """Configure world settings"""
        settings = self.world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = self.sim_config.tick_rate
        self.world.apply_settings(settings)

    def _init_components(self):
        """Initialize all component managers"""
        self.vehicle_manager = VehicleManager(self.world, self.client)
        self.sensor_manager = SensorManager(self.world, self.config)
        self.communication = Communication()
        self.point_cloud_merger = PointCloudMerger(max_point_age=1.0)
        
        if self.config['logging']['enabled']:
            self.vehicle_logger = VehicleLogger(self.config)

    def signal_handler(self, sig, frame):
        print('\nReceived interrupt signal. Cleaning up...')
        self.running = False
        
    def _update_spectator(self):
        if self.following_vehicle_id is None:
            return
            
        vehicle = self.vehicle_manager.vehicles.get(self.following_vehicle_id)
        if not vehicle or not vehicle.is_alive:
            logging.warning(f"Vehicle {self.following_vehicle_id} no longer exists")
            self.following_vehicle_id = None
            return
            
        # Calculate camera position behind and above vehicle
        vehicle_transform = vehicle.get_transform()
        vehicle_location = vehicle_transform.location
        vehicle_rotation = vehicle_transform.rotation
        
        # Position camera 10 units behind and 5 units above vehicle
        camera_transform = carla.Transform(
            carla.Location(
                x=vehicle_location.x - 10 * vehicle_rotation.get_forward_vector().x,
                y=vehicle_location.y - 10 * vehicle_rotation.get_forward_vector().y,
                z=vehicle_location.z + 5
            ),
            vehicle_rotation
        )
        
        self.spectator.set_transform(camera_transform)
    
    def _handle_keyboard_input(self):
        try:
            for key in '123456789':
                if keyboard.is_pressed(key):
                    seq_id = int(key)
                    # Check if this sequential ID exists in vehicle manager
                    if seq_id in self.vehicle_manager.get_sequential_ids():
                        self.following_vehicle_id = seq_id
                    else:
                        print(f"No vehicle with ID {seq_id}")
                    return
                    
            if keyboard.is_pressed('esc'):
                self.following_vehicle_id = None
                
        except Exception as e:
            print(f"Error handling keyboard input: {e}")
    
    def run(self):
        """Run the simulation"""
        try:
            # Initialize vehicles and sensors
            vehicles = self._init_vehicles()
            if not vehicles:
                raise RuntimeError("No vehicles spawned")
            
            # Print available controls after spawning vehicles
            self._print_vehicle_controls()
            
            # Create initial vehicle states and update dashboards
            initial_states = self._update_vehicle_states()
            if self.dashboard_app:
                self.dashboard_app.create_dashboards(initial_states)
            
            # Main simulation loop
            while self.running:
                self.world.tick()
                self._handle_keyboard_input()
                
                # Update vehicle states and V2V network
                vehicle_states = self._update_vehicle_states()
                
                # Update V2V network with new states
                for vid, state in vehicle_states.items():
                    self.dashboard_app.v2v_network.update_vehicle_state(vid, state)
                
                if self.following_vehicle_id:
                    self._update_spectator()
                
                # Process Qt events and update dashboards
                if self.dashboard_app:
                    self.dashboard_app.update_dashboards()
                    self.dashboard_app.app.processEvents()
            
            return True
            
        except Exception as e:
            logging.error(f"Error in simulation: {e}")
            return False
        finally:
            self.cleanup()

    def _init_vehicles(self):
        """Initialize vehicles and attach sensors"""
        vehicles = self.vehicle_manager.spawn_vehicles(
            self.sim_config.num_vehicles
        )
        
        if not vehicles:
            logging.error("Failed to spawn any vehicles")
            return []
        
        for vehicle in vehicles:
            self.sensor_manager.attach_sensors(vehicle)
        return vehicles

    def _print_vehicle_controls(self):
        """Print available vehicle controls"""
        print("\nAvailable vehicle IDs:")
        sequential_ids = self.vehicle_manager.get_sequential_ids()
        if sequential_ids:
            for seq_id in sequential_ids:
                print(f"Press {seq_id} to follow vehicle {seq_id}")
        else:
            print("No vehicles available")
        print("Press ESC to stop following\n")

    def _update_vehicle_states(self):
        """Update vehicle states with optimized batch processing"""
        vehicles = self.vehicle_manager.get_vehicles()
        if not vehicles:
            logging.warning("No vehicles found in simulation")
            return {}
        
        # Pre-allocate dictionary for better memory usage
        vehicle_states = {}
        other_vehicles_cache = {}
        
        # First pass: Create all vehicle states
        for vehicle in vehicles:
            seq_id = self.vehicle_manager.get_sequential_id(vehicle.id)
            if seq_id is not None:
                state = self._create_vehicle_state(vehicle, seq_id)
                vehicle_states[seq_id] = state
                other_vehicles_cache[seq_id] = state
        
        # Second pass: Update other_vehicles efficiently
        for state in vehicle_states.values():
            state.other_vehicles = {
                vid: vstate for vid, vstate in other_vehicles_cache.items() 
                if vid != state.vehicle_id
            }
            
            if self.point_cloud_merger:
                state.combined_point_cloud = self.point_cloud_merger.merge_point_clouds(
                    state, state.other_vehicles
                )
        
        # Batch process communications and logging
        if vehicle_states:
            self._batch_process_vehicle_states(vehicle_states)
        
        return vehicle_states

    def _batch_process_vehicle_states(self, vehicle_states):
        """Batch process communications and logging for better performance"""
        # Prepare all messages first
        messages = [(seq_id, state) for seq_id, state in vehicle_states.items()]
        
        # Batch send communications
        for seq_id, state in messages:
            self.communication.broadcast_vehicle_state(state)
        
        # Batch logging if enabled
        if hasattr(self, 'vehicle_logger') and self.vehicle_logger:
            for seq_id, state in messages:
                self.vehicle_logger.log_vehicle_data(seq_id, state, state.other_vehicles)

    def _create_vehicle_state(self, vehicle: carla.Vehicle, seq_id: int, 
                            transform: Optional[carla.Transform] = None) -> VehicleState:
        """Create vehicle state with cached transforms"""
        transform = transform or vehicle.get_transform()
        velocity = vehicle.get_velocity()
        
        # Calculate transform matrix
        transform_matrix = np.eye(4, dtype=np.float32)
        rotation_matrix = self._get_rotation_matrix(transform.rotation)
        transform_matrix[:3, :3] = rotation_matrix
        transform_matrix[:3, 3] = [transform.location.x, 
                                  transform.location.y, 
                                  transform.location.z]
        
        # Calculate speed
        speed = (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5 * 3.6  # m/s to km/h
        
        # Get sensor data and process point clouds
        sensor_data = self.sensor_manager.get_sensor_data(vehicle.id)
        point_cloud_cache = self._process_point_clouds(seq_id, sensor_data)
        
        return VehicleState(
            vehicle_id=seq_id,
            timestamp=datetime.now(),
            location=(transform.location.x, transform.location.y, transform.location.z),
            rotation=(transform.rotation.pitch, transform.rotation.yaw, transform.rotation.roll),
            velocity=(velocity.x, velocity.y, velocity.z),
            speed=speed,
            sensor_data=sensor_data,
            other_vehicles={},
            transform_matrix=transform_matrix,
            point_cloud_cache=point_cloud_cache
        )

    def _get_rotation_matrix(self, rotation: carla.Rotation) -> npt.NDArray[np.float32]:
        """Convert CARLA rotation to 3x3 rotation matrix"""
        pitch, yaw, roll = np.radians([rotation.pitch, rotation.yaw, rotation.roll])
        
        # Create rotation matrices for each axis
        R_pitch = np.array([
            [np.cos(pitch), 0, np.sin(pitch)],
            [0, 1, 0],
            [-np.sin(pitch), 0, np.cos(pitch)]
        ], dtype=np.float32)
        
        R_yaw = np.array([
            [np.cos(yaw), -np.sin(yaw), 0],
            [np.sin(yaw), np.cos(yaw), 0],
            [0, 0, 1]
        ], dtype=np.float32)
        
        R_roll = np.array([
            [1, 0, 0],
            [0, np.cos(roll), -np.sin(roll)],
            [0, np.sin(roll), np.cos(roll)]
        ], dtype=np.float32)
        
        # Combine rotations
        return R_yaw @ R_pitch @ R_roll

    def _process_point_clouds(self, vehicle_id: int, sensor_data: dict) -> dict:
        """Process point cloud data from sensors"""
        point_cloud_cache = {}
        
        # Process each sensor that provides point cloud data
        for sensor_type, data in sensor_data.items():
            if sensor_type in ['lidar', 'semantic_lidar']:
                if data is not None and hasattr(data, 'raw_data'):
                    # Convert raw data to point cloud format
                    point_cloud = self._convert_point_cloud_data(
                        data.raw_data,
                        vehicle_id,
                        sensor_type
                    )
                    point_cloud_cache[sensor_type] = point_cloud
        
        return point_cloud_cache

    def _convert_point_cloud_data(self, raw_data, vehicle_id: int, sensor_type: str) -> PointCloudData:
        """Convert raw sensor data to point cloud format"""
        # Convert raw data to numpy array
        data_array = np.frombuffer(raw_data, dtype=np.float32).reshape([-1, 4])
        
        # Extract points (x, y, z)
        points = data_array[:, :3]
        
        # Create timestamps array
        timestamps = np.full(len(points), time.time(), dtype=np.float32)
        
        # Extract tags for semantic lidar, None for regular lidar
        tags = data_array[:, 3].astype(np.int32) if sensor_type == 'semantic_lidar' else None
        
        return PointCloudData(
            points=points,
            timestamps=timestamps,
            tags=tags,
            source_vehicle=vehicle_id
        )

    def cleanup(self):
        """Cleanup simulation resources"""
        try:
            # First cleanup dashboard
            if hasattr(self, 'dashboard_app') and self.dashboard_app:
                self.dashboard_app.cleanup()
            
            # Then cleanup other components
            if hasattr(self, 'sensor_manager'):
                self.sensor_manager.cleanup()
            
            if hasattr(self, 'vehicle_manager'):
                self.vehicle_manager.cleanup()
            
            if hasattr(self, 'vehicle_logger'):
                self.vehicle_logger.cleanup()
            
            # Reset world settings
            if hasattr(self, 'world'):
                settings = self.world.get_settings()
                settings.synchronous_mode = False
                settings.fixed_delta_seconds = None
                self.world.apply_settings(settings)
            
            if hasattr(self, 'client'):
                self.client = None
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
        finally:
            logging.info("Cleanup completed")

def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    sim = SimulationManager()
    sim.run()

if __name__ == "__main__":
    main()