@echo off
echo Iniciando servidor SST con WebSocket (ASGI + recarga automatica)...
cd /d "%~dp0sst_proyecto"
call "%~dp0venv\Scripts\activate"
watchfiles "daphne sst_proyecto.asgi:application" .
