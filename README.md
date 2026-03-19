# Microservice with Discovery — CMPE 273 Take-Home

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Service Registry  :5001                 │
│  POST /register   GET /discover/:name   POST /heartbeat    │
└──────────┬───────────────────────────────────┬─────────────┘
           │  register + heartbeat             │  discover
           │                                   │
  ┌────────▼────────┐                 ┌────────▼────────┐
  │ hello-service-1 │                 │ hello-service-2 │
  │    Port 8001    │                 │    Port 8002    │
  └─────────────────┘                 └─────────────────┘
                          ↑
               ┌──────────┴──────────┐
               │   Discovery Client  │
               │  random() instance  │
               └─────────────────────┘
```

## Quick Start (Local — no Docker)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Terminal 1 — Start Registry
```bash
python registry/registry.py
# Listening on :5001
```

### 3. Terminal 2 — Start Instance 1
```bash
python service/service.py --name hello-service --port 8001
```

### 4. Terminal 3 — Start Instance 2
```bash
python service/service.py --name hello-service --port 8002
```

### 5. Terminal 4 — Run Client
```bash
python client/client.py --service hello-service --calls 12
```

Expected output:
```
── Load Distribution ──────────────────────────────
  http://localhost:8001    ██████  (6/12)
  http://localhost:8002    ██████  (6/12)
───────────────────────────────────────────────────
```

## Quick Start (Docker Compose)

```bash
# Start registry + both service instances
docker compose up --build

# In a second terminal, run the client demo
docker compose --profile demo up client
```

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET  | /health | Registry health check |
| POST | /register | Register an instance `{service, address}` |
| POST | /heartbeat | Send heartbeat `{service, address}` |
| POST | /deregister | Remove instance `{service, address}` |
| GET  | /discover/:name | Get all instances of a service |
| GET  | /services | List all registered services |

## Files

```
.
├── registry/
│   └── registry.py          # Central service registry (Flask, port 5001)
├── service/
│   └── service.py           # Hello microservice (register + heartbeat)
├── client/
│   └── client.py            # Discovery client (random load balancing)
├── docker/
│   ├── Dockerfile.registry
│   ├── Dockerfile.service
│   └── Dockerfile.client
├── docker-compose.yml
└── requirements.txt
```

## How It Works

1. **Registration** — Each service instance calls `POST /register` with its name and address at startup.
2. **Heartbeat** — Every 10 s each instance calls `POST /heartbeat`. The registry removes instances that go silent for >30 s.
3. **Discovery** — The client calls `GET /discover/hello-service` to get the live instance list.
4. **Random selection** — The client picks a random instance (`random.choice`) and calls it directly.

## Testing with curl (Terminal 5)

### Registry endpoints (port 5001)
```bash
# Check registry is alive
curl http://localhost:5001/health

# List all registered services
curl http://localhost:5001/services

# Discover all instances of hello-service
curl http://localhost:5001/discover/hello-service
```

### Manually register a fake service
```bash
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"service": "test-service", "address": "http://localhost:9999"}'
```

### Send a heartbeat for it
```bash
curl -X POST http://localhost:5001/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"service": "test-service", "address": "http://localhost:9999"}'
```

### Deregister it
```bash
curl -X POST http://localhost:5001/deregister \
  -H "Content-Type: application/json" \
  -d '{"service": "test-service", "address": "http://localhost:9999"}'
```

### Call the service instances directly (port 8001 / 8002)
```bash
# Health check on each instance
curl http://localhost:8001/health
curl http://localhost:8002/health

# The actual hello endpoint
curl http://localhost:8001/hello
curl http://localhost:8002/hello

# Instance info (name, uptime)
curl http://localhost:8001/info
curl http://localhost:8002/info
```

## Optional: Service Mesh (Istio)

With Istio, discovery moves out of the application code:
- Each pod gets an **Envoy sidecar proxy** injected automatically
- Proxies handle retries, mTLS, circuit breaking, and load balancing
- Kubernetes DNS + Istio `VirtualService` replace the custom registry

See `docs/ISTIO.md` for a starter config.



