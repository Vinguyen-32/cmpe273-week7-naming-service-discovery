"""
Discovery Client
CMPE 273 Take-Home Assignment

Demonstrates:
  1. Query the registry to discover all instances of a service
  2. Pick a random instance (client-side load balancing)
  3. Call that instance
  4. Repeat N times to show traffic is spread across instances
"""

import random
import time
import logging
import argparse

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CLIENT] %(message)s")
log = logging.getLogger(__name__)

REGISTRY_URL = "http://localhost:5001"


def discover(service_name: str) -> list[dict]:
    """Return list of healthy instances from the registry."""
    r = requests.get(f"{REGISTRY_URL}/discover/{service_name}", timeout=3)
    r.raise_for_status()
    return r.json()["instances"]


def call_random_instance(instances: list[dict], path: str = "/hello") -> dict:
    """Pick a random instance and call it — client-side load balancing."""
    instance = random.choice(instances)
    url = f"{instance['address']}{path}"
    log.info("→ Calling %s", url)
    r = requests.get(url, timeout=3)
    r.raise_for_status()
    return {"instance": instance["address"], "response": r.json()}


def run_demo(service_name: str, calls: int = 10):
    log.info("=== Discovery Client Demo ===")
    log.info("Service: %s  |  Calls: %d", service_name, calls)

    # 1. Discover
    instances = discover(service_name)
    log.info("Discovered %d instance(s):", len(instances))
    for inst in instances:
        log.info("  • %s  (uptime %.0fs)", inst["address"], inst["uptime_seconds"])

    # 2. Call random instance N times
    tally: dict[str, int] = {}
    for i in range(1, calls + 1):
        result = call_random_instance(instances)
        addr = result["instance"]
        tally[addr] = tally.get(addr, 0) + 1
        log.info("  [%d/%d] Response from %s: %s", i, calls, addr, result["response"]["message"])
        time.sleep(0.3)

    # 3. Print distribution
    print("\n── Load Distribution ──────────────────────────────")
    for addr, count in sorted(tally.items()):
        bar = "█" * count
        print(f"  {addr:30s}  {bar}  ({count}/{calls})")
    print("───────────────────────────────────────────────────\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discovery Client")
    parser.add_argument("--service", default="hello-service", help="Service name to discover")
    parser.add_argument("--calls", type=int, default=10, help="Number of calls to make")
    args = parser.parse_args()

    run_demo(args.service, args.calls)
