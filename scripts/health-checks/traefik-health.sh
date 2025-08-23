#!/bin/bash
curl -sf http://localhost:8080/api/health && echo "Traefik is healthy!" || echo "Traefik is NOT healthy!"
