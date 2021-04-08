#!/usr/bin/env bash

cd /peloton-server
./holoviews_app.py >/var/log/holoviews.log 2>&1 &
uvicorn  --host 0.0.0.0 --port 8888 run app:app
