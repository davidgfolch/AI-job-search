#!/bin/bash
sudo service docker start
# wait for docker to start
sleep 5
# check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi
docker-compose up
# docker-compose up -d
# && docker-compose logs -f
