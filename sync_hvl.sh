#!/bin/bash

# 1. LEAD ARCHITECT'S COOLDOWN
# Wait 2 seconds just to make sure Session 1 isn't mid-write
sleep 2

# 2. GIT PRODUCTION PIPELINE
# We don't run python here anymore. We just grab what the engine already made.
git add index.html web_graph_data.json series_history.json
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
git commit -m "telemetry: passive sync from live engine @ $TIMESTAMP"

# 3. PUSH TO REMOTE
git push origin main

echo -e "\e[92m[ SUCCESS ] Live Engine Data Pushed @ $TIMESTAMP\e[0m"

