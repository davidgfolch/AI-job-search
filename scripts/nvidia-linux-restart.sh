#!/bin/bash

function pause() {
    read -p "$*"
}

echo "==================================================================================="
echo "Linux Script to workarround nvidia driver problem after sleep/wake-up linux systems"
echo "==================================================================================="
echo ""

while [ True ]; do
    echo "Starting Ollama service"
    sudo systemctl start ollama
    echo "Killing nvidia-settings application..."
    $(pkill -9 -f '^nvidia-settings$') 1>&- 2>&-
    sleep .5
    echo "Starting nvidia-settings application..."
    nvidia-settings 2>/dev/null 1>/dev/null &

    echo ""
    echo "clear && sudo journalctl -u ollama -f | perl ~/scripts/colorTail.pl \"gpu|cuda\""
    pause "Press [Enter] stop ollama & nvidia-settings"
    echo ""
    echo "(Root pasword needed to restart services)"
    echo "Killing nvidia-settings application..."
    $(pkill -9 -f '^nvidia-settings$') 1>&- 2>&-
    sleep .5
    echo "Stoping Ollama service..."
    sudo systemctl stop ollama
    sleep .5
    pause "Press [Enter] to restart nvidia driver & start ollama & nvidia-settings"
    echo "Restarting nvidia driver..."
    sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm
    sleep .5
done
