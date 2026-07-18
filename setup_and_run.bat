@echo off
title Lanzador de Conversor PDF a Markdown
cd /d "%~dp0"

echo =====================================================================
echo       Lanzador Automático - Conversor de PDF a Markdown (Local)
echo =====================================================================
echo.

:: 1. Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH del sistema.
    echo.
    echo Por favor:
    echo 1. Descarga Python 3.11 o 3.12 desde python.org.
    echo 2. Ejecuta el instalador.
    echo 3. IMPORTANTE: Marca la casilla Add Python to PATH al inicio de la instalacion.
    echo 4. Vuelve a ejecutar este archivo.
    echo.
    pause
    exit /b 1
)

:: Mostrar versión de Python detectada
echo [OK] Python detectado: 
python --version
echo.

:: 2. Crear entorno virtual si no existe
if not exist ".venv" (
    echo [INFO] Creando entorno virtual aislado...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

:: 3. Activar entorno virtual
echo [INFO] Activando entorno virtual...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

:: 4. Verificar si ya se instalaron las dependencias anteriormente
if not exist ".venv\.installed" (
    echo [INFO] Primera ejecucion detectada. Configurando dependencias...
    echo [INFO] Esto puede tardar varios minutos dependiendo de tu conexion.
    echo.

    :: Comprobar si hay GPU NVIDIA
    nvidia-smi >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] GPU NVIDIA detectada. Instalando PyTorch con soporte CUDA - Aceleracion por Grafica...
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
    ) else (
        echo [INFO] No se detecto GPU NVIDIA. Instalando PyTorch version CPU - Sera mas lento...
        pip install torch torchvision torchaudio
    )

    if %errorlevel% neq 0 (
        echo [ERROR] Error al instalar PyTorch.
        pause
        exit /b 1
    )

    echo.
    echo [INFO] Instalando libreria de conversion y Streamlit...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Error al instalar las dependencias de requirements.txt.
        pause
        exit /b 1
    )

    :: Crear archivo bandera de instalacion completada
    echo. > ".venv\.installed"
    echo [OK] Dependencias instaladas correctamente.
    echo.
) else (
    echo [OK] Dependencias ya instaladas.
)

:: 5. Establecer la cache de modelos localmente en la carpeta del proyecto
echo [INFO] Configurando cache local de modelos de IA en la carpeta 'models_cache'...
set HF_HOME=%CD%\models_cache
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

:: 6. Iniciar la aplicacion de Streamlit
echo [INFO] Iniciando la aplicacion web...
echo Si el navegador no se abre automaticamente, visita: http://localhost:8501
echo.
streamlit run app.py

pause
