import carla
import keyboard
import logging

class VehicleController:
    def __init__(self, world, vehicle_manager, simulation_manager):
        self.world = world
        self.vehicle_manager = vehicle_manager
        self.simulation_manager = simulation_manager
        self.controlled_vehicle = None
        self.control = carla.VehicleControl()
        
    def handle_input(self, control_mode):
        """Handle keyboard input based on control mode"""
        try:
            # Handle ESC key
            if keyboard.is_pressed('esc'):
                if self.controlled_vehicle:
                    self.controlled_vehicle = None
                    self.simulation_manager.following_vehicle_id = None
                    return True
                    
            # Handle firetruck spawning with 'f' key when in spectator mode
            if keyboard.is_pressed('f') and self.controlled_vehicle is None:
                self._spawn_firetruck()
                return True
                
            # Handle vehicle selection (1-9 keys)
            for key in '123456789':
                if keyboard.is_pressed(key):
                    seq_id = int(key)
                    if seq_id in self.vehicle_manager.get_sequential_ids():
                        vehicle = self.vehicle_manager.get_vehicles()[seq_id - 1]
                        if vehicle:
                            if control_mode == "manual":
                                vehicle.set_autopilot(False)
                                self.controlled_vehicle = vehicle
                            else:  # autopilot mode
                                self.controlled_vehicle = vehicle
                            self.simulation_manager.following_vehicle_id = seq_id
                            
            if control_mode == "manual" and self.controlled_vehicle:
                self._handle_manual_control()
                
            return True
            
        except Exception as e:
            logging.error(f"Error handling input: {e}")
            return True
            
    def _handle_manual_control(self):
        # Reset control
        self.control.throttle = 0.0
        self.control.brake = 0.0
        self.control.steer = 0.0
        self.control.hand_brake = False
        
        # Handle controls
        if keyboard.is_pressed('w'):
            self.control.throttle = 1.0
        if keyboard.is_pressed('s'):
            self.control.brake = 1.0
        if keyboard.is_pressed('a'):
            self.control.steer = -1.0
        if keyboard.is_pressed('d'):
            self.control.steer = 1.0
        if keyboard.is_pressed('space'):
            self.control.hand_brake = True
        if keyboard.is_pressed('q'):
            self.control.reverse = not self.control.reverse
            
        # Apply control to vehicle
        self.controlled_vehicle.apply_control(self.control) 

    def _spawn_firetruck(self):
        """Spawn a firetruck at spectator location"""
        try:
            # Get spectator transform
            spectator = self.world.get_spectator()
            transform = spectator.get_transform()
            
            # Adjust height to ensure vehicle spawns on road
            transform.location.z -= 2  # Adjust height to be closer to road level
            
            # Create blueprint for firetruck
            blueprint_library = self.world.get_blueprint_library()
            firetruck_bp = blueprint_library.find('vehicle.carlamotors.firetruck')
            
            if firetruck_bp:
                # Spawn the firetruck
                firetruck = self.world.try_spawn_actor(firetruck_bp, transform)
                if firetruck:
                    logging.info("Firetruck spawned successfully")
                else:
                    logging.error("Failed to spawn firetruck - invalid position")
            else:
                logging.error("Firetruck blueprint not found")
                
        except Exception as e:
            logging.error(f"Error spawning firetruck: {e}") 