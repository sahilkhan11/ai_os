#!/bin/bash
set -e

# Set up virtual display
export DISPLAY=:99

echo "Starting Xvfb on DISPLAY $DISPLAY..."
# 1280x800 is a good default resolution for agent processing
Xvfb $DISPLAY -screen 0 1280x800x24 &

# Wait briefly for Xvfb to be ready
sleep 1

echo "Starting XFCE4..."
startxfce4 &

echo "Starting x11vnc..."
# -shared allows multiple connections, -nopw disables password (safe since we only expose noVNC)
x11vnc -display $DISPLAY -forever -shared -nopw -quiet -listen localhost -xkb &

echo "Starting noVNC (accessible at http://localhost:8080)..."
/opt/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 0.0.0.0:8080
