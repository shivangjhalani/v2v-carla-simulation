from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                             QGridLayout, QFrame)
from PySide6.QtCore import Qt
from ..data_structures import VehicleState
import numpy as np

class VehicleInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
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
    
    def update_state(self, state: VehicleState):
        """Update info display with new state"""
        labels = self.labels
        
        # Update basic values
        labels['vehicle_id'][1].setText(str(state.vehicle_id))
        labels['speed'][1].setText(f"{state.speed:.1f}")
        labels['location'][1].setText(
            f"({state.location[0]:.1f}, {state.location[1]:.1f}, {state.location[2]:.1f})"
        )
        labels['rotation'][1].setText(
            f"({state.rotation[0]:.1f}, {state.rotation[1]:.1f}, {state.rotation[2]:.1f})"
        )
        
        # Update other vehicles info
        num_others = len(state.other_vehicles)
        labels['other_vehicles'][1].setText(f"{num_others} vehicles")
        
        # Find nearest vehicle
        if state.other_vehicles:
            nearest_dist = float('inf')
            nearest_info = "None"
            
            for other in state.other_vehicles.values():
                dx = other.location[0] - state.location[0]
                dy = other.location[1] - state.location[1]
                dist = np.sqrt(dx*dx + dy*dy)
                
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_info = f"V{other.vehicle_id} at {nearest_dist:.1f}m"
            
            labels['nearest_vehicle'][1].setText(nearest_info)
        else:
            labels['nearest_vehicle'][1].setText("None")
