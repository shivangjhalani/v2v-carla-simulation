from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QFrame)
from PySide6.QtCore import Qt
from .lidar_view import LidarView
from .vehicle_info_widget import VehicleInfoWidget
from .styles import apply_styles
from ..data_structures import VehicleState

class DashboardWindow(QMainWindow):
    def __init__(self, vehicle_id: int, on_close_callback=None):
        super().__init__()
        self.vehicle_id = vehicle_id
        self.on_close_callback = on_close_callback
        self.setWindowTitle(f"Vehicle {vehicle_id} Dashboard")
        self.setup_ui()
        apply_styles(self)
        
    def setup_ui(self):
        """Setup the dashboard UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QHBoxLayout(central_widget)
        
        # Left panel with vehicle info
        self.vehicle_info = VehicleInfoWidget()
        layout.addWidget(self.vehicle_info)
        
        # Right panel with lidar view
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Lidar view
        self.lidar_view = LidarView()
        right_layout.addWidget(self.lidar_view)
        
        layout.addWidget(right_panel)
        layout.setStretch(0, 1)  # Vehicle info takes 1 part
        layout.setStretch(1, 3)  # Lidar view takes 3 parts
        
        self.setMinimumSize(1200, 800)
    
    def update_state(self, state: VehicleState):
        """Update dashboard with new vehicle state"""
        self.vehicle_info.update_state(state)
        self.lidar_view.update_state(state)
    
    def cleanup(self):
        """Cleanup dashboard resources"""
        if hasattr(self, 'lidar_view'):
            self.lidar_view.cleanup()
        if hasattr(self, 'vehicle_info'):
            self.vehicle_info.cleanup()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.on_close_callback:
            self.on_close_callback(self.vehicle_id)
        self.cleanup()
        super().closeEvent(event)
