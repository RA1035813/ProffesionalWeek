#!/bin/bash

# Forceer de Docker API versie naar 1.41 om de client/server mismatch te fixen
export DOCKER_API_VERSION=1.41

echo "--- Starten van SoilSMS Containers (API versie: $DOCKER_API_VERSION) ---"

# Start docker compose met alle meegegeven argumenten (standaard --build)
# Gebruik ./startDocker.sh -d om op de achtergrond te draaien
docker compose up --build "$@"
