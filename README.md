# 📄 PDF to .MD by jmcaamanog

### La herramienta libre y 100% offline para la conversión inteligente de documentos PDF a Markdown (.md).
*Desarrollado desde la perspectiva real de un Arquitecto Técnico para dotar al sector de una utilidad ágil, segura y privada en el procesamiento de información técnica.*

---

<p align="center">
  <a href="https://github.com/jmcaamanog/PDF_TO_MD_BY_JMCAAMANOG/releases/latest"><img src="https://img.shields.io/github/v/release/jmcaamanog/PDF_TO_MD_BY_JMCAAMANOG?label=Version&color=3b82f6&logo=github" alt="Versión"></a>
  <a href="https://github.com/jmcaamanog/PDF_TO_MD_BY_JMCAAMANOG/stargazers"><img src="https://img.shields.io/github/stars/jmcaamanog/PDF_TO_MD_BY_JMCAAMANOG?style=flat&label=Stars&color=f59e0b&logo=github" alt="Stars"></a>
  <a href="https://github.com/jmcaamanog/PDF_TO_MD_BY_JMCAAMANOG/blob/main/LICENSE"><img src="https://img.shields.io/badge/Licencia-MIT-8b5cf6.svg" alt="Licencia"></a>
  <a href="https://jmcaamanog.pages.dev/"><img src="https://img.shields.io/badge/Plataforma-Windows%20%7C%20Local-06b6d4" alt="Plataformas"></a>
  <a href="https://www.linkedin.com/in/jmcaamanog/"><img src="https://img.shields.io/badge/Profesi%C3%B3n-Arquitectos%20T%C3%A9cnicos-2e7d32?logo=micro%3Abit&logoColor=white" alt="Profesión"></a>
</p>

---

## ⚡ Enlaces y Accesos Rápidos

| 🌟 Recurso | 🚀 Acción / Enlace | 📝 Descripción |
| :--- | :--- | :--- |
| **Capturas de Pantalla** | 💻 **[Ver Galería de Capturas](./CAPTURAS)** | Capturas de pantalla de la interfaz de usuario en Windows. |

---

> [!IMPORTANT]
> ### 📥 Lanzador de Escritorio (Listo para usar)
> Si deseas usar la herramienta en tu ordenador en local:
> 1. Descarga el repositorio completo en un archivo ZIP.
> 2. Extrae el ZIP en tu disco duro (por ejemplo, en `C:\PDF_TO_MD`).
> 3. Haz doble clic en el archivo `setup_and_run.bat` para iniciar la instalación automática y abrir la interfaz web en tu navegador local `http://localhost:8501`.
> 
> *El script se encarga de crear el entorno virtual, instalar PyTorch con soporte de aceleración gráfica GPU (CUDA) o CPU, y ejecutar el parser offline.*

---

