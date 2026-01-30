#!/usr/bin/env bash
set -euo pipefail

echo "Installing AIOS Layer dependencies (Ubuntu 24.04)."
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin jq curl

echo "Installing NVIDIA container toolkit."
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi not found. Install NVIDIA driver before continuing."
fi

if ! command -v nvidia-container-toolkit >/dev/null 2>&1; then
  distribution=$(. /etc/os-release; echo "${ID}${VERSION_ID}")
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -fsSL https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  sudo apt-get update
  sudo apt-get install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
fi

echo "Done. You may need to log out/in to access docker without sudo."
