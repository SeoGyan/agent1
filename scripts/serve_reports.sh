#!/bin/bash
# Starts a local HTTP server to preview SEO reports in the browser.
# Runs automatically — no need to start it manually.

PORT=8888
DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Kill any existing server on this port
pkill -f "http.server $PORT" 2>/dev/null

# Start server in background
python3 -m http.server "$PORT" --directory "$DIR" &>/tmp/seo-server.log &
echo "SEO report server running at http://localhost:$PORT"
echo "Reports directory: $DIR"
