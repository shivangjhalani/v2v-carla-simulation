from digi.xbee.devices import XBeeDevice
import json
from typing import Dict, List, Any, Optional
import time
import threading
from queue import Queue

# XBee Configuration
PORT = "COM3"
BAUD_RATE = 9600

# Complete sequence map (make sure this matches exactly with the sender's map)
SEQUENCE_MAP = {
    0: ["vehicle_id"],
    1: ["location", "x"],
    2: ["location", "y"],
    3: ["location", "z"],
    4: ["rotation", "pitch"],
    5: ["rotation", "yaw"],
    6: ["rotation", "roll"],
    7: ["velocity", "x"],
    8: ["velocity", "y"],
    9: ["velocity", "z"],
    10: ["speed"],
    11: ["sensors", "gnss", "altitude"],
    12: ["sensors", "gnss", "latitude"],
    13: ["sensors", "gnss", "longitude"],
    14: ["sensors", "imu", "accelerometer", "x"],
    15: ["sensors", "imu", "accelerometer", "y"],
    16: ["sensors", "imu", "accelerometer", "z"],
    17: ["sensors", "imu", "gyroscope", "x"],
    18: ["sensors", "imu", "gyroscope", "y"],
    19: ["sensors", "imu", "gyroscope", "z"],
    20: ["sensors", "lidar", "num_points"]
}

class XBeeReceiver:
    def __init__(self, port: str, baud_rate: int):
        self.port = port
        self.baud_rate = baud_rate
        self.device = XBeeDevice(port, baud_rate)
        self.data_queue: Queue = Queue()
        self.reconstructed_data: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.received_sequences: set = set()
        self.last_received_time = time.time()
        self.is_running = True

    def create_nested_dict(self, path: List[str], value: Any) -> Dict[str, Any]:
        """Create nested dictionary from path and value."""
        result = {}
        current = result
        for part in path[:-1]:
            current[part] = {}
            current = current[part]
        current[path[-1]] = value
        return result

    def merge_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two nested dictionaries."""
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                dict1[key] = self.merge_dicts(dict1[key], value)
            else:
                dict1[key] = value
        return dict1

    def data_receive_callback(self, xbee_message):
        """Process received XBee message."""
        try:
            payload = xbee_message.data.decode()
            self.data_queue.put(payload)
            self.last_received_time = time.time()
        except Exception as e:
            print(f"Error receiving message: {e}")

    def reset_state(self):
        """Reset the receiver state for new data."""
        with self.lock:
            self.reconstructed_data.clear()
            self.received_sequences.clear()

    def process_data(self):
        """Process data from queue with improved error handling."""
        while self.is_running:
            try:
                # Reset state if we haven't received data for a while
                if time.time() - self.last_received_time > 5.0:
                    self.reset_state()

                if not self.data_queue.empty():
                    payload = self.data_queue.get()
                    packet = json.loads(payload)
                    
                    seq_num = packet.get("s")
                    value = packet.get("v")
                    
                    # Validate sequence number
                    if seq_num not in SEQUENCE_MAP:
                        print(f"Warning: Received unknown sequence number: {seq_num}")
                        continue
                    
                    path = SEQUENCE_MAP[seq_num]
                    print(f"Received Packet: Sequence {seq_num}, Path: {path}, Value: {value}")
                    
                    # Mark sequence as received
                    self.received_sequences.add(seq_num)
                    
                    # Update reconstructed data
                    nested_data = self.create_nested_dict(path, value)
                    with self.lock:
                        self.reconstructed_data = self.merge_dicts(
                            self.reconstructed_data, nested_data
                        )
                    
                    # Check if we have all sequences
                    if len(self.received_sequences) == len(SEQUENCE_MAP):
                        print("\nComplete Data Set Received:")
                        print(json.dumps(self.reconstructed_data, indent=2))
                        print(f"\nTotal sequences received: {len(self.received_sequences)}")
                        # Reset for next set of data
                        self.reset_state()
                
                time.sleep(0.1)  # Prevent CPU overuse
            
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
            except Exception as e:
                print(f"Error processing data: {e}")

    def start(self):
        """Start the receiver with improved error handling."""
        try:
            print(f"Opening connection to XBee on port {self.port}...")
            self.device.open()
            self.device.add_data_received_callback(self.data_receive_callback)
            
            # Start processing thread
            processing_thread = threading.Thread(target=self.process_data, daemon=True)
            processing_thread.start()
            
            print("Receiving data. Press Ctrl+C to exit.")
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
            self.is_running = False
            processing_thread.join(timeout=2.0)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.device.is_open():
                self.device.close()
            print("Connection closed.")

def main():
    receiver = XBeeReceiver(PORT, BAUD_RATE)
    receiver.start()

if __name__ == "__main__":
    main()