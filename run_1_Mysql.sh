#!/bin/bash
sudo service docker start
docker-compose up -d && docker-compose logs -f
