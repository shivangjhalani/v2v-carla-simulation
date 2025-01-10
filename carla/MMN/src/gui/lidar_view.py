from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF
import numpy as np
from ..data_structures import VehicleState, PointCloudData

class LidarView(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 600)
        self.state = None
        self.scale = 10  # pixels per meter
        self.center_offset = (300, 300)  # center point offset
        self._painter = None
        
    def cleanup(self):
        """Cleanup resources before destruction"""
        if hasattr(self, '_painter') and self._painter and self._painter.isActive():
            self._painter.end()
            self._painter = None
        self.state = None
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self.cleanup()
        super().closeEvent(event)
    
    def update_state(self, state: VehicleState):
        """Update view with new vehicle state"""
        self.state = state
        self.update()
    
    def paintEvent(self, event):
        if not self.state:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(40, 40, 40))
        
        # Draw grid
        self.draw_grid(painter)
        
        # Draw own vehicle's point cloud
        if self.state.point_cloud_cache and 'lidar' in self.state.point_cloud_cache:
            self.draw_point_cloud(painter, self.state.point_cloud_cache['lidar'], QColor(0, 255, 0, 100))
        
        # Draw other vehicles' point clouds
        if self.state.other_vehicles:
            for other in self.state.other_vehicles.values():
                if hasattr(other, 'point_cloud_cache') and other.point_cloud_cache and 'lidar' in other.point_cloud_cache:
                    transformed_cloud = self.transform_point_cloud(
                        other.point_cloud_cache['lidar'],
                        other.location,
                        other.rotation,
                        self.state.location,
                        self.state.rotation
                    )
                    # Draw with different color for each vehicle
                    color = self.get_vehicle_color(other.vehicle_id)
                    self.draw_point_cloud(painter, transformed_cloud, color)
        
        # Draw vehicles
        self.draw_vehicles(painter)
        
        painter.end()
    
    def draw_grid(self, painter):
        """Draw coordinate grid"""
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        
        # Draw grid lines
        for i in range(-30, 31, 5):
            # Vertical lines
            x = self.center_offset[0] + i * self.scale
            painter.drawLine(x, 0, x, self.height())
            
            # Horizontal lines
            y = self.center_offset[1] + i * self.scale
            painter.drawLine(0, y, self.width(), y)
    
    def draw_point_cloud(self, painter, point_cloud, color):
        """Draw lidar point cloud with batch rendering"""
        if point_cloud is None or not hasattr(point_cloud, 'points') or len(point_cloud.points) == 0:
            return
            
        points = point_cloud.points
        screen_points = np.zeros((len(points), 2), dtype=np.float32)
        
        # Vectorized transformation
        screen_points[:, 0] = self.center_offset[0] + points[:, 0] * self.scale
        screen_points[:, 1] = self.center_offset[1] - points[:, 1] * self.scale
        
        # Set pen once
        painter.setPen(QPen(color, 2))
        
        # Draw points in batches using QPointF array
        BATCH_SIZE = 1000
        for i in range(0, len(screen_points), BATCH_SIZE):
            batch = screen_points[i:i + BATCH_SIZE]
            points_array = [QPointF(float(x), float(y)) for x, y in batch]
            painter.drawPoints(points_array)
    
    def draw_vehicles(self, painter):
        """Draw vehicle positions"""
        if not self.state:
            return
        
        # Draw own vehicle at center
        self.draw_vehicle(painter, self.state, QColor(0, 255, 0))
        
        # Draw other vehicles with distance-based colors
        if self.state.other_vehicles:
            for other in self.state.other_vehicles.values():
                # Calculate relative position to ego vehicle
                dx = other.location[0] - self.state.location[0]
                dy = other.location[1] - self.state.location[1]
                
                # Transform relative coordinates
                rel_x = dx * np.cos(-np.radians(self.state.rotation[1])) - \
                       dy * np.sin(-np.radians(self.state.rotation[1]))
                rel_y = dx * np.sin(-np.radians(self.state.rotation[1])) + \
                       dy * np.cos(-np.radians(self.state.rotation[1]))
                
                # Calculate distance for coloring
                distance = np.sqrt(rel_x*rel_x + rel_y*rel_y)
                
                # Create transformed state for drawing
                transformed_state = VehicleState(
                    vehicle_id=other.vehicle_id,
                    timestamp=other.timestamp,
                    location=(rel_x, rel_y, other.location[2]),
                    rotation=(
                        other.rotation[0],
                        other.rotation[1] - self.state.rotation[1],  # Relative yaw
                        other.rotation[2]
                    ),
                    velocity=other.velocity,
                    speed=other.speed,
                    sensor_data={},
                    other_vehicles={},
                    transform_matrix=np.eye(4)
                )
                
                # Color gradient based on distance
                if distance < 10:
                    color = QColor(255, 100, 0)  # Red-orange
                elif distance < 30:
                    color = QColor(255, 165, 0)  # Orange
                else:
                    color = QColor(255, 255, 0)  # Yellow
                    
                self.draw_vehicle(painter, transformed_state, color)
    
    def draw_vehicle(self, painter, vehicle_state, color):
        """Draw single vehicle with direction indicator and info"""
        x, y = vehicle_state.location[:2]
        yaw = vehicle_state.rotation[1]  # Get yaw angle
        
        # Transform to screen coordinates (flip y-axis)
        screen_x = self.center_offset[0] + x * self.scale
        screen_y = self.center_offset[1] - y * self.scale  # Flip y-axis
        
        # Draw vehicle circle
        painter.setPen(QPen(color, 2))
        painter.setBrush(color)
        painter.drawEllipse(QPointF(screen_x, screen_y), 5, 5)
        
        # Draw direction indicator
        direction_length = 15
        rad = np.radians(yaw)
        end_x = screen_x + direction_length * np.cos(rad)
        end_y = screen_y - direction_length * np.sin(rad)  # Flip y-axis for direction
        painter.drawLine(int(screen_x), int(screen_y), 
                        int(end_x), int(end_y))
        
        # Draw vehicle info
        painter.setPen(QPen(color, 1))
        text = f"V{vehicle_state.vehicle_id}\n{vehicle_state.speed:.1f} km/h"
        painter.drawText(screen_x + 10, screen_y - 10, text)
    
    def transform_point_cloud(self, point_cloud, source_loc, source_rot, ego_loc, ego_rot):
        """Transform point cloud from source vehicle frame to ego vehicle frame"""
        # Convert to numpy arrays
        points = np.array(point_cloud.points)
        
        # Translate to world coordinates
        cos_yaw = np.cos(np.radians(source_rot[1]))
        sin_yaw = np.sin(np.radians(source_rot[1]))
        
        # Rotate points to world frame
        world_points = np.zeros_like(points)
        world_points[:, 0] = points[:, 0] * cos_yaw - points[:, 1] * sin_yaw
        world_points[:, 1] = points[:, 0] * sin_yaw + points[:, 1] * cos_yaw
        world_points[:, 2] = points[:, 2]
        
        # Translate to world position
        world_points[:, 0] += source_loc[0]
        world_points[:, 1] += source_loc[1]
        world_points[:, 2] += source_loc[2]
        
        # Transform to ego vehicle frame
        rel_x = world_points[:, 0] - ego_loc[0]
        rel_y = world_points[:, 1] - ego_loc[1]
        rel_z = world_points[:, 2] - ego_loc[2]
        
        # Rotate to ego vehicle frame
        ego_yaw = np.radians(ego_rot[1])
        cos_ego = np.cos(-ego_yaw)
        sin_ego = np.sin(-ego_yaw)
        
        transformed_points = np.zeros_like(points)
        transformed_points[:, 0] = rel_x * cos_ego - rel_y * sin_ego
        transformed_points[:, 1] = rel_x * sin_ego + rel_y * cos_ego
        transformed_points[:, 2] = rel_z
        
        return PointCloudData(
            points=transformed_points,
            timestamps=point_cloud.timestamps,
            tags=point_cloud.tags,
            source_vehicle=point_cloud.source_vehicle
        )
    
    def get_vehicle_color(self, vehicle_id):
        """Get unique color for each vehicle's point cloud"""
        colors = [
            QColor(255, 100, 0, 100),  # Orange
            QColor(100, 100, 255, 100),  # Blue
            QColor(255, 255, 0, 100),  # Yellow
            QColor(255, 0, 255, 100),  # Magenta
            QColor(0, 255, 255, 100),  # Cyan
        ]
        return colors[vehicle_id % len(colors)]