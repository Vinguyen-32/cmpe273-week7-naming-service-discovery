"""
Service Registry - Central discovery server
CMPE 273 Take-Home Assignment
Stores registered service instances and answers discovery queries.
"""

from flask import Flask, request, jsonify
import threading
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [REGISTRY] %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)

# { service_name: { address: { registered_at, last_heartbeat } } }
registry: dict = {}
lock = threading.Lock()

HEARTBEAT_TIMEOUT = 30  # seconds — instance considered dead after this


def _cleanup_stale():
    """Background thread: remove instances that stopped sending heartbeats."""
    while True:
        time.sleep(10)
        now = time.time()
        with lock:
            for svc in list(registry.keys()):
                for addr in list(registry[svc].keys()):
                    age = now - registry[svc][addr]["last_heartbeat"]
                    if age > HEARTBEAT_TIMEOUT:
                        log.warning("Removing stale instance %s @ %s (silent for %.0fs)", svc, addr, age)
                        del registry[svc][addr]
                if not registry[svc]:
                    del registry[svc]


threading.Thread(target=_cleanup_stale, daemon=True).start()


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "registry"})


@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    name = data.get("service")
    addr = data.get("address")
    if not name or not addr:
        return jsonify({"error": "service and address required"}), 400

    with lock:
        registry.setdefault(name, {})[addr] = {
            "registered_at": time.time(),
            "last_heartbeat": time.time(),
        }

    log.info("Registered  %s @ %s", name, addr)
    return jsonify({"status": "registered", "service": name, "address": addr})


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json or {}
    name = data.get("service")
    addr = data.get("address")
    if not name or not addr:
        return jsonify({"error": "service and address required"}), 400

    with lock:
        if name in registry and addr in registry[name]:
            registry[name][addr]["last_heartbeat"] = time.time()
            return jsonify({"status": "ok"})
        return jsonify({"error": "instance not registered"}), 404


@app.route("/deregister", methods=["POST"])
def deregister():
    data = request.json or {}
    name = data.get("service")
    addr = data.get("address")
    with lock:
        if name in registry and addr in registry[name]:
            del registry[name][addr]
            if not registry[name]:
                del registry[name]
            log.info("Deregistered %s @ %s", name, addr)
            return jsonify({"status": "deregistered"})
    return jsonify({"error": "instance not found"}), 404


@app.route("/discover/<service_name>")
def discover(service_name):
    with lock:
        instances = registry.get(service_name, {})
        now = time.time()
        result = [
            {
                "address": addr,
                "uptime_seconds": round(now - meta["registered_at"], 1),
            }
            for addr, meta in instances.items()
        ]

    if not result:
        return jsonify({"error": f"No instances found for '{service_name}'"}), 404

    return jsonify({"service": service_name, "instances": result, "count": len(result)})


@app.route("/services")
def list_services():
    with lock:
        summary = {
            svc: {"instances": list(addrs.keys()), "count": len(addrs)}
            for svc, addrs in registry.items()
        }
    return jsonify({"services": summary, "total": len(summary)})


if __name__ == "__main__":
    log.info("Service Registry starting on port 5001")
    app.run(port=5001, debug=False)
