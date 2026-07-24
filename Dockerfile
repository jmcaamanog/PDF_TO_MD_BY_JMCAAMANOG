FROM python:3.11-slim

# Evitar generación de bytecode y forzar salida en tiempo real
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/models_cache \
    TORCH_HOME=/app/models_cache \
    MARKER_HOME=/app/models_cache

# Instalación de librerías del sistema necesarias para OpenCV y PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . .

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando de arranque
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
