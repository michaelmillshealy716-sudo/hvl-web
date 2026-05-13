#!/bin/bash
while true
do
  echo "[VERITAS] Executing Quantitative Engine..."
  python fase_euler.py
  
  echo "[GIT] Synchronizing Telemetry..."
  git add web_status.json
  git commit -m "Live Data Update: $(date +'%Y-%m-%d %H:%M:%S')"
  git push origin main
  
  echo "[SLEEP] Standby for 5 minutes..."
  sleep 300
done
