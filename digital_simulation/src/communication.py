from typing import Dict
from .data_structures import VehicleState

class Communication:
    def __init__(self):
        self.vehicle_states: Dict[int, VehicleState] = {}

    def broadcast_vehicle_state(self, state: VehicleState):
        """Store vehicle state for V2V communication"""
        self.vehicle_states[state.vehicle_id] = state

    def get_other_vehicle_states(self, vehicle_id: int) -> Dict[int, VehicleState]:
        """Get states of other vehicles for V2V communication"""
        return {
            vid: state for vid, state in self.vehicle_states.items()
            if vid != vehicle_id
        }