# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 16:08:02 2025

@author: Jan
"""

from systemd.daemon import notify
import threading
import time
import sys


import json
import time
from math import radians, cos, sin, asin, sqrt
import paho.mqtt.client as mqtt
from NovaApi.ListDevices.nbe_list_devices import request_device_list
from NovaApi.ExecuteAction.LocateTracker.location_request import get_location_data_for_device
from ProtoDecoders.decoder import parse_device_list_protobuf, get_canonic_ids

# MQTT Configuration
MQTT_BROKER = "192.168.3.65"
MQTT_PORT = 1883
MQTT_USERNAME = "mqttuser"
MQTT_PASSWORD = "Coconuts1990"

# Home zone defaults
lat_home = 0  # placeholder until config arrives
lon_home = 0
home_radius = 0
config_received = False
last_full_update = 0.0 

MQTT_CLIENT_ID = "google_find_my_publisher"

# Home Assistant MQTT Discovery prefixes
DISCOVERY_PREFIX = "homeassistant"
DEVICE_PREFIX = "google_find_my"

current_home_config = {
    "lat_home": lat_home,
    "lon_home": lon_home,
    "home_radius": home_radius
}

# MQTT Callbacks and helpers

def _thread_excepthook(args):
    """Beende den Prozess, sobald irgendein Thread eine unbehandelte Exception wirft."""
    print(f"⚠️ Uncaught thread exception: {args.exc_value!r} – exiting.")
    sys.exit(1)
threading.excepthook = _thread_excepthook
    

def calculate_distance(lat1, lon1, lat2, lon2):
    """Berechnet Entfernung zwischen zwei GPS-Koordinaten in Metern."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return 6371000 * c  # Erdradius


def on_any_message(client, userdata, msg):
    print(f"ANY MSG: {msg.topic} → {msg.payload.decode()}")


def on_connect(client, userdata, flags, result_code, properties=None):
    print("🔌 Connected to MQTT, rc=", result_code)
    client.subscribe([
        ("googlefindmytools/config", 0),
        ("googlefindmytools/trigger/update", 0),
    ])
    print("Current home config:", current_home_config)
    print("✅ Subscribed to config & trigger/update")

def on_disconnect(*args, **kwargs):
    print("⚠️ MQTT disconnected—will reconnect…")

def on_config_message(client, userdata, msg):
    global config_received
    print(f"[Config] Topic: {msg.topic}, Payload: {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())
        current_home_config.update({
            "lat_home": float(payload.get("lat_home", current_home_config["lat_home"])),
            "lon_home": float(payload.get("lon_home", current_home_config["lon_home"])),
            "home_radius": int(payload.get("home_radius", current_home_config["home_radius"]))
        })
        config_received = True
        print("✅ Updated home zone:", current_home_config)
    except Exception as e:
        print("❌ Error parsing config:", e)


def publish_device_config(client, device_name, canonic_id):
    base = f"{DISCOVERY_PREFIX}/device_tracker/{DEVICE_PREFIX}_{canonic_id}"
    cfg = {
        "unique_id": f"{DEVICE_PREFIX}_{canonic_id}",
        "state_topic": f"{base}/state",
        "json_attributes_topic": f"{base}/attributes",
        "source_type": "gps",
        "device": {"identifiers": [f"{DEVICE_PREFIX}_{canonic_id}"],
                   "name": device_name,
                   "model": "Google Find My Device",
                   "manufacturer": "Google"}
    }
    client.publish(f"{base}/config", json.dumps(cfg), retain=True)


def publish_device_state(client, name, cid, loc):
    lat = loc.get("latitude")
    lon = loc.get("longitude")
    sem = loc.get("semantic_location")
    if lat is not None and lon is not None:
        dist = calculate_distance(current_home_config["lat_home"],
                                  current_home_config["lon_home"], lat, lon)
        state = "home" if dist < current_home_config["home_radius"] else "not_home"
    elif sem:
        state = "home" if sem.lower() == "zuhause" else sem
        lat, lon = current_home_config["lat_home"], current_home_config["lon_home"]
    else:
        state = "unknown"

    attrs = {
        "latitude": lat,
        "longitude": lon,
        "altitude": loc.get("altitude"),
        "gps_accuracy": loc.get("accuracy"),
        "source_type": "gps" if lat is not None else "semantic",
        "last_updated": loc.get("timestamp"),
        "semantic_location": sem
    }

    topic_s = f"homeassistant/device_tracker/google_find_my_{cid}/state"
    topic_a = f"homeassistant/device_tracker/google_find_my_{cid}/attributes"
    client.publish(topic_s, state, retain=True)
    client.publish(topic_a, json.dumps(attrs), retain=True)


def run_full_update(client):
    """Ruft Liste ab und published Config+State für alle Geräte."""
    global last_full_update
    print("▶️ Triggered run_full_update at", time.strftime("%Y-%m-%d %H:%M:%S"))
    try:
        hexdata = request_device_list()
        devices = parse_device_list_protobuf(hexdata)
        for name, cid in get_canonic_ids(devices):
            publish_device_config(client, name, cid)
            loc = get_location_data_for_device(cid, name)
            publish_device_state(client, name, cid, loc or {})
        print("✅ Full update complete")        
        last_full_update = time.time()
    except Exception as e:
        print("❌ run_full_update error:", e)


def main():
    global last_full_update

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, MQTT_CLIENT_ID)
    client.on_connect    = on_connect
    client.on_message    = on_any_message
    client.message_callback_add("googlefindmytools/config",        on_config_message)
    #client.message_callback_add("googlefindmytools/trigger/update", lambda c,u,m: run_full_update(c))
    client.message_callback_add(
        "googlefindmytools/trigger/update",
        lambda c, u, m: (
            print("📨 Received trigger/update payload:", m.payload.decode()),
            run_full_update(c)
        )
    )
    
    
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    client.on_disconnect = on_disconnect

    # Auth
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    print("🔌 Connecting to MQTT…")
    client.connect(MQTT_BROKER, MQTT_PORT)

    # Start loop
    client.loop_start()
    
    notify("READY=1")
    
    last_full_update = time.time()

    # Watchdog-Ping alle 10 Sekunden
    def _wd_pinger():
        INTERVAL = 30            # Sekunde(n) zwischen Pings
        THRESHOLD = 400           # wenn seit 60 s kein Full‑Update lief, kein Ping mehr
        while True:
            now = time.time()
            if now - last_full_update < THRESHOLD:
                notify("WATCHDOG=1")
            else:
                print("⚠️ Dienst scheint nicht mehr gesund (kein Full‑Update seit", 
                      int(now - last_full_update), "s). Watchdog darf eingreifen.")
                break
            time.sleep(INTERVAL)


    threading.Thread(target=_wd_pinger, daemon=True).start()    
    

    # wait for config if needed

    t0 = time.time()
    while not config_received and time.time() - t0 < 5:
        time.sleep(0.1)
    if not config_received:
        print("⚠️ No config received, using defaults.")

    # initial update
    run_full_update(client)

    # stay in loop for triggers
    client.loop_forever()


if __name__ == '__main__':
    main()

