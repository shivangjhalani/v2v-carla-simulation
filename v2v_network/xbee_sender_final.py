from digi.xbee.devices import XBeeDevice
import json
import time
import os

def read_state_log(filepath):
    """
    Read the state log JSON file and return all data entries.
    
    Args:
        filepath (str): Path to the state_log.json file
        
    Returns:
        list: The parsed JSON data array or None if there's an error
    """
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"Error: File not found at {filepath}")
            return None
            
        # Read and parse JSON file
        with open(filepath, 'r') as file:
            data_array = json.load(file)
            
        # Verify that we have an array of data
        if not isinstance(data_array, list):
            print("Error: Expected an array of state log entries")
            return None
            
        if not data_array:
            print("Error: State log array is empty")
            return None
            
        # Validate each entry in the array
        valid_entries = []
        for entry in data_array:
            if 'timestamp' in entry and 'own_data' in entry:
                valid_entries.append(entry)
            else:
                print(f"Warning: Skipping invalid entry (missing required fields)")
                
        if not valid_entries:
            print("Error: No valid entries found in state log")
            return None
            
        print(f"Found {len(valid_entries)} valid entries")
        return valid_entries
        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        print(f"Error reading state log: {e}")
        print(f"Error type: {type(e)}")
        return None

def get_value_from_path(data_dict, path):
    """Retrieve the value from the nested dictionary using the path."""
    try:
        current = data_dict
        for key in path:
            if isinstance(key, (str, int)) and str(key) in str(current):
                current = current[str(key)]
            else:
                return None
        return current
    except (KeyError, TypeError):
        return None

def send_with_retries(device, packet_str, retries=3, delay=0.5):
    """Send data with retry logic."""
    for attempt in range(retries):
        try:
            device.send_data_broadcast(packet_str)
            print(f"Sent: {packet_str}")
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    print(f"Failed to send after {retries} attempts: {packet_str}")
    return False

def process_entry(device, data, entry_num):
    """Process a single state log entry."""
    print(f"\nProcessing entry {entry_num} with timestamp: {data['timestamp']}")
    
    # Process all sequences for this entry
    for seq_num, path in SEQUENCE_MAP.items():
        value = get_value_from_path(data, path)
        if value is None:
            print(f"Warning: No data found for sequence {seq_num}, path: {path}")
            continue

        # Create a packet with sequence number and value
        packet = {"s": seq_num, "v": value}

        # Convert packet to JSON string
        packet_str = json.dumps(packet)

        # Send the data with retries
        success = send_with_retries(device, packet_str)
        if not success:
            print(f"Failed to send sequence {seq_num}.")

        # Delay between packets
        time.sleep(0.5)

def main():
    # Read data from state_log.json
    state_log_path = "state_log.json"  # Update this path as needed
    data_array = read_state_log(state_log_path)
    
    if data_array is None:
        print("Failed to read state log data. Exiting.")
        return

    # Initialize the XBee device
    device = XBeeDevice(PORT, BAUD_RATE)
    try:
        print("Opening connection to XBee...")
        device.open()
        print("Connection to XBee successful.")

        # Process each entry in the array
        for i, entry in enumerate(data_array, 1):
            process_entry(device, entry, i)
            print(f"Completed processing entry {i}")
            time.sleep(1)  # Add delay between entries

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if device.is_open():
            device.close()
            print("Connection to XBee closed.")

# XBee Configuration
PORT = "COM6"  # Replace with the sender XBee's COM port
BAUD_RATE = 9600

# Extended sequence map to handle two vehicles
SEQUENCE_MAP = {
    # Vehicle 1 sequences (0-20)
    0: ["own_data", "vehicle_id"],
    1: ["own_data", "location", "x"],
    2: ["own_data", "location", "y"],
    3: ["own_data", "location", "z"],
    4: ["own_data", "rotation", "pitch"],
    5: ["own_data", "rotation", "yaw"],
    6: ["own_data", "rotation", "roll"],
    7: ["own_data", "velocity", "x"],
    8: ["own_data", "velocity", "y"],
    9: ["own_data", "velocity", "z"],
    10: ["own_data", "speed"],
    11: ["own_data", "sensors", "gnss", "altitude"],
    12: ["own_data", "sensors", "gnss", "latitude"],
    13: ["own_data", "sensors", "gnss", "longitude"],
    14: ["own_data", "sensors", "imu", "accelerometer", "x"],
    15: ["own_data", "sensors", "imu", "accelerometer", "y"],
    16: ["own_data", "sensors", "imu", "accelerometer", "z"],
    17: ["own_data", "sensors", "imu", "gyroscope", "x"],
    18: ["own_data", "sensors", "imu", "gyroscope", "y"],
    19: ["own_data", "sensors", "imu", "gyroscope", "z"],
    20: ["own_data", "sensors", "lidar", "num_points"],
    
    # Vehicle 2 sequences (100-120)
    100: ["other_vehicles", "2", "vehicle_id"],
    101: ["other_vehicles", "2", "location", "x"],
    102: ["other_vehicles", "2", "location", "y"],
    103: ["other_vehicles", "2", "location", "z"],
    104: ["other_vehicles", "2", "rotation", "pitch"],
    105: ["other_vehicles", "2", "rotation", "yaw"],
    106: ["other_vehicles", "2", "rotation", "roll"],
    107: ["other_vehicles", "2", "velocity", "x"],
    108: ["other_vehicles", "2", "velocity", "y"],
    109: ["other_vehicles", "2", "velocity", "z"],
    110: ["other_vehicles", "2", "speed"],
    111: ["other_vehicles", "2", "sensors", "gnss", "altitude"],
    112: ["other_vehicles", "2", "sensors", "gnss", "latitude"],
    113: ["other_vehicles", "2", "sensors", "gnss", "longitude"],
    114: ["other_vehicles", "2", "sensors", "imu", "accelerometer", "x"],
    115: ["other_vehicles", "2", "sensors", "imu", "accelerometer", "y"],
    116: ["other_vehicles", "2", "sensors", "imu", "accelerometer", "z"],
    117: ["other_vehicles", "2", "sensors", "imu", "gyroscope", "x"],
    118: ["other_vehicles", "2", "sensors", "imu", "gyroscope", "y"],
    119: ["other_vehicles", "2", "sensors", "imu", "gyroscope", "z"],
    120: ["other_vehicles", "2", "sensors", "lidar", "num_points"]
}

if __name__ == "__main__":
    main()