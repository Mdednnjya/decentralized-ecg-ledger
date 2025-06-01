#!/bin/bash

# Check if network exists
if docker network ls | grep -q "ecg_network"; then
    echo "Network ecg_network already exists"
else
    echo "Creating Docker network ecg_network..."
    docker network create --driver bridge --subnet=172.20.0.0/16 ecg_network
    echo "✓ Network created successfully"
fi

# List networks
docker network ls | grep ecg_network
