from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                             QGridLayout, QFrame)
from PySide6.QtCore import Qt, QTimer
from ..data_structures import VehicleState
import numpy as np

class VehicleInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.labels = {}
        self.collision_timers = {}  # Store timers for each vehicle's collision
        self.setup_ui()
        
        # Add collision alert label
        self.collision_alert = QLabel("")
        self.collision_alert.setStyleSheet("color: red; font-weight: bold;")
        self.layout().addWidget(self.collision_alert)
        
    def setup_ui(self):
        """Setup the vehicle info UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Vehicle Information")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Info grid
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)
        info_layout = QGridLayout(info_frame)
        
        # Create labels
        self.labels = {
            'vehicle_id': self.create_info_label("Vehicle ID"),
            'speed': self.create_info_label("Speed (km/h)"),
            'location': self.create_info_label("Location (x, y, z)"),
            'rotation': self.create_info_label("Rotation (p, y, r)"),
            'other_vehicles': self.create_info_label("Other Vehicles"),
            'nearest_vehicle': self.create_info_label("Nearest Vehicle")
        }
        
        # Add labels to grid
        row = 0
        for key, (label, value) in self.labels.items():
            info_layout.addWidget(label, row, 0)
            info_layout.addWidget(value, row, 1)
            row += 1
        
        layout.addWidget(info_frame)
        layout.addStretch()
    
    def create_info_label(self, text):
        """Create a pair of labels for info display"""
        label = QLabel(f"{text}:")
        value = QLabel("-")
        label.setStyleSheet("font-weight: bold;")
        return label, value
    
    def cleanup(self):
        """Cleanup resources"""
        for timer in self.collision_timers.values():
            timer.stop()
        self.collision_timers.clear()
    
    def update_state(self, state: VehicleState):
        """Update info display with new state"""
        # Update basic vehicle info
        self.update_basic_info(state)
        
        # Check for collisions in other vehicles
        current_collisions = set()
        collision_alerts = []
        
        for other in state.other_vehicles.values():
            if 'collision' in other.sensor_data and other.sensor_data['collision']:
                vehicle_id = other.vehicle_id
                current_collisions.add(vehicle_id)
                
                # Only add alert for new collisions
                if vehicle_id not in self.collision_timers:
                    dx = other.location[0] - state.location[0]
                    dy = other.location[1] - state.location[1]
                    distance = np.sqrt(dx*dx + dy*dy)
                    collision_alerts.append(f"Vehicle {vehicle_id} collision at {distance:.1f}m!")
                    
                    # Start timer for this collision
                    timer = QTimer(self)
                    timer.setSingleShot(True)
                    timer.timeout.connect(lambda vid=vehicle_id: self.clear_collision(vid))
                    timer.start(2000)  # 2 seconds
                    self.collision_timers[vehicle_id] = timer
        
        # Update collision alert text only for new collisions
        if collision_alerts:
            self.collision_alert.setText("\n".join(collision_alerts))
    
    def clear_collision(self, vehicle_id):
        """Clear collision alert for a vehicle"""
        if vehicle_id in self.collision_timers:
            self.collision_timers[vehicle_id].stop()
            del self.collision_timers[vehicle_id]
            # Clear the collision alert text
            self.collision_alert.setText("")
    
    def update_basic_info(self, state: VehicleState):
        """Update basic vehicle information display"""
        # Update vehicle info labels
        self.labels['vehicle_id'][1].setText(str(state.vehicle_id))
        self.labels['speed'][1].setText(f"{state.speed:.1f}")
        self.labels['location'][1].setText(
            f"({state.location[0]:.1f}, {state.location[1]:.1f}, {state.location[2]:.1f})"
        )
        self.labels['rotation'][1].setText(
            f"({state.rotation[0]:.1f}, {state.rotation[1]:.1f}, {state.rotation[2]:.1f})"
        )
        
        # Update other vehicles info
        other_vehicles_count = len(state.other_vehicles)
        self.labels['other_vehicles'][1].setText(str(other_vehicles_count))
        
        # Find nearest vehicle
        if other_vehicles_count > 0:
            nearest_distance = float('inf')
            nearest_id = None
            for other in state.other_vehicles.values():
                dx = other.location[0] - state.location[0]
                dy = other.location[1] - state.location[1]
                distance = np.sqrt(dx*dx + dy*dy)
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_id = other.vehicle_id
            self.labels['nearest_vehicle'][1].setText(
                f"ID: {nearest_id} ({nearest_distance:.1f}m)"
            )
        else:
            self.labels['nearest_vehicle'][1].setText("None")
