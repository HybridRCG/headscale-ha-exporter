import os
import sys
import time
import json
import requests
import paho.mqtt.client as mqtt
import warnings
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

warnings.filterwarnings("ignore", category=DeprecationWarning)
sys.stdout.reconfigure(line_buffering=True)

VERSION = "0.2.1-beta"

HEADSCALE_API_URL = os.environ.get("HEADSCALE_API_URL")
HEADSCALE_API_KEY = os.environ.get("HEADSCALE_API_KEY")
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", 30))
HEALTH_PORT = int(os.environ.get("HEALTH_PORT", 8080))

USER_GROUPS = json.loads(os.environ.get("USER_GROUPS", "{}"))

DISCOVERY_PREFIX = "homeassistant"
DEVICE_PREFIX = "headscale"

node_online_since = {}
node_previous_state = {}
stats = {
    "start_time": datetime.now(timezone.utc).isoformat(),
    "last_poll": None,
    "nodes_total": 0,
    "nodes_online": 0,
    "poll_count": 0,
    "mqtt_connected": False,
}

print(f"Starting Headscale HA Exporter v{VERSION}")
print(f"API URL: {HEADSCALE_API_URL}")
print(f"MQTT: {MQTT_BROKER}:{MQTT_PORT}")
print(f"Poll interval: {POLL_INTERVAL}s")
print(f"Health check port: {HEALTH_PORT}")
print(f"User groups loaded: {len(USER_GROUPS)} mappings")

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            payload = {
                "status": "ok",
                "version": VERSION,
                "uptime_since": stats["start_time"],
                "last_poll": stats["last_poll"],
                "nodes_total": stats["nodes_total"],
                "nodes_online": stats["nodes_online"],
                "poll_count": stats["poll_count"],
                "mqtt_connected": stats["mqtt_connected"],
            }
            body = json.dumps(payload, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def start_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    print(f"Health check server started on port {HEALTH_PORT}")
    server.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()

def on_connect(c, userdata, flags, rc):
    stats["mqtt_connected"] = rc == 0

def on_disconnect(c, userdata, rc):
    stats["mqtt_connected"] = False
    print(f"MQTT disconnected (rc={rc}), reconnecting...")
    while True:
        try:
            c.reconnect()
            print("MQTT reconnected successfully")
            break
        except Exception as e:
            print(f"Reconnect failed: {e}, retrying in 10s...")
            time.sleep(10)

client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
if MQTT_USER:
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
if MQTT_PORT == 8883:
    client.tls_set()

while True:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print("MQTT connected successfully")
        stats["mqtt_connected"] = True
        break
    except Exception as e:
        print(f"MQTT connection failed: {e}, retrying in 10s...")
        time.sleep(10)

def fetch_nodes():
    url = f"{HEADSCALE_API_URL}/api/v1/node"
    headers = {"Authorization": f"Bearer {HEADSCALE_API_KEY}"}
    retries = 3
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json().get("nodes", [])
            else:
                print(f"Error fetching nodes: {r.status_code}")
        except Exception as e:
            print(f"Exception fetching nodes (attempt {attempt+1}/{retries}): {e}")
            time.sleep(5)
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

def duration_since(timestamp_str):
    try:
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        seconds = int((now - ts).total_seconds())
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h"
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
    user = node.get("user", {}).get("displayName") or node.get("user", {}).get("name")
    group = USER_GROUPS.get(user, "Other")

    prev = node_previous_state.get(name)
    if online and prev is False:
        node_online_since[name] = datetime.now(timezone.utc).isoformat()
        print(f"  ↑ {name} came online")
    elif not online:
        node_online_since.pop(name, None)

    node_previous_state[name] = online

    connected_since = node_online_since.get(name)
    connected_duration = duration_since(connected_since) if connected_since else None

    client.publish(state_topic, "online" if online else "offline", retain=True)

    attrs = {
        "hostname": node.get("name"),
        "user": user,
        "group": group,
        "last_seen": last_seen,
        "last_seen_ago": time_ago(last_seen) if last_seen else "unknown",
        "tailnet_ip": node.get("ipAddresses", [""])[0],
        "ip_addresses": node.get("ipAddresses", []),
        "approved_routes": node.get("approvedRoutes", []),
        "connected_since": connected_since,
        "connected_duration": connected_duration,
    }
    client.publish(attr_topic, json.dumps(attrs), retain=True)
    duration_str = f" | connected {connected_duration}" if connected_duration else ""
    print(f"  - {name} ({'online' if online else 'offline'}) [{group}]{duration_str}")

print("Publishing MQTT discovery configs...")
nodes = fetch_nodes()
for node in nodes:
    publish_discovery(node)
    # On startup, seed online_since for already-online nodes
    name = node.get("givenName")
    if node.get("online"):
        node_online_since[name] = stats["start_time"]
        node_previous_state[name] = True
    else:
        node_previous_state[name] = False
print(f"Discovery published for {len(nodes)} nodes")

while True:
    nodes = fetch_nodes()
    if nodes:
        print(f"Publishing state for {len(nodes)} nodes...")
        online_count = sum(1 for n in nodes if n.get("online"))
        stats["nodes_total"] = len(nodes)
        stats["nodes_online"] = online_count
        stats["last_poll"] = datetime.now(timezone.utc).isoformat()
        stats["poll_count"] += 1
        for node in nodes:
            state_topic, attr_topic = publish_discovery(node)
            publish_state(node, state_topic, attr_topic)
    else:
        print("No nodes fetched")
    time.sleep(POLL_INTERVAL)
