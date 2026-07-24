import os
import sys
import io
import time
import zipfile
import tempfile
import base64
import re
import difflib
import urllib.parse
import torch
import streamlit as st

# Intentar importación de librerías para scraping web, excel y dataframes
try:
    import requests
    from bs4 import BeautifulSoup
    import html2text
    WEB_EXTRACTOR_AVAILABLE = True
except ImportError:
    WEB_EXTRACTOR_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Configurar ruta local de caché de modelos ANTES de cualquier importación de marker/transformers
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_CACHE_DIR = os.path.join(CURRENT_DIR, "models_cache")
os.makedirs(MODELS_CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = MODELS_CACHE_DIR
os.environ["TORCH_HOME"] = MODELS_CACHE_DIR
os.environ["MARKER_HOME"] = MODELS_CACHE_DIR
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
    st.session_state.active_preset = "contech"
if "last_results" not in st.session_state:
    st.session_state.last_results = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Estilos CSS personalizados (Glassmorphic Acrílico + Fluent Design)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

    header[data-testid="stHeader"] { display: none !important; }
    footer { visibility: hidden !important; }

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
    
    h1, h2, h3, h4, .title-display {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700;
        text-transform: uppercase !important;
        background: linear-gradient(135deg, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    hr {
        border: 0 !important;
        height: 1px !important;
        background: rgba(255, 255, 255, 0.08) !important;
        margin-top: 20px !important;
        margin-bottom: 20px !important;
    }

    p, span, li, td, th, table, label, div.stMarkdown p {
        font-size: 15px !important;
        line-height: 1.7 !important;
    }
    
    div[data-testid="column"] button {
        height: 48px !important;
        border-radius: 10px !important;
        background-color: rgba(17, 24, 39, 0.4) !important;
        color: #9ca3af !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        font-weight: 700 !important;
        font-size: 12px !important;
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

    .stButton>button {
        background: linear-gradient(135deg, #3b82f6, #06b6d4) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 12px 25px !important;
        font-family: 'Outfit', sans-serif;
        font-size: 15px;
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

# Helper para parsear rangos de páginas (ej. "1-5, 10, 12-15")
def parse_page_range(range_str):
    if not range_str or not range_str.strip():
        return None
    pages = set()
    parts = range_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            sub = part.split('-')
            if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                start, end = int(sub[0]), int(sub[1])
                for p in range(start, end + 1):
                    if p > 0: pages.add(p - 1)
        elif part.isdigit():
            p = int(part)
            if p > 0: pages.add(p - 1)
    return sorted(list(pages)) if pages else None

# Helper para formatear para Obsidian Vault
def format_for_obsidian(md_text, title="Documento_Tecnico"):
    clean_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', title).replace('.pdf', '')
    frontmatter = f"""---
title: "{clean_title}"
date: "{time.strftime('%Y-%m-%d')}"
tags:
  - ConTech
  - AECO
  - Presupuestos
  - Documentacion
source: "PDF to .MD by jmcaamanog"
---

# {clean_title}

"""
    # Convertir cabeceras en wikilinks conceptuales
    obsidian_body = re.sub(r'^(##+)\s+(.*)$', r'\1 [[ \2 ]]', md_text, flags=re.MULTILINE)
    return frontmatter + obsidian_body

# Helper para extraer tablas Markdown a archivo Excel (.xlsx)
def extract_tables_to_excel(md_text):
    if not PANDAS_AVAILABLE:
        return None
        
    lines = md_text.split('\n')
    tables = []
    current_table = []
    
    for line in lines:
        if '|' in line:
            current_table.append(line)
        else:
            if len(current_table) >= 2:
                tables.append('\n'.join(current_table))
            current_table = []
    if len(current_table) >= 2:
        tables.append('\n'.join(current_table))
        
    if not tables:
        return None
        
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        for idx, table_md in enumerate(tables):
            try:
                # Convertir tabla Markdown a DataFrame
                rows = [row.strip().split('|')[1:-1] for row in table_md.strip().split('\n')]
                if len(rows) >= 2:
                    headers = [h.strip() for h in rows[0]]
                    data = [[cell.strip() for cell in r] for r in rows[2:]] # Ignorar separador |---|
                    df = pd.DataFrame(data, columns=headers)
                    sheet_name = f"Tabla_{idx+1}"[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception:
                pass
                
    excel_buffer.seek(0)
    return excel_buffer.getvalue() if tables else None

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
        <span>{hw_status_html} &nbsp;|&nbsp; 📁 Caché Local: <code>./models_cache</code></span>
    </div>
    """, unsafe_allow_html=True)

with col_hw2:
    if st.button("🧹 PURGAR VRAM", key="quick_vram_purge", help="Libera la memoria gráfica y caché del proyecto"):
        st.cache_resource.clear()
        st.cache_data.clear()
        if cuda_available:
            torch.cuda.empty_cache()
        st.success("VRAM Purgada")
        time.sleep(0.8)
        st.rerun()

# ----------------- BARRA DE NAVEGACIÓN EN PESTAÑAS -----------------
col_t1, col_t2, col_t3, col_t4, col_t5, col_t6, col_t7 = st.columns(7)

tabs = [
    ("INTRO", col_t1, "nav_intro"),
    ("CONVERTIR", col_t2, "nav_convert"),
    ("CHAT IA", col_t3, "nav_chat"),
    ("DIFF REVISIONES", col_t4, "nav_diff"),
    ("AJUSTES DE IA", col_t5, "nav_config"),
    ("REQUISITOS", col_t6, "nav_reqs"),
    ("AUTOR", col_t7, "nav_about")
]

for tab_name, col_obj, tab_key in tabs:
    with col_obj:
        if st.button(tab_name, use_container_width=True, key=tab_key):
            st.session_state.active_tab = tab_name
            st.rerun()

active_child = 1
for idx, (t_name, _, _) in enumerate(tabs):
    if st.session_state.active_tab == t_name:
        active_child = idx + 1
        break

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
            <div>🌐 <strong>Ingesta de Páginas Web:</strong> Extracción directa de URLs a Markdown con fotos</div>
            <div>🚀 <strong>Exportador para Obsidian:</strong> Salida con Frontmatter YAML y wikilinks</div>
            <div>📊 <strong>Exportador Excel (.xlsx):</strong> Volcado automático de tablas a libros Excel</div>
            <div>🔍 <strong>Filtro de Rango de Páginas:</strong> Selecciona solo las páginas que necesitas</div>
            <div>💬 <strong>Chat IA Offline:</strong> Realiza preguntas y resúmenes sobre tus documentos</div>
            <div>🔀 <strong>Comparador de Revisiones:</strong> Diferencias en paralelo entre Rev A vs Rev B</div>
            <div>🐳 <strong>Soporte Docker Integrado:</strong> Contenedor aislado para cero impacto en disco</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="border-left: 4px solid #3b82f6; background: rgba(59, 130, 246, 0.04); padding: 16px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
        <span style="font-size:13px; line-height: 1.6; color: #d1d5db;">
            🔧 <strong>Herramienta ConTech de Código Abierto:</strong> Creado por <strong>Jose Manuel Caamaño</strong> para la comunidad de la Arquitectura Técnica (<strong>COATAC</strong>) y el sector AECO.
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
    
    st.markdown("<h3 style='margin-top:0; font-size:14px; color:#3b82f6; font-family:\"Outfit\"; text-transform:uppercase;'>PERFIL / PRESET RÁPIDO DE IA</h3>", unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        if st.button("⚡ Modo Rápido (Sin Fotos)", key="p_rapido"):
            st.session_state.active_preset = "rapido"
            st.session_state.disable_images = True
            st.session_state.force_ocr = False
            st.rerun()
            
    with col_p2:
        if st.button("🏗️ Modo ConTech (Tablas & Fotos)", key="p_contech"):
            st.session_state.active_preset = "contech"
            st.session_state.disable_images = False
            st.session_state.force_ocr = False
            st.rerun()
            
    with col_p3:
        if st.button("🧮 Modo OCR & LaTeX Profundo", key="p_ocr"):
            st.session_state.active_preset = "ocr"
            st.session_state.disable_images = False
            st.session_state.force_ocr = True
            st.rerun()

    st.divider()

    st.markdown("<h3 style='margin-top:0; font-size:14px; color:#3b82f6; font-family:\"Outfit\"; text-transform:uppercase;'>ORIGEN DE DATOS & FILTROS</h3>", unsafe_allow_html=True)
    
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

    files_to_process = []
    web_url_target = None
    page_range_filter = None
    
    st.write("")

    if st.session_state.upload_mode == "archivo":
        col_up, col_info = st.columns([2, 1])
        with col_up:
            uploaded_files = st.file_uploader("Arrastra tus archivos PDF aquí (puedes seleccionar varios)", type=["pdf"], accept_multiple_files=True)
            if uploaded_files:
                files_to_process = uploaded_files
            
            page_range_str = st.text_input("🔍 Convertir solo páginas específicas (Opcional):", placeholder="Ejemplo: 1-5, 10, 15-20 (deja vacío para todo el PDF)")
            page_range_filter = parse_page_range(page_range_str)

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
        page_range_str = st.text_input("🔍 Convertir solo páginas específicas (Opcional):", placeholder="Ejemplo: 1-5, 10")
        page_range_filter = parse_page_range(page_range_str)
        
        if folder_path and os.path.isdir(folder_path):
            pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
            if pdf_files:
                st.success(f"✔️ Se encontraron {len(pdf_files)} archivos PDF en la carpeta.")
                for f in pdf_files:
                    fp = os.path.join(folder_path, f)
                    sz = os.path.getsize(fp) / (1024*1024)
                    files_to_process.append({"name": f, "path": fp, "size": sz})

    elif st.session_state.upload_mode == "web":
        web_url_target = st.text_input("Dirección Web (URL):", placeholder="https://ejemplo.com/articulo-tecnico")

    def convert_url_to_md(url, extract_images=True):
        if not WEB_EXTRACTOR_AVAILABLE:
            import urllib.request
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                html_content = response.read().decode('utf-8', errors='ignore')
            title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
            title = title_match.group(1) if title_match else "Pagina_Web"
            text = re.sub(r'<.*?>', '', html_content)
            return title, text.strip(), {}

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        page_title = soup.title.string.strip() if soup.title and soup.title.string else "Pagina_Web"
        
        for element in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            element.extract()

        h2t = html2text.HTML2Text()
        h2t.ignore_links = False
        h2t.ignore_images = not extract_images
        h2t.ignore_tables = False
        markdown_body = h2t.handle(str(soup))
        
        extracted_images = {}
        if extract_images:
            img_tags = soup.find_all('img')
            for i, img in enumerate(img_tags[:10]):
                src = img.get('src')
                if src:
                    full_img_url = urllib.parse.urljoin(url, src)
                    try:
                        img_resp = requests.get(full_img_url, headers=headers, timeout=5)
                        if img_resp.status_code == 200:
                            from PIL import Image
                            pil_img = Image.open(io.BytesIO(img_resp.content))
                            extracted_images[f"image_{i+1}.png"] = pil_img
                    except Exception:
                        pass
                        
        return page_title, markdown_body, extracted_images

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

    can_trigger = (files_to_process and len(files_to_process) > 0) or (st.session_state.upload_mode == "web" and web_url_target)
    
    if can_trigger:
        st.divider()
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            trigger_conversion = st.button("🚀 INICIAR PROCESAMIENTO IA", key="btn_convert_go")
            
        if trigger_conversion:
            pipeline_box = st.empty()
            progress_bar = st.progress(0)
            start_time = time.time()
            converted_results = []
            
            if st.session_state.upload_mode == "web":
                progress_bar.progress(0.5)
                pipeline_box.markdown(f"<div class='glass-card'>🌐 Extrayendo datos de: <code>{web_url_target}</code></div>", unsafe_allow_html=True)
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
                try:
                    converter = get_converter(st.session_state.disable_images, st.session_state.selected_lang, st.session_state.force_ocr)
                    total_files = len(files_to_process)
                    
                    for idx, file_item in enumerate(files_to_process):
                        file_name = file_item.name if st.session_state.upload_mode == "archivo" else file_item["name"]
                        progress_bar.progress((idx + 0.5) / total_files)
                        pipeline_box.markdown(f"<div class='glass-card'>📄 Procesando {idx+1}/{total_files}: {file_name}</div>", unsafe_allow_html=True)
                        
                        if st.session_state.upload_mode == "archivo":
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                                tmp_file.write(file_item.read())
                                input_path = tmp_file.name
                        else:
                            input_path = file_item["path"]

                        rendered = converter(input_path, page_range=page_range_filter) if page_range_filter else converter(input_path)
                        from marker.output import text_from_rendered
                        markdown_text, _, extracted_images = text_from_rendered(rendered)
                        
                        converted_results.append({
                            "name": file_name,
                            "markdown": markdown_text,
                            "images": extracted_images
                        })
                        if st.session_state.upload_mode == "archivo":
                            try: os.unlink(input_path)
                            except Exception: pass

                except Exception as e:
                    st.error("Error durante el procesamiento:")
                    st.code(str(e))

            elapsed_time = time.time() - start_time
            progress_bar.progress(1.0)
            pipeline_box.empty()
            
            if converted_results:
                st.session_state.last_results = converted_results
                st.success(f"🎉 Procesamiento Completado en {elapsed_time:.1f}s")
                
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                total_words = sum(len(res.get("markdown", "").split()) for res in converted_results)
                total_imgs = sum(len(res.get("images", {})) for res in converted_results if res.get("images"))
                
                with m_col1: st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(converted_results)}</div><div class='metric-label'>Documentos</div></div>", unsafe_allow_html=True)
                with m_col2: st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_words:,}</div><div class='metric-label'>Palabras</div></div>", unsafe_allow_html=True)
                with m_col3: st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_imgs}</div><div class='metric-label'>Imágenes</div></div>", unsafe_allow_html=True)
                with m_col4: st.markdown(f"<div class='metric-card'><div class='metric-value'>{elapsed_time:.1f}s</div><div class='metric-label'>Tiempo</div></div>", unsafe_allow_html=True)
                
                st.write("")
                
                # BOTONES DE EXPORTACIÓN AVANZADOS
                exp_col1, exp_col2, exp_col3 = st.columns(3)
                
                with exp_col1:
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
                    st.download_button("📥 Descargar ZIP (.zip)", zip_buffer.getvalue(), "resultado_conversion.zip", "application/zip", use_container_width=True)

                with exp_col2:
                    obsidian_md = format_for_obsidian(converted_results[0]["markdown"], converted_results[0]["name"])
                    st.download_button("🚀 Exportar para Obsidian (.md)", obsidian_md.encode("utf-8"), f"obsidian_{converted_results[0]['name']}", "text/markdown", use_container_width=True)

                with exp_col3:
                    excel_bytes = extract_tables_to_excel(converted_results[0]["markdown"])
                    if excel_bytes:
                        st.download_button("📊 Descargar Tablas en Excel (.xlsx)", excel_bytes, "tablas_extraidas.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                    else:
                        st.button("📊 Excel (Sin Tablas)", disabled=True, use_container_width=True)

                st.markdown("<h4 style='color:#38bdf8; font-family:\"Outfit\"; margin-top:20px;'>🔍 Inspector y Previsualizador</h4>", unsafe_allow_html=True)
                insp_tab1, insp_tab2 = st.tabs(["👁️ Vista Previa Formateada", "📝 Código Fuente Markdown"])
                first_md = converted_results[0].get("markdown", "")
                
                with insp_tab1:
                    st.markdown("<div class='glass-card' style='max-height: 400px; overflow-y: auto;'>", unsafe_allow_html=True)
                    st.markdown(first_md, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                with insp_tab2:
                    st.code(first_md, language="markdown")

# PESTAÑA 2: CHAT CON DOCUMENTO
elif st.session_state.active_tab == "CHAT IA":
    st.markdown("<h3 style='margin-top:0;'>💬 Chat Asistente con tu Documento (100% Offline)</h3>", unsafe_allow_html=True)
    
    if not st.session_state.last_results:
        st.info("ℹ️ Procesa un PDF o Página Web en la pestaña CONVERTIR para empezar a realizar consultas sobre el documento.")
    else:
        doc_text = st.session_state.last_results[0].get("markdown", "")
        doc_name = st.session_state.last_results[0].get("name", "Documento")
        st.markdown(f"<div class='glass-card'>📄 <strong>Documento en Memoria:</strong> <code>{doc_name}</code> ({len(doc_text.split())} palabras)</div>", unsafe_allow_html=True)
        
        user_query = st.text_input("Haz una pregunta o consulta sobre el documento:", placeholder="Ejemplo: Resúmeme los puntos clave del documento o busca precios de partidas")
        
        if user_query:
            # Motor de búsqueda offline local e inteligente
            keywords = [w.lower() for w in user_query.split() if len(w) > 3]
            matching_lines = []
            for line in doc_text.split('\n'):
                if any(kw in line.lower() for kw in keywords):
                    matching_lines.append(line)
                    
            st.markdown("#### 🤖 Respuesta del Asistente Offline")
            if matching_lines:
                st.success(f"Se encontraron {len(matching_lines)} fragmentos relevantes en `{doc_name}`:")
                st.markdown("<div class='glass-card' style='max-height:300px; overflow-y:auto;'>", unsafe_allow_html=True)
                for line in matching_lines[:15]:
                    st.markdown(f"• {line}")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("No se encontraron coincidencias exactas para tu consulta en el texto del documento.")

# PESTAÑA 3: COMPARADOR DE REVISIONES
elif st.session_state.active_tab == "DIFF REVISIONES":
    st.markdown("<h3 style='margin-top:0;'>🔀 Comparador de Revisiones de Documentos</h3>", unsafe_allow_html=True)
    st.write("Compara dos archivos o textos de proyectos (Rev A vs Rev B) para visualizar las diferencias lado a lado.")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        rev_a = st.text_area("Documento / Texto Revisión A:", height=200, placeholder="Pega el contenido o Markdown de la Revisión A")
    with col_d2:
        rev_b = st.text_area("Documento / Texto Revisión B:", height=200, placeholder="Pega el contenido o Markdown de la Revisión B")
        
    if rev_a and rev_b:
        st.markdown("#### 📊 Resultado de la Comparativa (Diff)")
        diff = difflib.HtmlDiff().make_file(rev_a.splitlines(), rev_b.splitlines(), fromdesc="Revisión A", todesc="Revisión B")
        st.components.v1.html(diff, height=400, scrolling=True)

# PESTAÑA 4: AJUSTES DE IA
elif st.session_state.active_tab == "AJUSTES DE IA":
    st.markdown("<h3 style='margin-top:0;'>⚙️ Ajustes de Procesamiento</h3>", unsafe_allow_html=True)
    
    st.session_state.disable_images = st.checkbox("Desactivar extracción de imágenes", value=st.session_state.disable_images)
    st.session_state.force_ocr = st.checkbox("Forzar procesamiento OCR completo", value=st.session_state.force_ocr)

    st.divider()
    st.markdown("<h4 style='color: #06b6d4; margin-top:0; font-family:\"Outfit\";'>⚙️ Opciones de Memoria del Servidor</h4>", unsafe_allow_html=True)
    
    if st.button("🧹 LIMPIAR CACHÉ DE IA"):
        st.cache_resource.clear()
        st.cache_data.clear()
        if torch.cuda.is_available(): torch.cuda.empty_cache()
        st.success("✔️ Caché RAM/VRAM liberada correctamente.")

# PESTAÑA 5: REQUISITOS
elif st.session_state.active_tab == "REQUISITOS":
    st.markdown("<h3 style='margin-top:0; font-family:\"Outfit\";'>💻 Estado del Acelerador Gráfico (CUDA) & Docker</h3>", unsafe_allow_html=True)
    
    cuda_status_str = "🟢 ACTIVA (Acelerada por GPU)" if torch.cuda.is_available() else "🔴 INACTIVA (Usando CPU)"
    st.markdown(f"""
    <table style='width:100%; border-collapse: collapse; font-size: 14px;'>
        <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
            <td style='padding:10px 0; font-weight:bold; color:#3b82f6; width:35%;'>Aceleración CUDA</td>
            <td style='padding:10px 0; font-weight:bold;'>{cuda_status_str}</td>
        </tr>
        <tr style='border-bottom:1px solid rgba(255,255,255,0.05);'>
            <td style='padding:10px 0; color:#9ca3af;'>Directorio de Caché de Modelos</td>
            <td style='padding:10px 0;'><code>./models_cache</code> (En la carpeta del proyecto)</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

# PESTAÑA 6: AUTOR
elif st.session_state.active_tab == "AUTOR":
    col_pic, col_desc = st.columns([1, 2])
    with col_pic:
        gif_file = "yo_animado.gif"
        if os.path.exists(gif_file):
            base64_gif = get_base64_image(gif_file)
            st.markdown(f"<div style='text-align: center;'><img src='{base64_gif}' style='width: 180px; height: 180px; border-radius: 50%; border: 3px solid #3b82f6;' /><p style='font-weight: bold; margin-top:10px;'>José Manuel Caamaño González</p></div>", unsafe_allow_html=True)
    with col_desc:
        st.markdown("<h3 style='margin-top:0; color:#3b82f6;'>Arquitecto Técnico & ConTech Developer</h3>", unsafe_allow_html=True)
        st.write("Arquitecto Técnico y BIM Manager operando desde A Coruña. ☕")
        st.markdown("[LinkedIn](https://www.linkedin.com/in/jmcaamanog/) | [GitHub](https://github.com/jmcaamanog)")
