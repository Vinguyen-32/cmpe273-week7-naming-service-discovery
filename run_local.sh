#!/usr/bin/env bash
# run_local.sh — starts all 3 processes, runs the client demo, then cleans up
# Usage: bash run_local.sh

set -e
cd "$(dirname "$0")"

echo "=== Installing dependencies ==="
pip install -r requirements.txt -q

echo ""
echo "=== Starting Service Registry on :5001 ==="
python registry/registry.py &
REGISTRY_PID=$!
sleep 2

echo ""
echo "=== Starting hello-service instance 1 on :8001 ==="
python service/service.py --name hello-service --port 8001 &
SVC1_PID=$!

echo "=== Starting hello-service instance 2 on :8002 ==="
python service/service.py --name hello-service --port 8002 &
SVC2_PID=$!
sleep 3

echo ""
echo "=== Running Discovery Client (12 calls) ==="
python client/client.py --service hello-service --calls 12

echo ""
echo "=== Shutting down ==="
kill $REGISTRY_PID $SVC1_PID $SVC2_PID 2>/dev/null
echo "Done."
