#!/bin/bash
.venv/bin/python3 -V

if [[ "$*" == *"DEV"* ]]
then
    echo "DEV Mode using streamlit fileWatcher for changes"
    echo "If you get an error on maxFileWatch use: "
    echo "cat /proc/sys/fs/inotify/max_user_watches"
    echo "sudo sysctl fs.inotify.max_user_watches=524288"
    .venv/bin/python3 -m streamlit run src/ai_job_search/view.py --server.headless true
else
    echo "DEV Mode disabled by default, activate it using: ./run_4_Viewer.sh dev"
    .venv/bin/python3 -m streamlit run src/ai_job_search/view.py --server.fileWatcherType none --server.headless true
fi

