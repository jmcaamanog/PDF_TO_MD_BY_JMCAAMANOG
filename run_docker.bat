@echo off
title Lanzador Docker - PDF to .MD by jmcaamanog
cd /d "%~dp0"

echo =====================================================================
echo    Lanzador Automático Docker - PDF to .MD (Ejecución Aislada)
echo =====================================================================
echo.

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker no esta instalado o no se encuentra activo.
    echo Por favor inicia Docker Desktop y vuelve a ejecutar este script.
    echo.
    pause
    exit /b 1
)

echo [INFO] Construyendo e iniciando contenedor aislado...
docker compose up --build -d

if %errorlevel% equ 0 (
    echo.
    echo [OK] Servidor iniciado correctamente en Docker!
    echo.
    echo Abriendo http://localhost:8501 en tu navegador...
    start http://localhost:8501
) else (
    echo [ERROR] No se pudo iniciar el contenedor Docker.
)

pause
