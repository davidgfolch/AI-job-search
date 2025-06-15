#!/bin/bash

wait_for_mysql() {
    while ! nc -z 127.0.0.1 3306; do
        echo "Waiting for MySQL server to be ready..."
        sleep 2
    done
    sleep 4
}

dependant_scripts() {
    terminator --new-tab --title="Ollama logs" --command="bash -c 'sudo clear && journalctl -u ollama -f | perl ~/scripts/colorTail.pl \"gpu|cuda\"; exec bash'"
    sleep 5
    terminator --new-tab --title="run_2_Scraper" --command="bash -c './scripts/run_2_Scraper.sh; exec bash'"
    sleep 5
    terminator --new-tab --title="run_3_AiEnricher" --command="bash -c './scripts/run_3_AiEnricher.sh; exec bash'"
    sleep 5
    terminator --new-tab --title="run_4_Viewer" --command="bash -c './scripts/run_4_Viewer.sh; exec bash'"
}

terminator --new-tab --title="run_1_Mysql" --command="bash -c 'sudo ./scripts/run_1_Mysql.sh; exec bash'" && \
    wait_for_mysql && \
    dependant_scripts


# run new bash terminal in tab


