#!/bin/bash
set -e
cd /home/runner/workspace/artifacts/api-server
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8080}" --reload --log-level info
