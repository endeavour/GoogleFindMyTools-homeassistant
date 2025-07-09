import json
import time
from typing import Dict, Any

import paho.mqtt.client as mqtt
from NovaApi.ListDevices.nbe_list_devices import request_device_list
from NovaApi.ExecuteAction.LocateTracker.location_request import (
    get_location_data_for_device,
)
from ProtoDecoders.decoder import parse_device_list_protobuf, get_canonic_ids

# MQTT Configuration
MQTT_BROKER = "192.168.1.10"  # Change this to your MQTT broker address
MQTT_PORT = 1883
MQTT_USERNAME = None  # Set your MQTT username if required
MQTT_PASSWORD = None  # Set your MQTT password if required
MQTT_CLIENT_ID = "google_find_my_publisher"

# Home Assistant MQTT Discovery
DISCOVERY_PREFIX = "homeassistant"
DEVICE_PREFIX = "google_find_my"

def on_connect(client, userdata, flags, result_code, properties):
    """Callback when connected to MQTT broker"""
    print(f"Connected to MQTT broker with result code {result_code}")


def publish_device_config(
    client: mqtt.Client, device_name: str, canonic_id: str
) -> None:
    """Publish Home Assistant MQTT discovery configuration for a device"""
    base_topic = f"{DISCOVERY_PREFIX}/device_tracker/{DEVICE_PREFIX}_{canonic_id}"

    # Device configuration for Home Assistant
    config = {
        "unique_id": f"{DEVICE_PREFIX}_{canonic_id}",
        "state_topic": f"{base_topic}/state",
        "json_attributes_topic": f"{base_topic}/attributes",
        "source_type": "gps",
        "device": {
            "identifiers": [f"{DEVICE_PREFIX}_{canonic_id}"],
            "name": device_name,
            "model": "Google Find My Device",
            "manufacturer": "Google",
        },
    }
    print(f"{base_topic}/config")
    # Publish discovery config
    r = client.publish(f"{base_topic}/config", json.dumps(config), retain=True)
    return r


def publish_device_state(
    client: mqtt.Client, device_name: str, canonic_id: str, location_data: Dict
) -> None:
    """Publish device state and attributes to MQTT"""
    base_topic = f"{DISCOVERY_PREFIX}/device_tracker/{DEVICE_PREFIX}_{canonic_id}"

    # Extract location data
    lat = location_data.get("latitude")
    lon = location_data.get("longitude")
    accuracy = location_data.get("accuracy")
    altitude = location_data.get("altitude")
    timestamp = location_data.get("timestamp", time.time())

    # Publish state (home/not_home/unknown)
    state = "unknown"
    client.publish(f"{base_topic}/state", state)

    # Publish attributes
    attributes = {
        "latitude": lat,
        "longitude": lon,
        "altitude": altitude,
        "gps_accuracy": accuracy,
        "source_type": "gps",
        "last_updated": timestamp,
    }
    r = client.publish(f"{base_topic}/attributes", json.dumps(attributes))
    return r


def main():
    # Initialize MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, MQTT_CLIENT_ID)
    client.on_connect = on_connect

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_start()

        print("Loading devices...")
        result_hex = request_device_list()
        device_list = parse_device_list_protobuf(result_hex)
        canonic_ids = get_canonic_ids(device_list)

        print(f"Found {len(canonic_ids)} devices")
        
        # Publish discovery config and state for each device
        for device_name, canonic_id in canonic_ids:
            print(f"Processing device: {device_name}")
            
            # Publish discovery configuration
            msg_info = publish_device_config(client, device_name, canonic_id)
            msg_info.wait_for_publish()
            
            # Get and publish location data
            location_data = get_location_data_for_device(canonic_id, device_name)
            msg_info = publish_device_state(client, device_name, canonic_id, location_data)
            msg_info.wait_for_publish()

            print(f"Published data for {device_name}")
            
        print("\nAll devices have been published to MQTT")
        print("Devices will now be discoverable in Home Assistant")
        print("You may need to restart Home Assistant or trigger device discovery")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
