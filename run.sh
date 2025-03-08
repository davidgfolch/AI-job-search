#!/bin/bash

wait_for_mysql() {
    while ! nc -z 127.0.0.1 3306; do
        echo "Waiting for MySQL server to be ready..."
        sleep 2
    done
}

dependant_scripts() {
    terminator --new-tab -e "bash -c './scripts/run_2_Scraper.sh; exec bash'" --title="run_2_Scraper"
    terminator --new-tab -e "bash -c './scripts/run_3_AiEnricher.sh; exec bash'" --title="run_3_AiEnricher"
    terminator --new-tab -e "bash -c './scripts/run_4_Viewer.sh; exec bash'" --title="run_4_Viewer"
    terminator --new-tab -e "bash -c ' clear && sudo journalctl  -u ollama -f | perl ~/scripts/colorTail.pl \"gpu|cuda\"; exec bash'" --title="run_4_Viewer"
}

terminator --new-tab -e "bash -c './scripts/run_1_Mysql.sh; exec bash'" --title="run_1_Mysql" && \
    wait_for_mysql && \
    dependant_scripts
