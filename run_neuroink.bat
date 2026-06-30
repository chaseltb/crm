@echo off
:: NeuroInk demo — runs on port 8052
:: Login: demo@neuroink.io / neuroink2024

set CRM_CONFIG=%~dp0config.neuroink.yaml
set CRM_DB=%~dp0data\neuroink\etherealcrm.db
set CRM_PORT=8052

echo Starting NeuroInk demo on http://localhost:8052
echo Login: demo@neuroink.io / neuroink2024
echo.

python "%~dp0app.py"
