from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np
import numpy.typing as npt

@dataclass
class SensorData:
    timestamp: float
    sensor_type: str
    data: Any

@dataclass
class PointCloudData:
    points: npt.NDArray[np.float32]  # Nx3 array of points
    timestamps: npt.NDArray[np.float32]  # N timestamps
    tags: Optional[npt.NDArray[np.int32]] = None  # N semantic tags (if semantic lidar)
    source_vehicle: int = -1  # vehicle_id of source

@dataclass
class CombinedPointCloud:
    points: npt.NDArray[np.float32]  # Combined points from all vehicles
    timestamps: npt.NDArray[np.float32]  # Timestamps for each point
    tags: Optional[npt.NDArray[np.int32]] = None  # Combined semantic tags
    sources: npt.NDArray[np.int32] = None  # Vehicle IDs for each point
    last_update: datetime = field(default_factory=datetime.now)

@dataclass 
class VehicleState:
    vehicle_id: int
    timestamp: datetime
    location: tuple  # (x, y, z)
    rotation: tuple  # (pitch, yaw, roll)
    velocity: tuple  # (x, y, z)
    speed: float  # km/h
    sensor_data: Dict[str, SensorData]
    other_vehicles: Dict[int, 'VehicleState']
    transform_matrix: npt.NDArray[np.float32] = field(default_factory=lambda: np.eye(4, dtype=np.float32))
    point_cloud_cache: Dict[str, PointCloudData] = field(default_factory=dict)
    combined_point_cloud: Optional[CombinedPointCloud] = None

class V2VNetwork:
    def __init__(self):
        self.vehicle_states: Dict[int, VehicleState] = {}
    
    def update_vehicle_state(self, vehicle_id: int, state: VehicleState):
        self.vehicle_states[vehicle_id] = state
    
    def get_all_vehicle_states(self) -> Dict[int, VehicleState]:
        return self.vehicle_states
