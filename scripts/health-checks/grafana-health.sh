#!/bin/bash
curl -sf http://localhost:3000/api/health && echo "Grafana is healthy!" || echo "Grafana is NOT healthy!"
