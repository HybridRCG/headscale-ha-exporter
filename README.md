# Headscale Home Assistant Exporter

![Version](https://img.shields.io/badge/version-0.1.0--beta-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A lightweight Docker-based exporter that polls the [Headscale](https://github.com/juanfont/headscale) API and publishes node status to Home Assistant via MQTT Discovery.

## Features

- 🟢 Real-time online/offline status for all Headscale nodes
- 📡 Auto-discovery in Home Assistant — no manual entity configuration
- 🕐 Human-readable "last seen" timestamps (e.g. `5m ago`, `2d 3h ago`)
- 👤 User, Tailnet IP, and approved routes per node
- 🔄 Configurable poll interval
- 🔒 Connects to Headscale internally via Docker network

## Requirements

- Headscale running in Docker
- Home Assistant with Mosquitto MQTT broker add-on
- MQTT reachable from the Headscale VPS (via Tailnet recommended)

## How It Works
```
Headscale API → exporter.py → MQTT Broker → Home Assistant
```

Each node becomes a `binary_sensor` in Home Assistant with the following attributes:
- `online` — true/false
- `last_seen` — ISO timestamp
- `last_seen_ago` — human readable
- `tailnet_ip` — first IPv4 address
- `ip_addresses` — all IPs
- `user` — Headscale user display name
- `approved_routes` — advertised subnet routes

## Installation

### 1. Clone the repo
```bash
git clone https://github.com/HybridRCG/headscale-ha-exporter.git
cd headscale-ha-exporter
```

### 2. Configure environment
```bash
cp .env.example .env
nano .env
```

Fill in your values:

| Variable | Description |
|---|---|
| `HEADSCALE_API_URL` | Internal Headscale URL e.g. `http://headscale:8080` |
| `HEADSCALE_API_KEY` | Headscale API key |
| `MQTT_BROKER` | MQTT broker IP or hostname |
| `MQTT_PORT` | MQTT port (default: `1883`) |
| `MQTT_USER` | MQTT username |
| `MQTT_PASSWORD` | MQTT password |
| `POLL_INTERVAL` | Poll interval in seconds (default: `30`) |

### 3. Configure Docker network

The exporter needs to be on the same Docker network as Headscale. Update `docker-compose.yml` with your Headscale network name:
```yaml
networks:
  headscale_network:
    external: true
    name: your_headscale_network_name
```

To find your Headscale network name:
```bash
docker network ls | grep headscale
```

### 4. Build and run
```bash
docker compose build
docker compose up -d
docker logs headscale-exporter -f
```

## Home Assistant

Once running, entities will auto-discover in Home Assistant under:

**Settings → Devices & Services → MQTT → Devices → Headscale Nodes**

Each node appears as `binary_sensor.headscale_<nodename>`.

## Dashboard

A ready-made Lovelace dashboard card is available in [DASHBOARD.md](DASHBOARD.md) showing:
- Online/Offline/Total summary
- Filter buttons (All / Online / Offline)
- Sortable node table

### Required HACS Cards
- [flex-table-card](https://github.com/custom-cards/flex-table-card)
- [auto-entities](https://github.com/iantrich/config-template-card)
- [button-card](https://github.com/custom-cards/button-card)
- [state-switch](https://github.com/thomasloven/lovelace-state-switch)

## License

MIT

## Headscale ACL Configuration

If your Home Assistant MQTT broker is accessed via the Tailnet (recommended over exposing port 1883 to the internet), you need to allow the Headscale VPS to reach Home Assistant on port 1883.

Add the following rule to your Headscale ACL policy:
```json
{
  "action": "accept",
  "src": [
    "hs-exit"
  ],
  "dst": [
    "ha:1883"
  ]
}
```

Replace `hs-exit` with your VPS node name and `ha` with your Home Assistant node name in Headscale.

To find your node names:
```bash
headscale nodes list
```

This is more secure than exposing MQTT port 1883 directly to the internet — all traffic stays encrypted within the Tailnet.
