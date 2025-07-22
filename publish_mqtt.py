# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 16:08:02 2025

@author: Jan
"""

import json
import time
from typing import Dict, Any

#from publish_mqtt import current_home_config
from math import radians, cos, sin, asin, sqrt
import paho.mqtt.client as mqtt
from NovaApi.ListDevices.nbe_list_devices import request_device_list
from NovaApi.ExecuteAction.LocateTracker.location_request import get_location_data_for_device
from ProtoDecoders.decoder import parse_device_list_protobuf, get_canonic_ids

# MQTT Configuration
MQTT_BROKER = "192.168.1.100"  # Change this to your MQTT broker address
MQTT_PORT = 1883
MQTT_USERNAME = "DeinMqttUser"  # Set your MQTT username if required
MQTT_PASSWORD = "DeinMqttPassword"  # Set your MQTT password if required
lat_home = 0 #48.8909528  # DEIN Zuhause-Breitengrad
lon_home = 0 #9.1904316   # DEIN Zuhause-Längengrad
home_cycle = 0 #200 # Umkreis der Homezone in [m]
config_received = False

MQTT_CLIENT_ID = "google_find_my_publisher"

current_home_config = {
    "lat_home": lat_home,
    "lon_home": lon_home,
    "home_radius": home_cycle
}

# Home Assistant MQTT Discovery
DISCOVERY_PREFIX = "homeassistant"
DEVICE_PREFIX = "google_find_my"

def on_any_message(client, userdata, msg):
    print(f"ANY MSG: {msg.topic} → {msg.payload.decode()}")



def on_connect(client, userdata, flags, result_code, properties):
    """Callback when connected to MQTT broker"""
    print("===> on_config_message aufgerufen!")
    print(f"Connected to MQTT broker with result code {result_code}")
    client.subscribe("googlefindmytools/config")
    print(current_home_config)



def calculate_distance(lat1, lon1, lat2, lon2):
    """Berechnet Entfernung zwischen zwei GPS-Koordinaten in Metern."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return 6371000 * c  # Erdradius in Metern


def on_config_message(client, userdata, msg):
    global current_home_config, config_received
    print(f"[MQTT] Nachricht empfangen auf Topic: {msg.topic}")
    print(f"[MQTT] Payload: {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())
        lat = float(payload.get("lat_home", current_home_config["lat_home"]))
        lon = float(payload.get("lon_home", current_home_config["lon_home"]))
        radius = int(payload.get("home_radius", current_home_config["home_radius"]))

        current_home_config["lat_home"] = lat
        current_home_config["lon_home"] = lon
        current_home_config["home_radius"] = radius

        config_received = True  # Markiere, dass Konfiguration eingetroffen ist

        print(f"[Config] Neue Home-Zone: lat={lat}, lon={lon}, radius={radius} m")
    except Exception as e:
        print(f"[Config] Fehler beim Verarbeiten der Konfiguration: {e}")





def publish_device_config(client: mqtt.Client, device_name: str, canonic_id: str) -> None:
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
            "manufacturer": "Google"
        }
    }
    print(f"{base_topic}/config")
    # Publish discovery config
    r = client.publish(f"{base_topic}/config", json.dumps(config), retain=True)
    return r

def publish_device_state(client, name, cid, location_data):
    # 1) Hole Home‑Zone
    lat_home = current_home_config["lat_home"]
    lon_home = current_home_config["lon_home"]
    home_radius = current_home_config["home_radius"]

    # 2) Versuche GPS‑Koordinaten
    lat = location_data.get("latitude")
    lon = location_data.get("longitude")
    sem = location_data.get("semantic_location")

    # 3) State‑Ermittlung
    if lat is not None and lon is not None:
        dist = calculate_distance(lat_home, lon_home, lat, lon)
        state = "home" if dist < home_radius else "not_home"

    elif sem:
        # Fallback: semantischer Raum → immer Home‑Koordinaten
        lat, lon = lat_home, lon_home
        if sem.lower() == "zuhause":
            state = "home"
        else:
            state = sem  # z.B. "Arbeitszimmer"
        print(f"[Fallback] Semantische Position erkannt: '{sem}' → Fallback-Koordinaten werden verwendet.")

    else:
        # keinerlei Info
        state = "unknown"

    # 4) Attribute‑Payload
    attrs = {
        "latitude":          lat,
        "longitude":         lon,
        "altitude":          location_data.get("altitude"),
        "gps_accuracy":      location_data.get("accuracy"),
        "source_type":       "gps" if location_data.get("latitude") is not None else "semantic",
        "last_updated":      location_data.get("timestamp"),
        "semantic_location": sem
    }

    # 5) Publish
    topic_state = f"homeassistant/device_tracker/google_find_my_{cid}/state"
    topic_attr  = f"homeassistant/device_tracker/google_find_my_{cid}/attributes"

    client.publish(topic_state, state, retain=True)
    client.publish(topic_attr,  json.dumps(attrs), retain=True)

