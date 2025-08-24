#!/bin/bash
# Start core infrastructure: Traefik and Portainer

docker compose up -d traefik portainer

echo "Infra services started: Traefik and Portainer"
