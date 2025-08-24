#!/bin/bash
# Start core infrastructure: Traefik and Portainer
docker compose --profile infra up -d traefik portainer sftp-demo postgres

echo "Infra services started: Traefik and Portainer"
