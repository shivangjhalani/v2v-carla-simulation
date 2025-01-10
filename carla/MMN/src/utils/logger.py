from datetime import datetime
import json
import os
import numpy as np
from typing import Dict, Any, Optional
from ..data_structures import VehicleState, PointCloudData
import open3d as o3d
import logging
import time

class VehicleLogger:
    def __init__(self, config):
        self.config = config
        self.log_dir = config['logging']['output']['directory']
        self.timestamp_format = config['logging']['output']['timestamp_format']
        self.max_file_size = config['logging']['json']['max_file_size_mb'] * 1024 * 1024
        os.makedirs(self.log_dir, exist_ok=True)
        
    def log_vehicle_data(self, vehicle_id: int, own_state: VehicleState, 
                        other_vehicles_data: Dict[int, VehicleState]):
        """Log vehicle state data"""
        log_file = self._get_log_file(vehicle_id)
        timestamp = datetime.now().strftime(self.timestamp_format)
        
        log_entry = {
            "timestamp": timestamp,
            "own_data": {
                "vehicle_id": own_state.vehicle_id,
                "location": {
                    "x": float(own_state.location[0]),
                    "y": float(own_state.location[1]),
                    "z": float(own_state.location[2])
                },
                "rotation": {
                    "pitch": float(own_state.rotation[0]),
                    "yaw": float(own_state.rotation[1]),
                    "roll": float(own_state.rotation[2])
                },
                "velocity": {
                    "x": float(own_state.velocity[0]),
                    "y": float(own_state.velocity[1]),
                    "z": float(own_state.velocity[2])
                },
                "speed": float(own_state.speed),
                "sensors": self._process_sensor_data(vehicle_id, timestamp, own_state.sensor_data)
            },
            "other_vehicles": {
                str(other.vehicle_id): {
                    "location": {
                        "x": float(other.location[0]),
                        "y": float(other.location[1]),
                        "z": float(other.location[2])
                    },
                    "velocity": {
                        "x": float(other.velocity[0]),
                        "y": float(other.velocity[1]),
                        "z": float(other.velocity[2])
                    },
                    "speed": float(other.speed),
                    "relative_distance": float(np.linalg.norm(
                        np.array(own_state.location) - np.array(other.location)
                    )),
                    "sensors": self._process_sensor_data(other.vehicle_id, timestamp, other.sensor_data)
                }
                for other in other_vehicles_data.values()
            }
        }
        
        # Add combined point cloud data if available
        if own_state.combined_point_cloud:
            log_entry["own_data"]["combined_point_cloud"] = {
                "num_points": len(own_state.combined_point_cloud.points),
                "num_sources": len(np.unique(own_state.combined_point_cloud.sources)),
                "last_update": own_state.combined_point_cloud.last_update.strftime(self.timestamp_format)
            }
        
        self._write_log(log_file, log_entry)
        
    def _process_sensor_data(self, vehicle_id: int, timestamp: str, 
                           sensor_data: Dict[str, Any]) -> dict:
        """Process and save sensor data, returning processed data structure"""
        processed = {}
        
        for sensor_type, data in sensor_data.items():
            if sensor_type == 'collision':
                processed['collision'] = bool(data.other_actor is not None)
            elif sensor_type == 'gnss':
                processed['gnss'] = {
                    'altitude': float(data.altitude),
                    'latitude': float(data.latitude),
                    'longitude': float(data.longitude)
                }
            elif sensor_type == 'imu':
                processed['imu'] = {
                    'accelerometer': {
                        'x': float(data.accelerometer.x),
                        'y': float(data.accelerometer.y),
                        'z': float(data.accelerometer.z)
                    },
                    'gyroscope': {
                        'x': float(data.gyroscope.x),
                        'y': float(data.gyroscope.y),
                        'z': float(data.gyroscope.z)
                    }
                }
            elif sensor_type in ['lidar', 'radar', 'semantic_lidar']:
                point_cloud = self._process_point_cloud(vehicle_id, timestamp, sensor_type, data)
                if point_cloud:
                    processed[sensor_type] = {
                        'num_points': len(point_cloud.points),
                        'timestamp': float(data.timestamp)
                    }
        
        return processed

    def _process_point_cloud(self, vehicle_id: int, timestamp: str, 
                             sensor_type: str, data) -> Optional[PointCloudData]:
        """Process point cloud data into structured format"""
        points = []
        tags = [] if sensor_type == 'semantic_lidar' else None
        timestamps = []
        point_size = 16 if sensor_type == 'semantic_lidar' else 12
        
        raw_data = bytes(data.raw_data)
        total_points = len(raw_data) // point_size
        
        if total_points == 0:
            return None
        
        current_time = time.time()
        
        # Parse points based on sensor type
        for i in range(total_points):
            offset = i * point_size
            if sensor_type == 'semantic_lidar':
                point_data = np.frombuffer(raw_data[offset:offset + 16], dtype=np.float32)
                points.append(point_data[:3])
                tags.append(int(point_data[3]))
            else:
                points.append(np.frombuffer(raw_data[offset:offset + 12], dtype=np.float32))
            timestamps.append(current_time)
        
        return PointCloudData(
            points=np.array(points, dtype=np.float32),
            timestamps=np.array(timestamps, dtype=np.float32),
            tags=np.array(tags, dtype=np.int32) if tags else None,
            source_vehicle=vehicle_id
        )

    def _get_log_file(self, vehicle_id: int) -> str:
        """Get appropriate log file path"""
        vehicle_dir = os.path.join(self.log_dir, f"vehicle_{vehicle_id}")
        os.makedirs(vehicle_dir, exist_ok=True)
        return os.path.join(vehicle_dir, "state_log.json")

    def _write_log(self, log_file: str, log_entry: dict):
        """Write log entry to file"""
        try:
            # Check if file exists and its size
            if os.path.exists(log_file) and os.path.getsize(log_file) > self.max_file_size:
                # Create new file with timestamp
                timestamp = datetime.now().strftime(self.timestamp_format)
                base, ext = os.path.splitext(log_file)
                log_file = f"{base}_{timestamp}{ext}"
            
            if not os.path.exists(log_file):
                # Create new file with array start
                with open(log_file, 'w') as f:
                    f.write('[\n')
                    json.dump(log_entry, f, indent=2)
                    f.write('\n]')
            else:
                # Read existing content
                with open(log_file, 'r+') as f:
                    # Move cursor to just before the closing bracket
                    f.seek(0, 2)  # Go to end
                    f.seek(f.tell() - 2, 0)  # Move back 2 characters (before ']')
                    f.write(',\n')  # Add comma and newline
                    json.dump(log_entry, f, indent=2)  # Write new entry
                    f.write('\n]')  # Close the array
                
        except Exception as e:
            logging.error(f"Error writing to log file: {e}")

    def cleanup(self):
        """Cleanup method for the VehicleLogger"""
        try:
            # Close any open log files
            for vehicle_dir in os.listdir(self.log_dir):
                if vehicle_dir.startswith('vehicle_'):
                    log_file = os.path.join(self.log_dir, vehicle_dir, "state_log.json")
                    if os.path.exists(log_file):
                        with open(log_file, 'a') as f:
                            # Ensure JSON file is properly closed
                            if os.path.getsize(log_file) > 0:
                                f.seek(0, 2)  # Go to end of file
                                if f.tell() > 1:  # If file has content
                                    f.write('\n]')  # Close the JSON array
                                    
        except Exception as e:
            print(f"Error during logger cleanup: {e}") 