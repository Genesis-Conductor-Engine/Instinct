#!/usr/bin/env bash
set -euo pipefail

sudo mkdir -p /etc/aios
sudo cp config/aios.yaml /etc/aios/aios.yaml

sudo useradd --system --no-create-home --shell /usr/sbin/nologin aios || true

sudo cp deploy/aios-agent.service /etc/systemd/system/aios-agent.service
sudo systemctl daemon-reload
sudo systemctl enable aios-agent.service

echo "Installed systemd unit. Start with: sudo systemctl start aios-agent"
