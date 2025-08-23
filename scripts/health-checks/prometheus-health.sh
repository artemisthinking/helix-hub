#!/bin/bash
curl -sf http://localhost:9090/-/ready && echo "Prometheus is healthy!" || echo "Prometheus is NOT healthy!"
