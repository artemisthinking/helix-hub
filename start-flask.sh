#!/bin/bash
# Start Helix Core (Flask app), Postgres, and SFTP demo

docker compose --profile core up -d helix-core postgres
docker compose --profile banking up -d sftp-demo

echo "Helix Core (Flask) started!"
echo "Access Flask app at: http://localhost:5000/"
echo "SFTP demo running on port 2222"
