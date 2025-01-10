import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtMultimedia import QSoundEffect
from .gui.dashboard_window import DashboardWindow
from .data_structures import VehicleState, V2VNetwork, PointCloudData
from typing import Dict, Optional
import logging
import signal
from datetime import datetime
import numpy as np

class DashboardApplication:
    def __init__(self, simulation_manager=None):
        logging.basicConfig(level=logging.INFO)
        self.app = QApplication(sys.argv)
        self.dashboards: Dict[int, DashboardWindow] = {}
        self.closed_dashboard_ids = set()  # Track closed dashboard IDs
        self.v2v_network = V2VNetwork()
        self.simulation_manager = simulation_manager
        
        # Initialize collision sound
        self.collision_sound = QSoundEffect()
        sound_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            'assets', 
            'collision_alert.wav'
        ))
        self.collision_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.collision_sound.setVolume(1.0)
        self.collision_played = set()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboards)
        self.update_timer.start(100)  # 10 Hz update rate
        
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Only create test data if no simulation manager is provided
        if not simulation_manager:
            self._create_test_data()
    
    def _create_test_data(self):
        """Create test vehicle states for development"""
        # Create point cloud data
        points = np.random.rand(1000, 3) * 20 - 10  # Random points in [-10, 10]
        point_cloud = PointCloudData(
            points=points,
            timestamps=np.ones(1000) * datetime.now().timestamp(),
            tags=None,
            source_vehicle=1
        )
        
        # Create test vehicle states
        test_states = {
            1: VehicleState(
                vehicle_id=1,
                timestamp=datetime.now(),
                location=(0.0, 0.0, 0.0),
                rotation=(0.0, 0.0, 0.0),
                velocity=(5.0, 0.0, 0.0),
                speed=18.0,
                sensor_data={'lidar': point_cloud},
                other_vehicles={},
                transform_matrix=np.eye(4),
                point_cloud_cache={'lidar': point_cloud}
            ),
            2: VehicleState(
                vehicle_id=2,
                timestamp=datetime.now(),
                location=(20.0, 20.0, 0.0),
                rotation=(0.0, 45.0, 0.0),
                velocity=(-3.0, 4.0, 0.0),
                speed=25.0,
                sensor_data={'lidar': point_cloud},
                other_vehicles={},
                transform_matrix=np.eye(4),
                point_cloud_cache={'lidar': point_cloud}
            )
        }
        
        # Update other_vehicles field
        for vid, state in test_states.items():
            other_vehicles = {
                other_id: other_state 
                for other_id, other_state in test_states.items() 
                if other_id != vid
            }
            state.other_vehicles = other_vehicles
            self.v2v_network.update_vehicle_state(vid, state)
    
    def update_dashboards(self):
        """Update dashboards with batch processing and caching"""
        try:
            # Cache vehicle states to avoid repeated lookups
            vehicle_states = {}
            
            if self.simulation_manager:
                vehicle_states = self.simulation_manager._update_vehicle_states()
                if vehicle_states:
                    for vehicle_id, state in vehicle_states.items():
                        self.v2v_network.update_vehicle_state(vehicle_id, state)
            
            all_states = vehicle_states or self.v2v_network.get_all_vehicle_states()
            
            if all_states:
                # Only create dashboards for vehicles that haven't been closed
                new_dashboards = {
                    vid: DashboardWindow(vid, self.on_dashboard_closed)
                    for vid in all_states
                    if vid not in self.dashboards and vid not in self.closed_dashboard_ids
                }
                
                # Show new dashboards
                for dashboard in new_dashboards.values():
                    dashboard.show()
                
                # Update dashboard dictionary
                self.dashboards.update(new_dashboards)
                
                # Update existing dashboards
                for vehicle_id, dashboard in self.dashboards.items():
                    if vehicle_id in all_states:
                        dashboard.update_state(all_states[vehicle_id])
                    
        except Exception as e:
            logging.error(f"Error updating dashboards: {e}")
    
    def create_dashboards(self, vehicle_states: Dict[int, VehicleState]):
        """Create a dashboard for each vehicle"""
        for vehicle_id, state in vehicle_states.items():
            if vehicle_id not in self.dashboards:
                logging.info(f"Creating dashboard for vehicle {vehicle_id}")
                dashboard = DashboardWindow(vehicle_id, self.on_dashboard_closed)
                dashboard.show()
                self.dashboards[vehicle_id] = dashboard
    
    def on_dashboard_closed(self, vehicle_id: int):
        """Handle dashboard window closure"""
        logging.info(f"Dashboard for vehicle {vehicle_id} closed")
        
        # Add to closed dashboards set
        self.closed_dashboard_ids.add(vehicle_id)
        
        # Remove from dashboards dict
        if vehicle_id in self.dashboards:
            del self.dashboards[vehicle_id]
            
        # Notify simulation manager to clean up vehicle processing
        if self.simulation_manager:
            if self.simulation_manager.following_vehicle_id == vehicle_id:
                self.simulation_manager.following_vehicle_id = None
                
            if (hasattr(self.simulation_manager, 'vehicle_controller') and 
                self.simulation_manager.vehicle_controller.controlled_vehicle and
                self.simulation_manager.vehicle_controller.controlled_vehicle.id == vehicle_id):
                self.simulation_manager.vehicle_controller.controlled_vehicle = None
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        logging.info("Shutting down dashboard application...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup resources"""
        logging.info("Cleaning up resources...")
        try:
            # Use a flag to prevent double cleanup
            if hasattr(self, '_cleanup_done') and self._cleanup_done:
                return
            
            # Stop update timer first
            if hasattr(self, 'update_timer'):
                try:
                    if self.update_timer.isActive():
                        self.update_timer.stop()
                        self.update_timer.timeout.disconnect(self.update_dashboards)
                except (RuntimeError, TypeError) as e:
                    logging.warning(f"Timer disconnect warning: {e}")
            
            # Process any pending events
            if hasattr(self, 'app'):
                self.app.processEvents()
            
            # Cleanup dashboards
            if hasattr(self, 'dashboards'):
                for dashboard in self.dashboards.values():
                    if dashboard is not None:
                        dashboard.cleanup()
                        dashboard.close()
                self.dashboards.clear()
            
            # Process events one final time and quit
            if hasattr(self, 'app'):
                self.app.processEvents()
                self.app.quit()
            
            self._cleanup_done = True
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
        finally:
            logging.info("Cleanup completed")
    
    def run(self):
        """Run the dashboard application"""
        try:
            logging.info("Starting dashboard application...")
            return self.app.exec()
        except Exception as e:
            logging.error(f"Error running dashboard application: {e}")
            return 1
        finally:
            self.cleanup()

def main():
    app = DashboardApplication()
    sys.exit(app.run())

if __name__ == "__main__":
    main()
