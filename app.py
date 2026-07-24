import os
import sys
import io
import time
import zipfile
import tempfile
import base64
import re
import urllib.parse
import torch
import streamlit as st

# Intentar importación de librerías para scraping web con fallback
try:
    import requests
    from bs4 import BeautifulSoup
    import html2text
    WEB_EXTRACTOR_AVAILABLE = True
except ImportError:
    WEB_EXTRACTOR_AVAILABLE = False

# Configurar ruta local de caché de modelos ANTES de cualquier importación de marker/transformers
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_CACHE_DIR = os.path.join(CURRENT_DIR, "models_cache")
os.makedirs(MODELS_CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = MODELS_CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Configuración de página de Streamlit
st.set_page_config(
    page_title="PDF to .MD by jmcaamanog",
    page_icon="📄",
    layout="centered"
)

# Inicializar session_state
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "INTRO"
if "upload_mode" not in st.session_state:
    st.session_state.upload_mode = "archivo" # 'archivo', 'carpeta', 'web'
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "es"
if "disable_images" not in st.session_state:
    st.session_state.disable_images = False
if "force_ocr" not in st.session_state:
    st.session_state.force_ocr = False
if "active_preset" not in st.session_state:
    st.session_state.active_preset = "contech" # 'rapido', 'contech', 'ocr'

# Estilos CSS personalizados (Glassmorphic Acrílico + Fluent Design)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

    /* Ocultar la barra superior nativa */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    footer {
        visibility: hidden !important;
    }

    .block-container {
        max-width: 1000px !important;
        padding-top: 5px !important;
        padding-bottom: 15px !important;
        margin: 0 auto !important;
    }
    
    .stApp {
        background: #090d16;
        color: #f3f4f6;
        font-family: 'Inter', sans-serif;
    }

    /* GLASSMORPHIC CONTAINER CARD */
    .glass-card {
        background: rgba(17, 24, 39, 0.65);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease-in-out;
    }
    
    .glass-card:hover {
        border-color: rgba(59, 130, 246, 0.3);
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
    }
    
    /* TODOS los títulos en mayúsculas y en Outfit */
    h1, h2, h3, h4, .title-display {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700;
        text-transform: uppercase !important;
        background: linear-gradient(135deg, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* SEPARADOR ELEGANTE */
    hr {
        border: 0 !important;
        height: 1px !important;
        background: rgba(255, 255, 255, 0.08) !important;
        margin-top: 20px !important;
        margin-bottom: 20px !important;
    }

    /* TEXTOS DE CONTENIDO MÁS ALTOS/GRANDES */
    p, span, li, td, th, table, label, div.stMarkdown p {
        font-size: 16px !important;
        line-height: 1.8 !important;
    }
    
    /* BARRA DE NAVEGACIÓN EN PESTAÑAS */
    div[data-testid="column"] button {
        height: 50px !important;
        border-radius: 10px !important;
        background-color: rgba(17, 24, 39, 0.4) !important;
        color: #9ca3af !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        font-family: 'Outfit', sans-serif !important;
        text-transform: uppercase !important;
        transition: all 0.3s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        width: 100% !important;
    }
    div[data-testid="column"] button:hover {
        color: #ffffff !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(6, 182, 212, 0.12)) !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2) !important;
    }

    /* BOTÓN PRIMARIO DE EJECUCIÓN */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6, #06b6d4) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 12px 30px !important;
        font-family: 'Outfit', sans-serif;
        font-size: 16px;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4);
    }
    
    /* HARDWARE STATUS BAR IN HEADER */
    .hw-bar {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 8px;
        padding: 8px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 12px;
        color: #cbd5e1;
        margin-bottom: 15px;
    }
    .hw-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-weight: 600;
    }
    
    /* PRESET QUICK-PILLS */
    .preset-container {
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
    }
    .preset-pill {
        flex: 1;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(17, 24, 39, 0.4);
        text-align: center;
        font-family: 'Outfit', sans-serif;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    /* METRICS BADGES */
    .metric-card {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .metric-value {
        font-family: 'Outfit', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 11px;
        color: #9ca3af;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# Helper para codificar imágenes a Base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f"data:image/gif;base64,{encoded_string}"

# Encabezado Principal con Logo Diseñado en SVG
st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px; margin-top: 5px;">
  <div style="display: flex; align-items: center; gap: 15px;">
    <svg width="45" height="45" viewBox="0 0 24 24" fill="none" stroke="url(#blue-cyan-grad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <defs>
        <linearGradient id="blue-cyan-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#3b82f6" />
          <stop offset="100%" stop-color="#06b6d4" />
        </linearGradient>
      </defs>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
    <div>
      <h1 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 800; background: linear-gradient(135deg, #3b82f6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 28px; text-transform: uppercase;">PDF to .MD by jmcaamanog</h1>
      <p style='font-size: 13px !important; color: #9ca3af; margin: 0;'>Analizador inteligente de PDFs y Webs para AECO · Motor IA Local</p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------- HARDWARE STATUS BAR (TELEMETRÍA SUPERIOR) -----------------
cuda_available = torch.cuda.is_available()
if cuda_available:
    gpu_name_short = torch.cuda.get_device_name(0)
    mem_alloc_mb = torch.cuda.memory_allocated(0) / (1024**2)
    mem_res_mb = torch.cuda.memory_reserved(0) / (1024**2)
    hw_status_html = f"🟢 <strong>GPU:</strong> {gpu_name_short} &nbsp;|&nbsp; <strong>VRAM:</strong> {mem_alloc_mb:.1f} MB (Res: {mem_res_mb:.1f} MB)"
else:
    hw_status_html = "🔴 <strong>Acelerador:</strong> Modo CPU (Sin GPU CUDA)"

col_hw1, col_hw2 = st.columns([4, 1])
with col_hw1:
    st.markdown(f"""
    <div class="hw-bar">
        <span class="hw-badge">{hw_status_html}</span>
    </div>
    """, unsafe_allow_html=True)

with col_hw2:
    if st.button("🧹 PURGAR VRAM", key="quick_vram_purge", help="Libera la memoria gráfica inmediatamente"):
        st.cache_resource.clear()
        st.cache_data.clear()
        if cuda_available:
            torch.cuda.empty_cache()
        st.success("VRAM Purgada")
        time.sleep(0.8)
        st.rerun()

# ----------------- BARRA DE NAVEGACIÓN EN PESTAÑAS -----------------
col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)

with col_t1:
    if st.button("INTRO", use_container_width=True, key="nav_intro"):
        st.session_state.active_tab = "INTRO"
        st.rerun()

with col_t2:
    if st.button("CONVERTIR", use_container_width=True, key="nav_convert"):
        st.session_state.active_tab = "CONVERTIR"
        st.rerun()

with col_t3:
    if st.button("AJUSTES DE IA", use_container_width=True, key="nav_config"):
        st.session_state.active_tab = "AJUSTES DE IA"
        st.rerun()

with col_t4:
    if st.button("REQUISITOS", use_container_width=True, key="nav_reqs"):
        st.session_state.active_tab = "REQUISITOS"
        st.rerun()

with col_t5:
    if st.button("AUTOR", use_container_width=True, key="nav_about"):
        st.session_state.active_tab = "AUTOR"
        st.rerun()

# Inyectar CSS dinámico para resaltar la pestaña activa
active_child = 1
if st.session_state.active_tab == "CONVERTIR":
    active_child = 2
elif st.session_state.active_tab == "AJUSTES DE IA":
    active_child = 3
elif st.session_state.active_tab == "REQUISITOS":
    active_child = 4
elif st.session_state.active_tab == "AUTOR":
    active_child = 5

st.markdown(f"""
<style>
    div[data-testid="column"]:nth-child({active_child}) button {{
        background: linear-gradient(135deg, #3b82f6, #06b6d4) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.35) !important;
    }}
</style>
""", unsafe_allow_html=True)

st.write("")

# ----------------- RENDERING DEL CONTENIDO DE LA PESTAÑA ACTIVA -----------------

# PESTAÑA 0: INTRO
if st.session_state.active_tab == "INTRO":
    st.markdown("""
    <div class="glass-card">
        <h3 style='color: #06b6d4; font-family:"Outfit"; font-size: 16px; margin-top: 0;'>¿QUÉ PUEDES HACER CON ESTA VERSIÓN PREMIUM?</h3>
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 13.5px; color: #d1d5db;'>
            <div>📄 <strong>Conversión PDF local:</strong> Reconocimiento de texto y columnas con IA</div>
            <div>📂 <strong>Lotes y Carpetas:</strong> Procesamiento masivo automático en disco</div>
            <div>🌐 <strong>Ingesta de Páginas Web:</strong> Extracción directa de URLs a Markdown con fotos</div>
            <div>📊 <strong>Tablas y Presupuestos:</strong> Detección avanzada de celdas y mediciones</div>
            <div>🧮 <strong>Fórmulas LaTeX:</strong> Conversión de matemáticas de edificación a sintaxis limpia</div>
            <div>⚡ <strong>Aceleración GPU CUDA:</strong> Multiplica x10 la velocidad en gráficas NVIDIA</div>
            <div>🔌 <strong>Operación 100% Offline:</strong> Tus datos locales no salen de tu máquina</div>
            <div>🎨 <strong>Interfaz Glassmorphic:</strong> Estilo moderno acrílico Fluent Windows 11</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Caja de Desarrollo Activo
    st.markdown("""
    <div style="border-left: 4px solid #3b82f6; background: rgba(59, 130, 246, 0.04); padding: 16px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
        <span style="font-size:13px; line-height: 1.6; color: #d1d5db;">
            🔧 <strong>Herramienta en Desarrollo Activo (ConTech):</strong> Este proyecto es de código abierto. Si tienes sugerencias o ideas de mejoras, ponte en contacto con el creador del repositorio <strong>Jose Manuel Caamaño</strong> via <a href="https://www.linkedin.com/in/jmcaamanog/" target="_blank" style="color:#3b82f6; text-decoration:none; font-weight:bold;">LinkedIn</a> o mediante su Colegio Profesional de la Arquitectura Técnica (<strong>COATAC</strong>).
        </span>
    </div>
    """, unsafe_allow_html=True)

    col_intro_btn_l, col_intro_btn_c, col_intro_btn_r = st.columns([1, 2, 1])
    with col_intro_btn_c:
        if st.button("🚀 EMPEZAR CONVERSIÓN", key="intro_btn_to_conv", use_container_width=True):
            st.session_state.active_tab = "CONVERTIR"
            st.rerun()

# PESTAÑA 1: CONVERTIR
elif st.session_state.active_tab == "CONVERTIR":
    
    # PRESETS DE CONVERSIÓN RÁPIDA (QUICK-PILLS)
    st.markdown("<h3 style='margin-top:0; font-size:14px; color:#3b82f6; font-family:\"Outfit\"; text-transform:uppercase;'>PERFIL / PRESET RÁPIDO DE IA</h3>", unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        btn_p1_style = "background: linear-gradient(135deg, #0284c7, #0ea5e9); color: white; border-color: #38bdf8;" if st.session_state.active_preset == "rapido" else "background: rgba(17, 24, 39, 0.4); color: #9ca3af;"
        if st.button("⚡ Modo Rápido (Sin Fotos)", key="p_rapido", help="Desactiva imágenes para máxima velocidad"):
            st.session_state.active_preset = "rapido"
            st.session_state.disable_images = True
            st.session_state.force_ocr = False
            st.rerun()
            
    with col_p2:
        btn_p2_style = "background: linear-gradient(135deg, #0f766e, #14b8a6); color: white; border-color: #2dd4bf;" if st.session_state.active_preset == "contech" else "background: rgba(17, 24, 39, 0.4); color: #9ca3af;"
        if st.button("🏗️ Modo ConTech (Tablas & Fotos)", key="p_contech", help="Equilibrado para memorias, tablas y planos"):
            st.session_state.active_preset = "contech"
            st.session_state.disable_images = False
            st.session_state.force_ocr = False
            st.rerun()
            
    with col_p3:
        btn_p3_style = "background: linear-gradient(135deg, #6d28d9, #8b5cf6); color: white; border-color: #a78bfa;" if st.session_state.active_preset == "ocr" else "background: rgba(17, 24, 39, 0.4); color: #9ca3af;"
        if st.button("🧮 Modo OCR & LaTeX Profundo", key="p_ocr", help="Fuerza OCR completo para PDFs escaneados y ecuaciones"):
            st.session_state.active_preset = "ocr"
            st.session_state.disable_images = False
            st.session_state.force_ocr = True
            st.rerun()

    st.divider()

    # CONTENEDOR 1: CARGA ARCHIVOS / CARPETA / WEB URL
    st.markdown("<h3 style='margin-top:0; font-size:14px; color:#3b82f6; font-family:\"Outfit\"; text-transform:uppercase;'>ORIGEN DE DATOS</h3>", unsafe_allow_html=True)
    
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        if st.button("📁 ARCHIVO(S) PDF", key="set_mode_file"):
            st.session_state.upload_mode = "archivo"
            st.rerun()
            
    with col_m2:
        if st.button("📂 CARPETA LOCAL", key="set_mode_folder"):
            st.session_state.upload_mode = "carpeta"
            st.rerun()

    with col_m3:
        if st.button("🌐 PÁGINA WEB (URL)", key="set_mode_web"):
            st.session_state.upload_mode = "web"
            st.rerun()

    # Inyectar estilos resaltados a los 3 modos
    mode_idx = 1 if st.session_state.upload_mode == "archivo" else (2 if st.session_state.upload_mode == "carpeta" else 3)
    st.markdown(f"""
    <style>
        div[data-testid="column"]:nth-child({mode_idx}) button[key^="set_mode_"] {{
            background: linear-gradient(135deg, #0284c7, #0ea5e9) !important;
            color: white !important;
            border-color: #38bdf8 !important;
            box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3) !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    files_to_process = []
    web_url_target = None
    
    st.write("")

    if st.session_state.upload_mode == "archivo":
        col_up, col_info = st.columns([2, 1])
        with col_up:
            uploaded_files = st.file_uploader("Arrastra tus archivos PDF aquí (puedes seleccionar varios)", type=["pdf"], accept_multiple_files=True)
            if uploaded_files:
                files_to_process = uploaded_files

        with col_info:
            st.markdown("<div class='glass-card' style='padding: 15px;'>", unsafe_allow_html=True)
            st.markdown("<h5 style='color: #06b6d4; margin-top:0; font-family:\"Outfit\";'>Detalles del Lote</h5>", unsafe_allow_html=True)
            if uploaded_files:
                total_size = sum(f.size for f in uploaded_files) / (1024*1024)
                st.markdown(f"""
                <p style='font-size: 13px !important; margin-bottom: 5px;'><strong>Cantidad:</strong> {len(uploaded_files)} PDF(s)</p>
                <p style='font-size: 13px !important; margin-bottom: 8px;'><strong>Tamaño:</strong> {total_size:.2f} MB</p>
                <div style='max-height: 80px; overflow-y: auto; font-size: 11px; color: #9ca3af; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 5px;'>
                    {'<br>'.join(f"• {f.name[:25]}" for f in uploaded_files)}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #9ca3af; font-style: italic; font-size: 13px !important;'>Ningún archivo cargado.</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.upload_mode == "carpeta":
        folder_path = st.text_input("Ingresa la ruta absoluta de tu carpeta de PDFs local:", placeholder="Ejemplo: C:\\Proyectos\\PDFs")
        
        if folder_path:
            if os.path.isdir(folder_path):
                pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
                if pdf_files:
                    st.success(f"✔️ Se encontraron {len(pdf_files)} archivos PDF en la carpeta.")
                    for f in pdf_files:
                        fp = os.path.join(folder_path, f)
                        sz = os.path.getsize(fp) / (1024*1024)
                        files_to_process.append({"name": f, "path": fp, "size": sz})
                    
                    st.dataframe(
                        [{"Archivo": f["name"], "Tamaño": f"{f['size']:.2f} MB"} for f in files_to_process],
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ No se encontraron archivos PDF en la carpeta especificada.")
            else:
                st.error("❌ La ruta provista no es un directorio válido.")

    elif st.session_state.upload_mode == "web":
        st.markdown("""
        <div class="glass-card" style="padding: 15px;">
            <h5 style="color: #06b6d4; margin-top:0; font-family:'Outfit';">Extractor de Páginas Web a Markdown</h5>
            <p style="font-size: 13px !important; color: #cbd5e1; margin-bottom: 10px;">Introduce cualquier URL de internet (artículo técnico, documentación, web ConTech o blog) para extraer su contenido formateado en Markdown junto con sus imágenes adjuntas.</p>
        </div>
        """, unsafe_allow_html=True)
        
        web_url_target = st.text_input("Dirección Web (URL):", placeholder="https://ejemplo.com/articulo-tecnico")

    # ----------------- FUNCIÓN EXTRACTORA DE WEB A MARKDOWN -----------------
    def convert_url_to_md(url, extract_images=True):
        if not WEB_EXTRACTOR_AVAILABLE:
            # Fallback simple usando urllib y regex nativos
            import urllib.request
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                html_content = response.read().decode('utf-8', errors='ignore')
            
            # Limpiar etiquetas bsic
            clean_text = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL)
            clean_text = re.sub(r'<style.*?>.*?</style>', '', clean_text, flags=re.DOTALL)
            title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
            title = title_match.group(1) if title_match else "Pagina_Web"
            
            # Formatear párrafos sencillos
            text = re.sub(r'<h[1-6].*?>(.*?)</h[1-6]>', r'\n\n# \1\n\n', clean_text)
            text = re.sub(r'<p.*?>(.*?)</p>', r'\n\n\1\n', text)
            text = re.sub(r'<.*?>', '', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            return title, text.strip(), {}

        # Extractor avanzado con BeautifulSoup y html2text
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extraer título principal
        page_title = soup.title.string.strip() if soup.title and soup.title.string else "Pagina_Web"
        
        # Eliminar elementos irrelevantes (nav, scripts, footer, anuncios)
        for element in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
            element.extract()

        # Configurar conversor html2text
        h2t = html2text.HTML2Text()
        h2t.ignore_links = False
        h2t.ignore_images = not extract_images
        h2t.ignore_tables = False
        h2t.body_width = 0

        markdown_body = h2t.handle(str(soup))
        
        # Extraer imágenes si está habilitado
        extracted_images = {}
        if extract_images:
            img_tags = soup.find_all('img')
            for i, img in enumerate(img_tags[:15]): # Máximo 15 imágenes clave
                src = img.get('src')
                if src:
                    full_img_url = urllib.parse.urljoin(url, src)
                    try:
                        img_resp = requests.get(full_img_url, headers=headers, timeout=5)
                        if img_resp.status_code == 200:
                            img_filename = f"image_{i+1}.png"
                            img_obj = io.BytesIO(img_resp.content)
                            from PIL import Image
                            pil_img = Image.open(img_obj)
                            extracted_images[img_filename] = pil_img
                    except Exception:
                        pass
                        
        return page_title, markdown_body, extracted_images

    # ----------------- MOTOR CONVERSOR MARKER (PDFs) -----------------
    @st.cache_resource
    def get_converter(disable_img_ext, lang, force_ocr):
        from marker.models import create_model_dict
        from marker.converters.pdf import PdfConverter
        from marker.config.parser import ConfigParser

        config_dict = {
            "output_format": "markdown",
            "disable_image_extraction": disable_img_ext,
            "force_ocr": force_ocr
        }
        if lang:
            config_dict["languages"] = lang

        config_parser = ConfigParser(config_dict)
        artifact_dict = create_model_dict()
        return PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=artifact_dict,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer()
        )

    # CONTENEDOR 3: EJECUCIÓN DE PROCESO & PIPELINE MULTI-ETAPA
    can_trigger = (files_to_process and len(files_to_process) > 0) or (st.session_state.upload_mode == "web" and web_url_target)
    
    if can_trigger:
        st.divider()
        st.markdown("<h3 style='margin-top:0; font-size:14px; color:#c084fc; font-family:\"Outfit\"; text-transform:uppercase;'>EJECUCIÓN DE PROCESO</h3>", unsafe_allow_html=True)
        
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            trigger_conversion = st.button("🚀 INICIAR PROCESAMIENTO IA", key="btn_convert_go")
            
        if trigger_conversion:
            pipeline_box = st.empty()
            progress_bar = st.progress(0)
            start_time = time.time()
            
            # FASES DEL PIPELINE MULTI-ETAPA
            stages = [
                ("📄", "Paso 1/5: Lectura de origen y extracción preliminar"),
                ("📐", "Paso 2/5: Detección de layouts, títulos y columnas"),
                ("📊", "Paso 3/5: Estructuración de tablas numéricas de edificación"),
                ("🧮", "Paso 4/5: Procesamiento de fórmulas LaTeX e imágenes"),
                ("📦", "Paso 5/5: Ensamblado final del documento Markdown (.md)")
            ]
            
            converted_results = []
            
            if st.session_state.upload_mode == "web":
                # PROCESAR PÁGINA WEB
                for idx, (icon, stage_desc) in enumerate(stages):
                    progress_bar.progress((idx + 1) / len(stages))
                    pipeline_box.markdown(f"""
                    <div class="glass-card" style="border-color: #38bdf8;">
                        <h4 style="color: #38bdf8; margin-top:0; font-family:'Outfit';">{icon} {stage_desc}</h4>
                        <p style="margin-bottom: 0;">🌐 Extrayendo datos de la URL: <code>{web_url_target}</code></p>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.3)
                    
                try:
                    title, md_content, web_imgs = convert_url_to_md(web_url_target, extract_images=not st.session_state.disable_images)
                    converted_results.append({
                        "name": f"{re.sub(r'[^a-zA-Z0-9_-]', '_', title)[:30]}.md",
                        "markdown": md_content,
                        "images": web_imgs
                    })
                except Exception as e:
                    st.error(f"Error extrayendo URL Web: {e}")
            else:
                # PROCESAR ARCHIVOS PDF (MARKER)
                try:
                    converter = get_converter(
                        st.session_state.disable_images, 
                        st.session_state.selected_lang, 
                        st.session_state.force_ocr
                    )
                    
                    total_files = len(files_to_process)
                    
                    for idx, file_item in enumerate(files_to_process):
                        file_name = file_item.name if st.session_state.upload_mode == "archivo" else file_item["name"]
                        
                        # Simulación visual fluida del pipeline por cada archivo
                        for s_idx, (icon, stage_desc) in enumerate(stages):
                            p_val = (idx + (s_idx + 1) / len(stages)) / total_files
                            progress_bar.progress(min(p_val, 1.0))
                            pipeline_box.markdown(f"""
                            <div class="glass-card" style="border-color: #3b82f6;">
                                <h4 style="color: #38bdf8; margin-top:0; font-family:'Outfit';">Documento {idx+1}/{total_files}: {file_name}</h4>
                                <p style="margin-bottom:0;">{icon} <strong>{stage_desc}</strong></p>
                            </div>
                            """, unsafe_allow_html=True)
                            if s_idx == 0:
                                if st.session_state.upload_mode == "archivo":
                                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                                        tmp_file.write(file_item.read())
                                        input_path = tmp_file.name
                                else:
                                    input_path = file_item["path"]

                        # Conversión real con Marker
                        rendered = converter(input_path)
                        from marker.output import text_from_rendered
                        markdown_text, _, extracted_images = text_from_rendered(rendered)
                        
                        if st.session_state.upload_mode == "archivo":
                            converted_results.append({
                                "name": file_name,
                                "markdown": markdown_text,
                                "images": extracted_images
                            })
                            try:
                                os.unlink(input_path)
                            except Exception:
                                pass
                        else:
                            base_path = os.path.splitext(file_item["path"])[0]
                            md_output_path = f"{base_path}.md"
                            with open(md_output_path, "w", encoding="utf-8") as f:
                                f.write(markdown_text)
                                
                            if extracted_images and not st.session_state.disable_images:
                                img_dir = f"{base_path}_images"
                                os.makedirs(img_dir, exist_ok=True)
                                for img_name, img_obj in extracted_images.items():
                                    img_obj.save(os.path.join(img_dir, img_name))
                                    
                            converted_results.append({
                                "name": file_name,
                                "markdown": markdown_text,
                                "images": extracted_images,
                                "saved_at": md_output_path
                            })

                except Exception as e:
                    st.error("Error durante el procesamiento del lote con Marker:")
                    st.code(str(e))

            elapsed_time = time.time() - start_time
            progress_bar.progress(1.0)
            pipeline_box.empty()
            
            # ----------------- INSPECTOR SPLIT-VIEW & MÉTRICAS -----------------
            if converted_results:
                st.markdown("""
                <div style="background: rgba(74, 222, 128, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #4ade80; margin-bottom: 20px;">
                  <h4 style="color: #4ade80; margin-top:0; font-family:'Outfit';">🎉 Procesamiento Completado</h4>
                  <p style="margin-bottom:0; font-size:13px !important;">El documento/lote ha sido analizado y transformado con éxito.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # METRIC CARDS
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                total_words = sum(len(res.get("markdown", "").split()) for res in converted_results)
                total_imgs = sum(len(res.get("images", {})) for res in converted_results if res.get("images"))
                
                with m_col1:
                    st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(converted_results)}</div><div class='metric-label'>Documentos</div></div>", unsafe_allow_html=True)
                with m_col2:
                    st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_words:,}</div><div class='metric-label'>Palabras</div></div>", unsafe_allow_html=True)
                with m_col3:
                    st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_imgs}</div><div class='metric-label'>Imágenes</div></div>", unsafe_allow_html=True)
                with m_col4:
                    st.markdown(f"<div class='metric-card'><div class='metric-value'>{elapsed_time:.1f}s</div><div class='metric-label'>Tiempo Total</div></div>", unsafe_allow_html=True)
                
                st.write("")
                
                # BOTONES DE DESCARGA / GUARDADO
                if st.session_state.upload_mode in ["archivo", "web"]:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        for result in converted_results:
                            base_n = os.path.splitext(result["name"])[0]
                            zip_file.writestr(f"{base_n}.md", result["markdown"].encode("utf-8"))
                            
                            if result.get("images") and not st.session_state.disable_images:
                                for img_n, img_obj in result["images"].items():
                                    img_byte_arr = io.BytesIO()
                                    img_obj.save(img_byte_arr, format="PNG")
                                    zip_file.writestr(f"{base_n}_images/{img_n}", img_byte_arr.getvalue())
                                    
                    st.download_button(
                        label="📥 Descargar archivo(s) convertidos (.zip)",
                        data=zip_buffer.getvalue(),
                        file_name="resultado_conversion.zip",
                        mime="application/zip"
                    )
                else:
                    for item in converted_results:
                        if "saved_at" in item:
                            st.markdown(f"✔️ **{item['name']}** guardado directamente en: `{os.path.basename(item['saved_at'])}`")

                # INSPECTOR INTERACTIVO (SPLIT-VIEW)
                st.markdown("<h4 style='color:#38bdf8; font-family:\"Outfit\"; margin-top:20px;'>🔍 Inspector y Previsualizador de Resultados</h4>", unsafe_allow_html=True)
                
                insp_tab1, insp_tab2 = st.tabs(["👁️ Vista Previa Formateada", "📝 Código Fuente Markdown"])
                
                first_md = converted_results[0].get("markdown", "")
                
                with insp_tab1:
                    st.markdown("<div class='glass-card' style='max-height: 400px; overflow-y: auto;'>", unsafe_allow_html=True)
                    st.markdown(first_md, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                with insp_tab2:
                    st.code(first_md, language="markdown")
                    
                    # Botón para copiar al portapapeles instantáneo
                    b64_md = base64.b64encode(first_md.encode()).decode()
                    st.markdown(f"""
                    <button onclick="navigator.clipboard.writeText(atob('{b64_md}')); alert('¡Markdown copiado al portapapeles!');" style="background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; color: white; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-family: 'Outfit'; font-weight: 600;">
                        📋 Copiar Markdown al Portapapeles
                    </button>
                    """, unsafe_allow_html=True)

# PESTAÑA 2: AJUSTES DE IA
elif st.session_state.active_tab == "AJUSTES DE IA":
    st.markdown("<h3 style='margin-top:0;'>⚙️ Ajustes de Procesamiento</h3>", unsafe_allow_html=True)
    
    lang_dict = {
        "Español": "es",
        "Inglés": "en",
        "Español + Inglés": "es,en",
        "Francés": "fr",
        "Alemán": "de",
        "Italiano": "it",
        "Portugués": "pt",
        "Autodetectar": ""
    }
    
    lang_keys = list(lang_dict.keys())
    current_lang_name = "Español"
    for k, v in lang_dict.items():
        if v == st.session_state.selected_lang:
            current_lang_name = k
            break
            
    selected_lang_name = st.selectbox(
        "Idioma del Documento", 
        lang_keys, 
        index=lang_keys.index(current_lang_name),
        key="config_lang_select"
    )
    st.session_state.selected_lang = lang_dict[selected_lang_name]

    st.session_state.disable_images = st.checkbox(
        "Desactivar extracción de imágenes", 
        value=st.session_state.disable_images,
        help="Acelera el proceso al no procesar ni guardar figuras o fotos.",
        key="config_disable_images"
    )
    
    st.session_state.force_ocr = st.checkbox(
        "Forzar procesamiento OCR completo", 
        value=st.session_state.force_ocr,
        help="Fuerza al motor a procesar cada página como una imagen independiente. Útil en PDFs escaneados de baja calidad.",
        key="config_force_ocr"
    )

    st.divider()

    # OPCIONES DE MEMORIA DEL SERVIDOR
    st.markdown("<h4 style='color: #06b6d4; margin-top:0; font-family:\"Outfit\";'>⚙️ Opciones de Memoria del Servidor</h4>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='font-size:13px; color:#9ca3af; margin-bottom: 15px; text-align: justify;'>
        Cuando realizas conversiones, el sistema carga los pesos de los modelos de inteligencia artificial en la memoria RAM/VRAM para acelerar el procesamiento de futuros PDFs.
    </div>
    """, unsafe_allow_html=True)
    
    if "show_clear_confirm" not in st.session_state:
        st.session_state.show_clear_confirm = False
        
    if not st.session_state.show_clear_confirm:
        if st.button("🧹 LIMPIAR CACHÉ DE IA"):
            st.session_state.show_clear_confirm = True
            st.rerun()
    else:
        st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
            <p style="margin: 0; color: #f87171; font-weight: bold; font-size: 14px;">⚠️ ¿Estás seguro de que deseas limpiar la caché de la IA?</p>
            <p style="margin: 5px 0 0 0; color: #fca5a5; font-size: 13px;">Esta acción eliminará todos los modelos de la memoria de tu tarjeta gráfica y memoria RAM. Tendrán que volver a cargarse en la siguiente conversión.</p>
        </div>
        """, unsafe_allow_html=True)
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Sí, limpiar caché", key="btn_clear_yes"):
                st.cache_resource.clear()
                st.cache_data.clear()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                st.session_state.show_clear_confirm = False
                st.success("✔️ Caché RAM/VRAM liberada correctamente.")
                time.sleep(1)
                st.rerun()
        with col_no:
            if st.button("Cancelar", key="btn_clear_no"):
                st.session_state.show_clear_confirm = False
                st.rerun()

# PESTAÑA 3: REQUISITOS
elif st.session_state.active_tab == "REQUISITOS":
    st.markdown("<h3 style='margin-top:0; font-family:\"Outfit\";'>💻 Estado del Acelerador Gráfico (CUDA)</h3>", unsafe_allow_html=True)
    
    cuda_status_str = "🟢 ACTIVA (Acelerada por GPU)" if torch.cuda.is_available() else "🔴 INACTIVA (Usando CPU)"
    pytorch_ver = torch.__version__
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        mem_allocated = torch.cuda.memory_allocated(0) / (1024**2)
        mem_cached = torch.cuda.memory_reserved(0) / (1024**2)
        vram_str = f"{mem_allocated:.1f} MB (Reservada en caché: {mem_cached:.1f} MB)"
    else:
        gpu_name = "No disponible / CPU"
        vram_str = "N/A"

    st.markdown(f"""
    <table style='width:100%; border-collapse: collapse; font-size: 14px;'>
        <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
            <td style='padding:12px 0; font-weight:bold; color:#3b82f6; width:35%;'>Concepto</td>
            <td style='padding:12px 0; font-weight:bold; color:#3b82f6;'>Valor Detectado / Estado</td>
        </tr>
        <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
            <td style='padding:12px 0; color:#9ca3af;'>Aceleración CUDA</td>
            <td style='padding:12px 0; font-weight:bold;'>{cuda_status_str}</td>
        </tr>
        <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
            <td style='padding:12px 0; color:#9ca3af;'>Modelo de Gráfica</td>
            <td style='padding:12px 0;'>{gpu_name}</td>
        </tr>
        <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
            <td style='padding:12px 0; color:#9ca3af;'>Uso de Memoria VRAM</td>
            <td style='padding:12px 0;'>{vram_str}</td>
        </tr>
        <tr>
            <td style='padding:12px 0; color:#9ca3af;'>Versión PyTorch (CUDA)</td>
            <td style='padding:12px 0;'>{pytorch_ver}</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("<h3 style='margin-top:0; font-family:\"Outfit\";'>📊 Diagnóstico del Sistema</h3>", unsafe_allow_html=True)
    st.write("Verifica la compatibilidad de tu máquina para una ejecución fluida.")
    st.write("")

    if st.button("🔍 CHEQUEAR REQUISITOS DEL SISTEMA", key="btn_check_reqs"):
        st.write("---")
        
        py_ver = sys.version.split()[0]
        import platform
        os_platform = f"{platform.system()} {platform.release()}"
        
        cache_size = "0.00 GB"
        if os.path.exists(MODELS_CACHE_DIR):
            total_bytes = 0
            for root, dirs, files in os.walk(MODELS_CACHE_DIR):
                for f in files:
                    total_bytes += os.path.getsize(os.path.join(root, f))
            cache_size = f"{total_bytes / (1024**3):.2f} GB"

        st.markdown("<h4 style='color:#3b82f6; font-family:\"Outfit\";'>1. Entorno de Ejecución</h4>", unsafe_allow_html=True)
        st.markdown(f"""
        <table style='width:100%; border-collapse: collapse; font-size: 14px;'>
            <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
                <td style='padding:10px 0; font-weight:bold; width:35%;'>Requisito</td>
                <td style='padding:10px 0; font-weight:bold;'>Detalle Detectado</td>
                <td style='padding:10px 0; font-weight:bold; text-align:right;'>Estado</td>
            </tr>
            <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
                <td style='padding:10px 0; color:#9ca3af;'>Sistema Operativo</td>
                <td style='padding:10px 0;'>{os_platform}</td>
                <td style='padding:10px 0; text-align:right; color:#4ade80;'>✔️ Compatible</td>
            </tr>
            <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
                <td style='padding:10px 0; color:#9ca3af;'>Intérprete Python</td>
                <td style='padding:10px 0;'>Versión {py_ver}</td>
                <td style='padding:10px 0; text-align:right; color:#4ade80;'>✔️ Compatible</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("<h4 style='color:#3b82f6; font-family:\"Outfit\"; margin-top:20px;'>2. Almacenamiento y Caché Local</h4>", unsafe_allow_html=True)
        st.markdown(f"""
        <table style='width:100%; border-collapse: collapse; font-size: 14px;'>
            <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
                <td style='padding:10px 0; font-weight:bold; width:35%;'>Directorio</td>
                <td style='padding:10px 0; font-weight:bold;'>Ruta / Tamaño</td>
                <td style='padding:10px 0; font-weight:bold; text-align:right;'>Estado</td>
            </tr>
            <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
                <td style='padding:10px 0; color:#9ca3af;'>Caché Modelos local</td>
                <td style='padding:10px 0;'><code>pdf_to_md/models_cache</code></td>
                <td style='padding:10px 0; text-align:right; color:#4ade80;'>✔️ Configurada</td>
            </tr>
            <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
                <td style='padding:10px 0; color:#9ca3af;'>Peso en disco</td>
                <td style='padding:10px 0;'>{cache_size} descargados</td>
                <td style='padding:10px 0; text-align:right; color:#4ade80;'>✔️ Disponible</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("<h3 style='margin-top:0; font-family:\"Outfit\";'>🚀 Guía de Instalación y Compartición</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <table style='width:100%; border-collapse: collapse; margin-top: 15px;'>
      <tr style='background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;'>
        <td style='padding: 15px; width: 60px; text-align: center; vertical-align: middle; font-size: 24px;'>1️⃣</td>
        <td style='padding: 15px; vertical-align: top; text-align: justify;'>
          <strong style='color:#3b82f6; font-size: 15px; font-family: "Outfit";'>Empaquetar el proyecto</strong><br>
          <span style='color: #9ca3af; font-size: 13px; line-height: 1.5;'>Comprime la carpeta del proyecto <code>pdf_to_md</code> en un archivo ZIP sin incluir las carpetas <code>.venv</code> ni <code>models_cache</code>.</span>
        </td>
      </tr>
      <tr style='height: 10px;'></tr>
      <tr style='background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;'>
        <td style='padding: 15px; width: 60px; text-align: center; vertical-align: middle; font-size: 24px;'>2️⃣</td>
        <td style='padding: 15px; vertical-align: top; text-align: justify;'>
          <strong style='color:#3b82f6; font-size: 15px; font-family: "Outfit";'>Desplegar en el destino</strong><br>
          <span style='color: #9ca3af; font-size: 13px; line-height: 1.5;'>Extraer el archivo ZIP y ejecutar <code>setup_and_run.bat</code>.</span>
        </td>
      </tr>
      <tr style='height: 10px;'></tr>
      <tr style='background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;'>
        <td style='padding: 15px; width: 60px; text-align: center; vertical-align: middle; font-size: 24px;'>3️⃣</td>
        <td style='padding: 15px; vertical-align: top; text-align: justify;'>
          <strong style='color:#3b82f6; font-size: 15px; font-family: "Outfit";'>Autoconfiguración local</strong><br>
          <span style='color: #9ca3af; font-size: 13px; line-height: 1.5;'>El script analiza el hardware local e instala las versiones adecuadas de PyTorch y CUDA.</span>
        </td>
      </tr>
    </table>
    """, unsafe_allow_html=True)

# PESTAÑA 4: AUTOR
elif st.session_state.active_tab == "AUTOR":
    col_pic, col_desc = st.columns([1, 2])
    
    with col_pic:
        gif_file = "yo_animado.gif"
        if os.path.exists(gif_file):
            try:
                base64_gif = get_base64_image(gif_file)
                st.markdown(f"""
                <div style='text-align: center;'>
                    <a href='https://jmcaamanog.pages.dev/' target='_blank'>
                        <img src='{base64_gif}' style='width: 180px; height: 180px; border-radius: 50%; border: 3px solid #3b82f6; box-shadow: 0 4px 15px rgba(59,130,246,0.45); object-fit: cover; transition: all 0.3s ease-in-out; cursor: pointer;' onmouseover='this.style.transform="scale(1.06)"' onmouseout='this.style.transform="scale(1)"' title="Visitar mi Web" />
                    </a>
                    <p style='margin-top: 15px; font-weight: bold; font-family: "Outfit"; font-size: 18px; color:#ffffff; margin-bottom: 0;'>José Manuel Caamaño González</p>
                    <p style='color: #9ca3af; font-size: 12px; margin-top: 2px;'>A Coruña (Galicia)</p>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error("Error al cargar la foto de perfil.")
        else:
            st.markdown("""
            <div style='text-align: center;'>
                <a href='https://jmcaamanog.pages.dev/' target='_blank' style='text-decoration: none;'>
                    <div style='background: linear-gradient(135deg, #3b82f6, #06b6d4); width: 150px; height: 150px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; box-shadow: 0 4px 15px rgba(59,130,246,0.35); cursor: pointer;' onmouseover='this.style.transform="scale(1.05)"' onmouseout='this.style.transform="scale(1)"'>
                        <span style='font-size: 52px;'>👤</span>
                    </div>
                </a>
                <p style='margin-top: 15px; font-weight: bold; font-family: "Outfit"; font-size: 18px; color:#ffffff;'>José Manuel Caamaño González</p>
                <p style='color: #9ca3af; font-size: 12px; margin-top: -10px;'>A Coruña (Galicia)</p>
            </div>
            """, unsafe_allow_html=True)
        
    with col_desc:
        st.markdown("<h3 style='margin-top:0; font-family:\"Outfit\"; color:#3b82f6;'>Arquitecto Técnico & ConTech Developer</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-size: 14px; text-align: justify; line-height: 1.6;'>
            ¡Hola! Soy Jose Manuel Caamaño, Arquitecto técnico ConTech!👋<br>
            <strong>Digital Product Lead | ConTech & Digital Twin SaaS | BIM, Energy Modeling & Sustainability | Data Analytics (SQL, Power BI)</strong>
            <br><br>
            Arquitecto Técnico y BIM Manager operando desde la trinchera en A Coruña. ☕ Me dedico a construir puentes entre la construcción tradicional (sector AECO) y el ecosistema digital. Si algo se puede automatizar, auditar o visualizar en 3D, probablemente ya esté escribiendo un script en Python para hacerlo.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="margin-top: 20px; display: flex; gap: 10px; text-align: left;">
          <a href="https://github.com/jmcaamanog" target="_blank" style="text-decoration: none; display: inline-flex; align-items: center; gap: 10px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 10px 20px; color: #ffffff; font-family: 'Outfit', sans-serif; font-weight: 600; font-size: 14px; transition: all 0.3s ease;">
            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24" style="vertical-align: middle;">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span>GitHub</span>
          </a>
          <a href="https://www.linkedin.com/in/jmcaamanog/" target="_blank" style="text-decoration: none; display: inline-flex; align-items: center; gap: 10px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 10px 20px; color: #ffffff; font-family: 'Outfit', sans-serif; font-weight: 600; font-size: 14px; transition: all 0.3s ease;">
            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24" style="vertical-align: middle;">
              <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.779-1.75-1.75s.784-1.75 1.75-1.75 1.75.779 1.75 1.75-.784 1.75-1.75 1.75zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
            </svg>
            <span>LinkedIn</span>
          </a>
        </div>
        """, unsafe_allow_html=True)
