#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "打开 http://127.0.0.1:8765/index.html"
python3 -m http.server 8765
