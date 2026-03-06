# Headscale Home Assistant Exporter

![Version](https://img.shields.io/badge/version-0.2.0--beta-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A lightweight Docker-based exporter that polls the [Headscale](https://github.com/juanfont/headscale) API and publishes node status to Home Assistant via MQTT Discovery.

## Features

- 🟢 Real-time online/offline status for all Headscale nodes
- 📡 Auto-discovery in Home Assistant — no manual entity configuration
- 🕐 Human-readable "last seen" timestamps (e.g. `5m ago`, `2d 3h ago`)
- 👤 User, Tailnet IP, and approved routes per node
- 👥 Group mapping — assign nodes to groups for filtered dashboard cards
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

| Attribute | Description |
|---|---|
| `online` | true/false |
| `last_seen` | ISO timestamp |
| `last_seen_ago` | Human readable e.g. `5m ago` |
| `tailnet_ip` | First IPv4 tailnet address |
| `ip_addresses` | All IP addresses |
| `user` | Headscale user display name |
| `group` | Group assigned via `USER_GROUPS` mapping |
| `approved_routes` | Advertised subnet routes |
| `hostname` | Machine hostname |

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
| `USER_GROUPS` | JSON mapping of user display names to group names |

### 3. Configure group mappings

The `USER_GROUPS` environment variable maps Headscale user display names to group names. This adds a `group` attribute to each node entity in Home Assistant, allowing you to create filtered dashboard cards per group.
```bash
USER_GROUPS={"Marius Viljoen":"MVSolar","Rika Viljoen":"MVSolar","Riaan Grobler":"Admin"}
```

Any user not in the mapping will be assigned the group `Other`.

### 4. Configure Docker network

The exporter needs to be on the same Docker network as Headscale. Update `docker-compose.yml` with your Headscale network name:
```yaml
networks:
  headscale_network:
    external: true
    name: headscale_headscale_default
```

To find your Headscale network name:
```bash
docker network ls | grep headscale
```

### 5. Build and run
```bash
docker compose build
docker compose up -d
docker logs headscale-exporter -f
```

## Home Assistant

Once running, entities will auto-discover in Home Assistant under:

**Settings → Devices & Services → MQTT → Devices → Headscale Nodes**

Each node appears as `binary_sensor.headscale_<nodename>`.

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

## Dashboard

A ready-made Lovelace dashboard card is available in [DASHBOARD.md](DASHBOARD.md) showing:
- Online/Offline/Total summary
- Filter buttons (All / Online / Offline)
- Sortable node table
- Group filtered cards (MVSolar, Dyna, IT & Admin)

### Required HACS Cards
- [flex-table-card](https://github.com/custom-cards/flex-table-card)
- [auto-entities](https://github.com/iantrich/config-template-card)
- [button-card](https://github.com/custom-cards/button-card)
- [state-switch](https://github.com/thomasloven/lovelace-state-switch)

## License

MIT

## Health Check

The exporter exposes a health check endpoint on port `8099` (configurable via `HEALTH_PORT`):
```bash
curl http://your-vps-ip:8099/health
```

Returns:
```json
{
  "status": "ok",
  "version": "0.2.1-beta",
  "uptime_since": "2026-03-06T07:07:59Z",
  "last_poll": "2026-03-06T07:08:29Z",
  "nodes_total": 17,
  "nodes_online": 10,
  "poll_count": 2,
  "mqtt_connected": true
}
```

Add `HEALTH_PORT=8099` to your `.env` to change the port.

## State Persistence

The exporter saves node online timestamps to `/app/data/node_state.json` so that connection durations survive container restarts.

The `data/` directory is mounted as a volume in `docker-compose.yml`:
```yaml
cat >> /headscale/headscale-ha-exporter/README.md << 'EOF'

## State Persistence

The exporter saves node online timestamps to `/app/data/node_state.json` so that connection durations survive container restarts.

The `data/` directory is mounted as a volume in `docker-compose.yml`:
```yaml
volumes:
  - ./data:/app/data
```

This means:
- ✅ Container restarts preserve `connected_since` timestamps
- ✅ `status_info` attribute shows correct `Up Xh Xm` after restart
- ✅ State is saved once per poll cycle

The `data/` directory is created automatically on first run.

## Attributes Reference

Each `binary_sensor.headscale_<nodename>` entity exposes the following attributes:

| Attribute | Description | Example |
|---|---|---|
| `hostname` | Machine hostname | `macbookpro` |
| `user` | Headscale user display name | `Riaan Grobler` |
| `group` | Group from `USER_GROUPS` mapping | `Admin` |
| `last_seen` | ISO timestamp of last seen | `2026-03-06T07:00:00Z` |
| `last_seen_ago` | Human readable last seen | `5m ago` |
| `status_info` | Up duration or last seen ago | `Up 2h 30m` or `1d 2h ago` |
| `tailnet_ip` | First IPv4 tailnet address | `100.64.0.4` |
| `ip_addresses` | All IP addresses | `100.64.0.4, fd7a::4` |
| `approved_routes` | Advertised subnet routes | `192.168.1.0/24` |
| `connected_since` | ISO timestamp of when node came online | `2026-03-06T07:00:00Z` |
| `connected_duration` | How long node has been online | `2h 30m` |

## State Persistence

The exporter saves node online timestamps to `/app/data/node_state.json` so that connection durations survive container restarts.

The `data/` directory is mounted as a volume in `docker-compose.yml`:
```yaml
volumes:
  - ./data:/app/data
```

This means:
- ✅ Container restarts preserve `connected_since` timestamps
- ✅ `status_info` attribute shows correct `Up Xh Xm` after restart
- ✅ State is saved once per poll cycle

The `data/` directory is created automatically on first run.

## Attributes Reference

Each `binary_sensor.headscale_<nodename>` entity exposes the following attributes:

| Attribute | Description | Example |
|---|---|---|
| `hostname` | Machine hostname | `macbookpro` |
| `user` | Headscale user display name | `Riaan Grobler` |
| `group` | Group from `USER_GROUPS` mapping | `Admin` |
| `last_seen` | ISO timestamp of last seen | `2026-03-06T07:00:00Z` |
| `last_seen_ago` | Human readable last seen | `5m ago` |
| `status_info` | Up duration or last seen ago | `Up 2h 30m` or `1d 2h ago` |
| `tailnet_ip` | First IPv4 tailnet address | `100.64.0.4` |
| `ip_addresses` | All IP addresses | `100.64.0.4, fd7a::4` |
| `approved_routes` | Advertised subnet routes | `192.168.1.0/24` |
| `connected_since` | ISO timestamp of when node came online | `2026-03-06T07:00:00Z` |
| `connected_duration` | How long node has been online | `2h 30m` |
