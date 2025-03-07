#!/bin/bash

# Abrir cada script en una nueva pestaña del terminal usando terminator
terminator --new-tab -e "bash -c './run_1_Mysql.sh; exec bash'" --title="run_1_Mysql" && \
    terminator --new-tab -e "bash -c './run_2_Scraper.sh; exec bash'" --title="run_2_Scraper"
terminator --new-tab -e "bash -c './run_3_AiEnricher.sh; exec bash'" --title="run_3_AiEnricher"
terminator --new-tab -e "bash -c './run_4_Viewer.sh; exec bash'" --title="run_4_Viewer"