def main():
    # Initialize MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, MQTT_CLIENT_ID)
    #client.subscribe("googlefindmytools/config")
    client.on_connect = on_connect
    client.on_message = on_any_message

    client.message_callback_add("googlefindmytools/config", on_config_message)
    #client.subscribe("googlefindmytools/config")


    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        print("Starte Verbindung zu MQTT...")
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_start()
        print("→ MQTT Verbindung gestartet")
        print("Warte auf MQTT-Konfiguration... (max 5 Sekunden)")
        timeout = 5
        waited = 0
        while not config_received and waited < timeout:
           time.sleep(0.1)
           waited += 0.1
           if int(waited * 10) % 10 == 0:  # jede volle Sekunde
              print(f"  ...warte seit {int(waited)}s")
        if config_received:
           print("Konfiguration empfangen.")
        else:
           print("Keine Konfiguration empfangen – verwende Default-Werte.")


        print("Loading devices...")
        result_hex = request_device_list()
        device_list = parse_device_list_protobuf(result_hex)
        canonic_ids = get_canonic_ids(device_list)

        print(f"Found {len(canonic_ids)} devices")

        # Publish discovery config and state for each device
        for device_name, canonic_id in canonic_ids:
            print("\n" + "=" * 60)
            print(f"Processing device: {device_name}")
            print("=" * 60)


            # Publish discovery config (optional – funktioniert nicht zwingend jedes Mal)
            try:
                if client.is_connected():
                    msg_info = publish_device_config(client, device_name, canonic_id)
                    msg_info.wait_for_publish()
                else:
                    print(f"[Discovery] MQTT nicht verbunden – Discovery für {device_name} übersprungen.")
            except Exception as e:
                print(f"[Discovery] Error publishing config for {device_name}: {e}")

            # Get and publish location data
            try:
                location_data = get_location_data_for_device(canonic_id, device_name)
                if location_data:
                    if client.is_connected():
                        msg_info = publish_device_state(client, device_name, canonic_id, location_data)
                        msg_info.wait_for_publish()
                        print(f"Published data for {device_name}")
                    else:
                        raise Exception("MQTT client is not connected during state publish")
                else:
                    raise Exception("Keine Standortdaten vorhanden")
            except Exception as e:
                print(f"[Error] Fehler beim Verarbeiten von {device_name}: {e}")

                # Fallback auf unknown, wenn keine Daten gepublisht werden konnten
                try:
                    if client.is_connected():
                        fallback_info = client.publish(
                            f"homeassistant/device_tracker/{DEVICE_PREFIX}_{canonic_id}/state",
                            payload="unknown",
                            retain=True
                        )
                        fallback_info.wait_for_publish()
                        print(f"[Fallback] Unknown-Status für {device_name} veröffentlicht.")
                    else:
                        print(f"[Fallback] MQTT nicht verbunden – konnte 'unknown' für {device_name} nicht setzen.")
                except Exception as retry_e:
                    print(f"[Fallback] Fehler beim Setzen von 'unknown' für {device_name}: {retry_e}")

            print("-" * 60)


        print("\nAll devices have been published to MQTT")
        print("Devices will now be discoverable in Home Assistant")
        print("You may need to restart Home Assistant or trigger device discovery")



    finally:
        print("→ MQTT Loop stoppen...")
        client.loop_stop()  # Stoppt die MQTT-Loop
        print("→ MQTT Verbindung trennen...")
        client.disconnect()  # Trennt die Verbindung zum Broker

        # Falls ein FCM Listener läuft, stoppen (nur wenn du darauf Zugriff hast)
        try:
            if 'fcm_client' in locals():  # Überprüfen, ob fcm_client existiert
                fcm_client.stop()  # Falls du eine Instanz gespeichert hast
                print("→ FCM Listener gestoppt.")
            else:
                print("→ Kein FCM Listener gefunden.")
        except AttributeError as e:
            print(f"[Error] Fehler beim Stoppen des FCM Listeners: {e}")
        except Exception as e:
            print(f"[Unexpected Error] Ein unerwarteter Fehler ist aufgetreten: {e}")





if __name__ == '__main__':
    main()

