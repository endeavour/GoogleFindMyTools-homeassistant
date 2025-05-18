import json
import time
from datetime import datetime
from typing import Dict, Any

import paho.mqtt.client as mqtt
from NovaApi.ListDevices.nbe_list_devices import request_device_list
from NovaApi.ExecuteAction.LocateTracker.location_request import get_location_data_for_device
from ProtoDecoders.decoder import parse_device_list_protobuf, get_canonic_ids

# MQTT Configuration
MQTT_BROKER = "localhost"       # Replace with your MQTT broker address
MQTT_PORT = 1883
MQTT_USERNAME = "username"              # Optional: set your MQTT username
MQTT_PASSWORD = "password"            # Optional: set your MQTT password
MQTT_CLIENT_ID = "google_find_my_publisher"

# Home Assistant MQTT Discovery
DISCOVERY_PREFIX = "homeassistant"
DEVICE_PREFIX = "google_find_my"

def on_connect(client, userdata, flags, result_code, properties):
    print(f"[MQTT] Connected to broker with result code {result_code}")

def publish_device_config(client: mqtt.Client, device_name: str, canonic_id: str) -> None:
    """
    Publishes the MQTT discovery configuration for Home Assistant
    """
    base_topic = f"{DISCOVERY_PREFIX}/device_tracker/{DEVICE_PREFIX}_{canonic_id}"

    config = {
        "unique_id": f"{DEVICE_PREFIX}_{canonic_id}",
        "state_topic": f"{base_topic}/state",
        "json_attributes_topic": f"{base_topic}/attributes",
        "source_type": "gps",
        "device": {
            "identifiers": [f"{DEVICE_PREFIX}_{canonic_id}"],
            "name": device_name,
            "model": "Google Find My Device",
            "manufacturer": "Google"
        }
    }

    client.publish(f"{base_topic}/config", json.dumps(config), retain=True)

def publish_device_state(client: mqtt.Client, device_name: str, canonic_id: str, location_data: Dict) -> None:
    """
    Publishes device state and attributes to MQTT
    """
    base_topic = f"{DISCOVERY_PREFIX}/device_tracker/{DEVICE_PREFIX}_{canonic_id}"

    try:
        lat = location_data.get('latitude')
        lon = location_data.get('longitude')
        accuracy = location_data.get('accuracy')
        altitude = location_data.get('altitude')
        raw_ts = location_data.get('timestamp', time.time())

        # Normalize timestamp (handles string, milliseconds, and invalid formats)
        try:
            if isinstance(raw_ts, str):
                dt = datetime.strptime(raw_ts, "%Y-%m-%d %H:%M:%S")
                timestamp = int(dt.timestamp())
            elif isinstance(raw_ts, (int, float)):
                timestamp = int(raw_ts)
                if timestamp > 9999999999:
                    timestamp = timestamp // 1000  # convert milliseconds to seconds
            else:
                raise ValueError(f"Unsupported timestamp format: {raw_ts}")
        except Exception:
            timestamp = int(time.time())

        state = "unknown"  # Optional: implement proximity logic for 'home' vs 'not_home'
        attributes = {
            "latitude": lat,
            "longitude": lon,
            "altitude": altitude,
            "gps_accuracy": accuracy,
            "source_type": "gps",
            "last_updated": timestamp
        }

        client.publish(f"{base_topic}/state", state)
        client.publish(f"{base_topic}/attributes", json.dumps(attributes))

    except Exception as e:
        print(f"[ERROR] Failed to publish state for {device_name}: {e}")

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, MQTT_CLIENT_ID)
    client.on_connect = on_connect

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_start()

        print("[INFO] Loading devices...")
        result_hex = request_device_list()
        device_list = parse_device_list_protobuf(result_hex)
        canonic_ids = get_canonic_ids(device_list)

        print(f"[INFO] Found {len(canonic_ids)} devices")

        for device_name, canonic_id in canonic_ids:
            print(f"[INFO] Publishing: {device_name}")
            try:
                publish_device_config(client, device_name, canonic_id)
                location_data = get_location_data_for_device(canonic_id, device_name)
                publish_device_state(client, device_name, canonic_id, location_data)
            except Exception as e:
                print(f"[ERROR] Failed to process {device_name}: {e}")

        print("[OK] All devices successfully published to MQTT")

    except Exception as e:
        print(f"[FATAL] General error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    main()
