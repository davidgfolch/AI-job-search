@echo off
cd apps/viewer
poetry run streamlit run .\viewer\main.py
cd ../..
