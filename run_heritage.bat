@echo off
:: Heritage Landscaping demo — runs on port 8051
:: Login: demo@heritagelandscaping.com / heritage2024

set CRM_CONFIG=%~dp0config.heritage.yaml
set CRM_DB=%~dp0data\heritage\etherealcrm.db
set CRM_PORT=8051

echo Starting Heritage Landscaping demo on http://localhost:8051
echo Login: demo@heritagelandscaping.com / heritage2024
echo.

python "%~dp0app.py"
