import os
import sys
import time
import json
import requests
import paho.mqtt.client as mqtt
import warnings
from datetime import datetime, timezone

warnings.filterwarnings("ignore", category=DeprecationWarning)
sys.stdout.reconfigure(line_buffering=True)

HEADSCALE_API_URL = os.environ.get("HEADSCALE_API_URL")
HEADSCALE_API_KEY = os.environ.get("HEADSCALE_API_KEY")
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", 30))

DISCOVERY_PREFIX = "homeassistant"
DEVICE_PREFIX = "headscale"

VERSION = "0.1.0-beta"
print(f"Starting Headscale HA Exporter v{VERSION}")
print(f"API URL: {HEADSCALE_API_URL}")
print(f"MQTT: {MQTT_BROKER}:{MQTT_PORT}")
print(f"Poll interval: {POLL_INTERVAL}s")

client = mqtt.Client()
if MQTT_USER:
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
if MQTT_PORT == 8883:
    client.tls_set()

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("MQTT connected successfully")
except Exception as e:
    print(f"MQTT connection failed: {e}")
    sys.exit(1)

def fetch_nodes():
    url = f"{HEADSCALE_API_URL}/api/v1/node"
    headers = {"Authorization": f"Bearer {HEADSCALE_API_KEY}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("nodes", [])
        else:
            print(f"Error fetching nodes: {r.status_code}")
    except Exception as e:
        print(f"Exception: {e}")
    return []

def time_ago(timestamp_str):
    try:
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - ts
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h {(seconds % 3600) // 60}m ago"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h ago"
    except:
        return "unknown"

def publish_discovery(node):
    name = node.get("givenName")
    node_id = f"{DEVICE_PREFIX}_{name}"
    state_topic = f"{DEVICE_PREFIX}/nodes/{name}/state"
    attr_topic = f"{DEVICE_PREFIX}/nodes/{name}/attributes"

    discovery_topic = f"{DISCOVERY_PREFIX}/binary_sensor/{node_id}/config"
    discovery_payload = {
        "name": name,
        "unique_id": node_id,
        "object_id": node_id,
        "state_topic": state_topic,
        "payload_on": "online",
        "payload_off": "offline",
        "device_class": "connectivity",
        "json_attributes_topic": attr_topic,
        "device": {
            "identifiers": [node_id],
            "name": "Headscale Nodes",
            "manufacturer": "Headscale",
            "model": "Tailscale Node"
        }
    }
    client.publish(discovery_topic, json.dumps(discovery_payload), retain=True)
    return state_topic, attr_topic

def publish_state(node, state_topic, attr_topic):
    name = node.get("givenName")
    online = node.get("online", False)
    last_seen = node.get("lastSeen", "")

    client.publish(state_topic, "online" if online else "offline", retain=True)

    attrs = {
        "hostname": node.get("name"),
        "user": node.get("user", {}).get("displayName") or node.get("user", {}).get("name"),
        "last_seen": last_seen,
        "last_seen_ago": time_ago(last_seen) if last_seen else "unknown",
        "tailnet_ip": node.get("ipAddresses", [""])[0],
        "ip_addresses": node.get("ipAddresses", []),
        "approved_routes": node.get("approvedRoutes", []),
    }
    client.publish(attr_topic, json.dumps(attrs), retain=True)
    print(f"  - {name} ({'online' if online else 'offline'}) last seen: {attrs['last_seen_ago']}")

# Publish discovery configs
print("Publishing MQTT discovery configs...")
nodes = fetch_nodes()
for node in nodes:
    publish_discovery(node)
print(f"Discovery published for {len(nodes)} nodes")

# Main loop
while True:
    nodes = fetch_nodes()
    if nodes:
        print(f"Publishing state for {len(nodes)} nodes...")
        for node in nodes:
            state_topic, attr_topic = publish_discovery(node)
            publish_state(node, state_topic, attr_topic)
    else:
        print("No nodes fetched")
    time.sleep(POLL_INTERVAL)
