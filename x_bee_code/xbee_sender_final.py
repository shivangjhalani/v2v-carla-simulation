from digi.xbee.devices import XBeeDevice
import json
import time

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

def get_value_from_path(data_dict, path):
    """Retrieve the value from the nested dictionary using the path."""
    try:
        current = data_dict
        for key in path:
            current = current[key]
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

def main():
    # Sample data (same as before)
    data = {
        "timestamp": "20250109_223722",
        "own_data": {
            "vehicle_id": 1,
            "location": {
                "x": 99.38441467285156,
                "y": -6.305729389190674,
                "z": 0.5461000204086304
            },
            "rotation": {
                "pitch": 0.0,
                "yaw": 90.39070129394531,
                "roll": 0.0
            },
            "velocity": {
                "x": 0.0,
                "y": 0.0,
                "z": -0.9800000786781311
            },
            "speed": 3.5280002832412722,
            "sensors": {
                "gnss": {
                    "altitude": 1.0461000204086304,
                    "latitude": 0.5000566453308721,
                    "longitude": 0.500892785387039
                },
                "imu": {
                    "accelerometer": {
                        "x": -4.104411721902052e-37,
                        "y": -5.8386274916310485e-36,
                        "z": 9.8100004196167
                    },
                    "gyroscope": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    }
                },
                "lidar": {
                    "num_points": 7184,
                    "timestamp": 21628.751257743686
                }
            }
        },
        "other_vehicles": {
            "2": {
                "vehicle_id": 2,  # Added vehicle_id for vehicle 2
                "location": {
                    "x": -52.330810546875,
                    "y": -14.039613723754883,
                    "z": 0.5461000204086304
                },
                "rotation": {  # Added missing rotation data
                    "pitch": 0.0,
                    "yaw": 180.0,
                    "roll": 0.0
                },
                "velocity": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": -0.9800000786781311
                },
                "speed": 3.5280002832412722,
                "sensors": {
                    "gnss": {
                        "altitude": 1.0461000204086304,
                        "latitude": 0.5001261199959117,
                        "longitude": 0.4995299043305538
                    },
                    "imu": {
                        "accelerometer": {
                            "x": -8.019430669598591e-37,
                            "y": 3.081867955001272e-36,
                            "z": 9.8100004196167
                        },
                        "gyroscope": {
                            "x": 0.0,
                            "y": 0.0,
                            "z": 0.0
                        }
                    },
                    "lidar": {
                        "num_points": 7292,
                        "timestamp": 21628.751257743686
                    }
                }
            }
        }
    }

    # Initialize the XBee device
    device = XBeeDevice(PORT, BAUD_RATE)
    try:
        print("Opening connection to XBee...")
        device.open()
        print("Connection to XBee successful.")

        # Process all sequences
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

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if device.is_open():
            device.close()
            print("Connection to XBee closed.")

if __name__ == "__main__":
    main()