### 👨‍💻 Creador de la Versión Premium
Desarrollado y optimizado por `José Manuel Caamaño González` ([LinkedIn](https://www.linkedin.com/in/jmcaamanog/)), Arquitecto Técnico y BIM Manager.
*Bajo la filosofía ConTech de construir puentes entre la construcción tradicional (AECO) y la automatización digital, esta utilidad procesa tus datos locales con máxima privacidad sin depender de APIs de terceros ni enviar información al exterior.*

---

## Descripción

`PDF to .MD` es una aplicación de escritorio local que permite **convertir en lote archivos PDF a Markdown (.md) estructurado**. Al usar motores locales avanzados de inteligencia artificial, la app reconoce de forma autónoma capas de texto, layouts complejos de múltiples columnas, tablas numéricas detalladas y fórmulas matemáticas complejas en formato LaTeX, empaquetando todo de manera portable y segura.

---

## 🌟 Características Principales (PDF to .MD Premium)

| Módulo | Icono | Funcionalidades Destacadas |
| :--- | :---: | :--- |
| **Conversión en Lote** | 📂 | Sube y procesa **múltiples PDFs simultáneamente** y descárgalos agrupados en un solo archivo comprimido `.zip` junto con todas sus imágenes extraídas. |
| **Procesamiento de Carpeta** | 📁 | Indica una **ruta absoluta física de Windows** y la aplicación procesará, convertirá y guardará cada archivo `.md` e imágenes directamente en tu disco duro al lado del PDF original. |
| **Extracción de Tablas** | 📊 | Conserva el formato y la alineación de **tablas complejas de presupuestos, mediciones y datos estructurados** dentro del archivo Markdown final. |
| **Fórmulas LaTeX** | 🧮 | Conversión precisa de **fórmulas y ecuaciones matemáticas** de proyectos de edificación o ingeniería a sintaxis LaTeX integrada. |
| **Aceleración GPU CUDA** | ⚡ | Soporte completo y diagnóstico de la tarjeta gráfica NVIDIA (por ejemplo, la RTX 4070) para **multiplicar la velocidad del proceso de IA** local por hardware. |
| **Operación 100% Offline** | 🔌 | No requiere conexión a internet tras la instalación. Tus datos, presupuestos y planos **nunca abandonan tu máquina**. |
| **Mantenimiento en un Clic** | 🧹 | Panel de **limpieza de caché** interactivo en castellano para liberar la memoria RAM y VRAM (memoria gráfica) de tu equipo de forma segura. |

---

## 📁 Estructura del Directorio

*   **`app.py`**: El motor principal del backend en Python y la interfaz gráfica premium en Streamlit.
*   **`setup_and_run.bat`**: El instalador automático y ejecutable de un solo clic para Windows.
*   **`requirements.txt`**: Definición de librerías esenciales y dependencias de procesamiento de IA.
*   **`yo_animado.gif`**: Avatar animado del autor mostrado en la pestaña de información del creador.
*   **`.streamlit/config.toml`**: Configuración de tema acrílico oscuro personalizado.

---

## 🏁 Primeros Pasos (Instrucciones Simplificadas)

Esta sección está diseñada para ayudarte a poner en marcha la aplicación paso a paso, incluso si no tienes experiencia técnica previa.

### 1. Requisitos de Partida (Hardware y Software)

| Tipo | Componente / Requisito | Propósito | ¿Es obligatorio? |
| :--- | :--- | :--- | :---: |
| **Hardware** | Procesador Intel / AMD con 8 GB de RAM | Ejecutar la aplicación de forma estable. | Sí |
| **Hardware** | Tarjeta Gráfica NVIDIA con soporte CUDA | Acelerar el procesamiento de los PDFs mediante IA por hardware. | Recomendado *(CPU es más lento)* |
| **Software** | [Python 3.11 o 3.12](https://www.python.org/downloads/) | El lenguaje en el que corre la aplicación. | **Sí** *(Marcar "Add Python to PATH" al instalar)* |
| **Software** | [Git (Instalador)](https://git-scm.com/) | Descargar y clonar las actualizaciones de la aplicación. | Opcional |

### 2. Pasos a seguir en tu ordenador (Instalación)

| Paso | Acción a realizar | ¿Qué hace el ordenador? |
| :---: | :--- | :--- |
| **1** | Descarga este proyecto pulsando en el botón verde **Code > Download ZIP** de esta web y descomprímelo en una carpeta de tu disco duro (ej: `C:\PDF_to_MD`). | Prepara los archivos de ejecución en tu máquina local. |
| **2** | Asegúrate de tener Python instalado. Si no estás seguro, descarga el instalador de [Python 3.11 o 3.12](https://www.python.org/downloads/) y ejecútalo. **¡Importante!** Marca la casilla **"Add Python to PATH"** al principio de la instalación. | Registra Python en el sistema para poder arrancar scripts. |
| **3** | Entra en la carpeta descomprimida y haz doble clic sobre el archivo **`setup_and_run.bat`**. | El ordenador creará un entorno virtual seguro (`.venv`), detectará tu tarjeta gráfica NVIDIA, instalará de forma automática las dependencias de IA (PyTorch) y descargará los modelos necesarios. |
| **4** | Una vez termine (tardará unos minutos la primera vez), se abrirá tu navegador en: **`http://localhost:8501`**. | ¡Listo! Ya puedes empezar a arrastrar y convertir tus PDFs en local. |

---

## 🚀 Cómo Ejecutar e Instalar (Instrucciones)

### Requisitos del Sistema
*   Tener instalado [Python 3.11 o 3.12](https://www.python.org/downloads/) en Windows.
*   *Recomendado:* Una tarjeta gráfica NVIDIA con soporte CUDA activo para acelerar la IA por hardware.

### 💻 Lanzamiento de un Clic (setup_and_run.bat)
1. Haz doble clic en `setup_and_run.bat`.
2. El script detectará si posees una tarjeta gráfica NVIDIA y descargará automáticamente la versión optimizada de **PyTorch con soporte CUDA**.
3. Creará un entorno virtual privado `.venv` para no interferir con otras aplicaciones de tu máquina.
4. Descargará los pesos de los modelos de IA en la caché interna local `./models_cache`.
5. Levantará el servidor en **[http://localhost:8501](http://localhost:8501)** de forma automatizada.

---

## 🗺️ Hoja de Ruta (Roadmap)

*   **Fase 1: Conversión básica offline y aceleración CUDA** [✔️ Completado]
    *   Integración del parser local basado en Marker.
    *   Configuración automática de hardware para aceleración por GPU NVIDIA CUDA.
*   **Fase 2: Interfaz acrílica y navegación nativa** [✔️ Completado]
    *   Rediseño estilo acrílico oscuro de Windows 11.
    *   Sistema de navegación nativo en columnas ultra rápido y adaptativo.
*   **Fase 3: Procesamiento en lote masivo y escaneo de carpetas** [✔️ Completado]
    *   Procesamiento múltiple y descargas agrupadas en ZIP.
    *   Lectura y escritura local automática en directorios absolutos de Windows.
*   **Fase 4: Exportación extendida a Excel y CSV** [⏳ Planificado]
    *   Módulo para volcar tablas detectadas en los PDFs directamente a archivos `.xlsx` independientes.
*   **Fase 5: Previsualización en vivo en Markdown** [⏳ Planificado]
    *   Visor de doble panel en tiempo real para ver el resultado de la conversión antes de descargar.

---

## 👨‍💻 Autor de la versión

[Jose Manuel Caamaño González](https://www.linkedin.com/in/jmcaamanog/) | Arquitecto Técnico & ConTech Developer.
Digital Product Lead | ConTech & Digital Twin SaaS | BIM, Energy Modeling & Sustainability | Data Analytics (SQL, Power BI).

Hecho con código y café desde A Coruña. ☕
