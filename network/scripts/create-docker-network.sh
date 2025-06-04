#!/bin/bash

# Remove existing network if exists
if docker network ls | grep -q "ecg_network"; then
    echo "Removing existing ecg_network..."
    docker network rm ecg_network 2>/dev/null || echo "Network removal failed (containers might be using it)"
fi

echo "Creating Docker network ecg_network..."
docker network create --driver bridge --subnet=172.20.0.0/16 ecg_network

echo "✓ Network created successfully"

# List networks
docker network ls | grep ecg_network
