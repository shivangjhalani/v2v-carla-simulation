import carla
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from queue import Queue
from threading import Lock
import weakref

@dataclass
class SensorConfig:
    enabled: bool
    type: str
    attributes: Dict[str, str]
    transform: carla.Transform = carla.Transform()

class SensorManager:
    def __init__(self, world: carla.World, config: Dict):
        self.world = world
        self.blueprint_library = world.get_blueprint_library()
        self.sensors: Dict[int, List[carla.Sensor]] = {}
        self.sensor_data: Dict[int, Dict[str, Queue]] = {}
        self._data_locks: Dict[int, Lock] = {}
        self.max_queue_size = 10
        
        self.sensor_configs = self._parse_sensor_configs(config['sensors'])

    def _parse_sensor_configs(self, config: Dict) -> Dict[str, SensorConfig]:
        """Parse sensor configurations from config file"""
        sensor_types = {
            'collision': ('sensor.other.collision', {}),
            'lane_invasion': ('sensor.other.lane_invasion', {}),
            'gnss': ('sensor.other.gnss', {
                'noise_alt_bias': str(config['gnss']['noise_alt']),
                'noise_lat_bias': str(config['gnss']['noise_lat']),
                'noise_lon_bias': str(config['gnss']['noise_lon'])
            }),
            'imu': ('sensor.other.imu', {}),
            'lidar': ('sensor.lidar.ray_cast', {
                'points_per_second': str(config['lidar']['points_per_second']),
                'rotation_frequency': str(config['lidar']['rotation_frequency']),
                'channels': str(config['lidar']['channels']),
                'range': str(config['lidar']['range'])
            })
        }
        
        return {
            sensor_type: SensorConfig(
                enabled=config[sensor_type]['enabled'],
                type=blueprint_id,
                attributes=attributes
            )
            for sensor_type, (blueprint_id, attributes) in sensor_types.items()
        }

    def attach_sensors(self, vehicle: carla.Vehicle) -> None:
        """Attach configured sensors to vehicle"""
        if vehicle.id in self.sensors:
            return

        self.sensors[vehicle.id] = []
        self._data_locks[vehicle.id] = Lock()
        self.sensor_data[vehicle.id] = {}

        for sensor_type, config in self.sensor_configs.items():
            if not config.enabled:
                continue

            try:
                sensor = self._spawn_sensor(vehicle, config)
                if sensor:
                    self.sensors[vehicle.id].append(sensor)
                    self._setup_sensor_callback(sensor, vehicle.id, sensor_type)
            except Exception as e:
                logging.error(f"Failed to attach {sensor_type} to vehicle {vehicle.id}: {e}")

    def _spawn_sensor(self, vehicle: carla.Vehicle, config: SensorConfig) -> Optional[carla.Sensor]:
        """Spawn a sensor with given configuration"""
        try:
            bp = self.blueprint_library.find(config.type)
            for attr, value in config.attributes.items():
                bp.set_attribute(attr, value)
            return self.world.spawn_actor(bp, config.transform, attach_to=vehicle)
        except Exception as e:
            logging.error(f"Error spawning sensor {config.type}: {e}")
            return None

    def _setup_sensor_callback(self, sensor: carla.Sensor, vehicle_id: int, sensor_type: str) -> None:
        """Setup sensor data callback with thread safety"""
        if vehicle_id not in self.sensor_data:
            self.sensor_data[vehicle_id] = {}
        if sensor_type not in self.sensor_data[vehicle_id]:
            self.sensor_data[vehicle_id][sensor_type] = Queue(maxsize=self.max_queue_size)

        def callback(data):
            with self._data_locks[vehicle_id]:
                queue = self.sensor_data[vehicle_id][sensor_type]
                if queue.full():
                    queue.get()
                queue.put(data)

        sensor.listen(callback)

    def get_sensor_data(self, vehicle_id: int) -> Dict:
        """Get latest sensor data for vehicle"""
        if vehicle_id not in self.sensor_data:
            return {}

        with self._data_locks[vehicle_id]:
            return {
                sensor_type: queue.queue[-1]
                for sensor_type, queue in self.sensor_data[vehicle_id].items()
                if not queue.empty()
            }

    def cleanup(self) -> None:
        """Cleanup all sensors safely"""
        for vehicle_id in list(self.sensors.keys()):
            with self._data_locks[vehicle_id]:
                for sensor in self.sensors[vehicle_id]:
                    if sensor and sensor.is_alive:
                        try:
                            sensor.stop()
                            sensor.destroy()
                        except Exception as e:
                            logging.error(f"Error destroying sensor: {e}")
        
        self.sensors.clear()
        self.sensor_data.clear()
        self._data_locks.clear()
