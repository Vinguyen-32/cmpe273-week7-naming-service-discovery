"""
Hello Microservice
CMPE 273 Take-Home Assignment

Usage:
    python service.py --name hello-service --port 8001
    python service.py --name hello-service --port 8002

Each instance:
  1. Registers itself with the registry on startup
  2. Sends heartbeats every 10 s
  3. Deregisters gracefully on shutdown (Ctrl-C)
"""

import argparse
import signal
import sys
import threading
import time
import logging

import requests
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SERVICE %(port)s] %(message)s")

REGISTRY_URL = "http://localhost:5001"
HEARTBEAT_INTERVAL = 10  # seconds


class MicroService:
    def __init__(self, name: str, port: int):
        self.name = name
        self.port = port
        self.address = f"http://localhost:{port}"
        self.log = logging.LoggerAdapter(
            logging.getLogger(__name__), {"port": port}
        )
        self.app = Flask(__name__)
        self._setup_routes()


    def _setup_routes(self):
        app = self.app
        svc = self  # closure

        @app.route("/health")
        def health():
            return jsonify({"status": "ok", "service": svc.name, "port": svc.port})

        @app.route("/hello")
        def hello():
            return jsonify({
                "message": f"Hello from {svc.name}!",
                "instance": svc.address,
                "port": svc.port,
                "timestamp": time.time(),
            })

        @app.route("/info")
        def info():
            return jsonify({
                "name": svc.name,
                "address": svc.address,
                "uptime": round(time.time() - svc._start_time, 1),
            })

 
    def _register(self):
        for attempt in range(5):
            try:
                r = requests.post(
                    f"{REGISTRY_URL}/register",
                    json={"service": self.name, "address": self.address},
                    timeout=3,
                )
                r.raise_for_status()
                self.log.info("Registered with registry as %s", self.name)
                return
            except Exception as exc:
                self.log.warning("Register attempt %d failed: %s", attempt + 1, exc)
                time.sleep(2)
        self.log.error("Could not register — is the registry running?")

    def _heartbeat_loop(self):
        while self._running:
            try:
                requests.post(
                    f"{REGISTRY_URL}/heartbeat",
                    json={"service": self.name, "address": self.address},
                    timeout=3,
                )
                self.log.info("Heartbeat sent")
            except Exception as exc:
                self.log.warning("Heartbeat failed: %s", exc)
            time.sleep(HEARTBEAT_INTERVAL)

    def _deregister(self):
        try:
            requests.post(
                f"{REGISTRY_URL}/deregister",
                json={"service": self.name, "address": self.address},
                timeout=3,
            )
            self.log.info("Deregistered from registry")
        except Exception as exc:
            self.log.warning("Deregister failed: %s", exc)


    def start(self):
        self._start_time = time.time()
        self._running = True

        self._register()

        hb = threading.Thread(target=self._heartbeat_loop, daemon=True)
        hb.start()

        def _shutdown(sig, frame):
            self.log.info("Shutting down …")
            self._running = False
            self._deregister()
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        self.log.info("Listening on port %d", self.port)
        self.app.run(port=self.port, debug=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hello Microservice")
    parser.add_argument("--name", default="hello-service", help="Service name")
    parser.add_argument("--port", type=int, default=8001, help="Listen port")
    args = parser.parse_args()

    MicroService(args.name, args.port).start()
