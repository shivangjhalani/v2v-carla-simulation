from typing import Dict, List, Optional
import numpy as np
import numpy.typing as npt
from ..data_structures import VehicleState, PointCloudData, CombinedPointCloud
from datetime import datetime, timedelta
import logging
import time

class PointCloudMerger:
    def __init__(self, max_point_age: float = 1.0):
        self.max_point_age = max_point_age
        self._transform_cache = {}
        self._buffer_cache = {}
        
    def merge_point_clouds(self, own_state: VehicleState, 
                         other_vehicles: Dict[int, VehicleState]) -> CombinedPointCloud:
        """Merge point clouds with GPU-optimized batch processing"""
        current_time = time.time()
        
        # Pre-calculate total points for single allocation
        total_points = 0
        if own_state.point_cloud_cache.get('semantic_lidar'):
            total_points += len(own_state.point_cloud_cache['semantic_lidar'].points)
        
        for other_state in other_vehicles.values():
            if other_state.point_cloud_cache.get('semantic_lidar'):
                total_points += len(other_state.point_cloud_cache['semantic_lidar'].points)
        
        if total_points == 0:
            return None
            
        # Get or create pre-allocated buffers
        if total_points not in self._buffer_cache:
            self._buffer_cache[total_points] = {
                'points': np.zeros((total_points, 3), dtype=np.float32),
                'timestamps': np.zeros(total_points, dtype=np.float32),
                'sources': np.zeros(total_points, dtype=np.int32),
                'tags': np.zeros(total_points, dtype=np.int32)
            }
            
            # Clear cache if too large
            if len(self._buffer_cache) > 10:
                smallest_key = min(self._buffer_cache.keys())
                del self._buffer_cache[smallest_key]
        
        buffers = self._buffer_cache[total_points]
        current_idx = 0
        
        # Process own vehicle's point cloud
        own_cloud = self._transform_vehicle_points(own_state)
        if own_cloud is not None:
            points_count = len(own_cloud.points)
            end_idx = current_idx + points_count
            
            # Use vectorized operations
            np.copyto(buffers['points'][current_idx:end_idx], own_cloud.points)
            np.copyto(buffers['timestamps'][current_idx:end_idx], own_cloud.timestamps)
            buffers['sources'][current_idx:end_idx] = own_state.vehicle_id
            
            if own_cloud.tags is not None:
                np.copyto(buffers['tags'][current_idx:end_idx], own_cloud.tags)
                
            current_idx = end_idx
        
        # Process other vehicles' point clouds in batch
        for other_state in other_vehicles.values():
            other_cloud = self._transform_vehicle_points(other_state)
            if other_cloud is not None:
                points_count = len(other_cloud.points)
                end_idx = current_idx + points_count
                
                # Use vectorized operations
                np.copyto(buffers['points'][current_idx:end_idx], other_cloud.points)
                np.copyto(buffers['timestamps'][current_idx:end_idx], other_cloud.timestamps)
                buffers['sources'][current_idx:end_idx] = other_state.vehicle_id
                
                if other_cloud.tags is not None:
                    np.copyto(buffers['tags'][current_idx:end_idx], other_cloud.tags)
                    
                current_idx = end_idx
        
        # Remove old points using vectorized operations
        age_mask = current_time - buffers['timestamps'][:current_idx] <= self.max_point_age
        valid_points = current_idx
        current_idx = np.sum(age_mask)
        
        if current_idx == 0:
            return None
            
        return CombinedPointCloud(
            points=buffers['points'][:current_idx],
            timestamps=buffers['timestamps'][:current_idx],
            tags=buffers['tags'][:current_idx],
            sources=buffers['sources'][:current_idx],
            last_update=datetime.now()
        )

    def _transform_vehicle_points(self, vehicle_state: VehicleState) -> Optional[PointCloudData]:
        """Transform point cloud with pre-allocated buffers"""
        try:
            if 'semantic_lidar' not in vehicle_state.point_cloud_cache:
                return None
            
            cloud = vehicle_state.point_cloud_cache['semantic_lidar']
            if cloud is None or len(cloud.points) == 0:
                return None
            
            # Use class-level pre-allocated buffers
            if not hasattr(self, '_points_buffer'):
                self._points_buffer = {}
                self._transformed_buffer = {}
            
            points_count = len(cloud.points)
            buffer_key = points_count
            
            # Create or reuse buffers
            if buffer_key not in self._points_buffer:
                self._points_buffer[buffer_key] = np.zeros((points_count, 4), dtype=np.float32)
                self._transformed_buffer[buffer_key] = np.zeros((points_count, 3), dtype=np.float32)
            
            # Reuse existing buffer
            homogeneous_points = self._points_buffer[buffer_key]
            transformed_points = self._transformed_buffer[buffer_key]
            
            # Copy points to buffer without allocation
            homogeneous_points[:, :3] = cloud.points
            homogeneous_points[:, 3] = 1
            
            # In-place transformation
            np.dot(homogeneous_points, vehicle_state.transform_matrix.T, out=transformed_points)
            
            return PointCloudData(
                points=transformed_points[:, :3],  # View, not copy
                timestamps=cloud.timestamps,
                tags=cloud.tags,
                source_vehicle=vehicle_state.vehicle_id
            )
            
        except Exception as e:
            logging.error(f"Error transforming points: {e}")
            return None

    def _process_point_cloud(self, vehicle_id: int, timestamp: str, sensor_type: str, data) -> Optional[PointCloudData]:
        """Process point cloud data using vectorized operations and memory pre-allocation"""
        point_size = 16 if sensor_type == 'semantic_lidar' else 12
        raw_data = bytes(data.raw_data)
        total_points = len(raw_data) // point_size
        
        if total_points == 0:
            return None
        
        # Pre-allocate numpy arrays for better memory efficiency
        points = np.empty((total_points, 3), dtype=np.float32)
        timestamps = np.full(total_points, time.time(), dtype=np.float32)
        tags = np.empty(total_points, dtype=np.int32) if sensor_type == 'semantic_lidar' else None
        
        # Use numpy's frombuffer for faster data conversion
        data_array = np.frombuffer(raw_data, dtype=np.float32).reshape(total_points, -1)
        points[:] = data_array[:, :3]
        
        if sensor_type == 'semantic_lidar':
            tags[:] = data_array[:, 3].astype(np.int32)
        
        return PointCloudData(
            points=points,
            timestamps=timestamps,
            tags=tags,
            source_vehicle=vehicle_id
        ) 