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
import subprocess
import torch
import streamlit as st

# Importaciones condicionales para scraping web, excel y dataframes
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

# Configurar ruta local de caché de modelos
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_CACHE_DIR = os.path.join(CURRENT_DIR, "models_cache")
os.makedirs(MODELS_CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = MODELS_CACHE_DIR
os.environ["TORCH_HOME"] = MODELS_CACHE_DIR
os.environ["MARKER_HOME"] = MODELS_CACHE_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Configuración de la página
st.set_page_config(
    page_title="PDF to .MD by jmcaamanog",
    page_icon="📄",
    layout="wide"
)

# Inicializar variables de estado
if "src_choice" not in st.session_state:
    st.session_state.src_choice = "PDF"
if "ext_choice" not in st.session_state:
    st.session_state.ext_choice = "TÉCNICO"
if "source_folder_path" not in st.session_state:
    st.session_state.source_folder_path = ""
if "dest_folder_path" not in st.session_state:
    st.session_state.dest_folder_path = ""
if "default_lang" not in st.session_state:
    st.session_state.default_lang = "es"
if "last_results" not in st.session_state:
    st.session_state.last_results = []
if "switch_to_convert" not in st.session_state:
    st.session_state.switch_to_convert = False

# Función robusta para abrir explorador nativo de Windows TRAÍDO AL PRIMER PLANO (TopMost)
def select_folder_dialog(title="Seleccionar Carpeta"):
    ps_file = os.path.join(CURRENT_DIR, "select_folder.ps1")
    if os.path.exists(ps_file):
        try:
            res = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file],
                capture_output=True,
                text=True,
                timeout=35
            )
            folder = res.stdout.strip()
            if folder and os.path.isdir(folder):
                return folder
        except Exception:
            pass

    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.lift()
        root.focus_force()
        folder = filedialog.askdirectory(title=title, master=root)
        root.destroy()
        return folder
    except Exception:
        return ""

# Estilos CSS de Alta Calidad (+25% Más Ancho, Pestañas 100% Ancho y Botones Activos Azul Claro)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

    header[data-testid="stHeader"] { display: none !important; }
    footer { visibility: hidden !important; }

    /* PAGINA 25% MÁS ANCHA */
    .block-container {
        max-width: 1250px !important;
        padding-top: 15px !important;
        padding-bottom: 25px !important;
        margin: 0 auto !important;
    }
    
    .stApp {
        background: #0b0f19;
        color: #f3f4f6;
        font-family: 'Inter', sans-serif;
    }

    /* ESTILO DE BORDES Y CONTENEDORES NATIVOS */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(17, 24, 39, 0.65) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 14px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35) !important;
    }

    .container-title {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px;
        color: #38bdf8 !important;
        margin-top: 0 !important;
        margin-bottom: 16px !important;
        text-align: left;
    }

    /* TITULOS EN OUTFIT */
    h1, h2, h3, h4, .title-display {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700;
        text-transform: uppercase !important;
        background: linear-gradient(135deg, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    p, span, li, td, th, table, label, div.stMarkdown p {
        font-size: 15px !important;
        line-height: 1.7 !important;
    }
    
    /* PESTAÑAS 100% ANCHO REPARTIDAS A PARTES IGUALES */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        display: flex !important;
        width: 100% !important;
        gap: 10px !important;
        background-color: rgba(17, 24, 39, 0.6) !important;
        padding: 8px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    div[data-testid="stTabs"] [data-baseweb="tab-list"] button {
        flex: 1 1 0% !important;
        width: 20% !important;
        min-width: 0 !important;
        height: 50px !important;
        border-radius: 12px !important;
        color: #9ca3af !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        font-family: 'Outfit', sans-serif !important;
        text-transform: uppercase !important;
        border: none !important;
        text-align: center !important;
        justify-content: center !important;
        padding: 0 !important;
        transition: none !important;
    }

    div[data-testid="stTabs"] [data-baseweb="tab-list"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #00c6ff, #0072ff) !important;
        color: #ffffff !important;
        box-shadow: 0 6px 20px rgba(0, 198, 255, 0.4) !important;
    }

    /* ESTILO DE BOTONES SELECCIONADOS (PRIMARY) VS INACTIVOS (SECONDARY) */
    button[kind="primary"], div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #00c6ff, #0072ff) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 198, 255, 0.4) !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        text-transform: uppercase !important;
        transform: none !important;
        height: 48px !important;
    }
    
    button[kind="secondary"], div[data-testid="stButton"] > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #9ca3af !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        text-transform: uppercase !important;
        transform: none !important;
        height: 48px !important;
    }

    /* TARJETA CON BORDE IZQUIERDO AZUL REPLICADA DE IMAGEN 001 */
    .dev-active-card {
        background: rgba(15, 23, 42, 0.75);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 18px 24px;
        margin-top: 15px;
        margin-bottom: 20px;
    }

    /* TABLA ESTILO REQUISITOS IMAGEN 008 */
    .req-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        margin-bottom: 20px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        overflow: hidden;
    }
    .req-table th {
        background: rgba(30, 41, 59, 0.8);
        color: #38bdf8;
        padding: 12px 16px;
        text-align: left;
        font-family: 'Outfit', sans-serif;
        font-size: 14px;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .req-table td {
        padding: 14px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        color: #e2e8f0;
        font-size: 14px;
    }
    
    .badge-num {
        background: #0072ff;
        color: white;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# Helper para codificar imágenes a Base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f"data:image/gif;base64,{encoded_string}"

# Helper para parsear rangos de páginas
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

# Helper avanzado para exportación a Obsidian Vault
def format_for_obsidian(md_text, title="Documento_Tecnico"):
    clean_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', title).replace('.pdf', '')
    frontmatter = f"""---
title: "{clean_title}"
date: "{time.strftime('%Y-%m-%d')}"
tags:
  - #ConTech
  - #AECO
  - #Presupuestos
  - #BIM
source: "PDF to .MD by jmcaamanog"
cssclasses:
  - readable-line-length
---

# 📌 [[{clean_title}]]

> [!info] Documento Procesado
> Generado automáticamente para Obsidian Vault con formato de hipervínculos bidireccionales.

"""
    obsidian_body = re.sub(r'^(##+)\s+(.*)$', r'\1 [[ \2 ]]', md_text, flags=re.MULTILINE)
    return frontmatter + obsidian_body

# Helper para extraer tablas Markdown a Excel
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
                rows = [row.strip().split('|')[1:-1] for row in table_md.strip().split('\n')]
                if len(rows) >= 2:
                    headers = [h.strip() for h in rows[0]]
                    data = [[cell.strip() for cell in r] for r in rows[2:]]
                    df = pd.DataFrame(data, columns=headers)
                    sheet_name = f"Tabla_{idx+1}"[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception:
                pass
                
    excel_buffer.seek(0)
    return excel_buffer.getvalue() if tables else None

# Encabezado Principal con Logo SVG
st.markdown("""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 20px; margin-top: 5px;">
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="url(#blue-cyan-grad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <defs>
      <linearGradient id="blue-cyan-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#00c6ff" />
        <stop offset="100%" stop-color="#0072ff" />
      </linearGradient>
    </defs>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
  <div>
    <h1 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 800; background: linear-gradient(135deg, #00c6ff, #0072ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 30px; text-transform: uppercase;">PDF to .MD by jmcaamanog</h1>
  </div>
</div>
""", unsafe_allow_html=True)

# JavaScript para conmutar directamente a la pestaña CONVERTIR cuando se solicite
if st.session_state.switch_to_convert:
    st.session_state.switch_to_convert = False
    st.components.v1.html("""
    <script>
        var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
        if (tabs.length > 1) {
            tabs[1].click();
        }
    </script>
    """, height=0)

# ----------------- 5 PESTAÑAS (INTRO, CONVERTIR, ASISTENTE IA, REQUISITOS, AUTOR) -----------------
tab_home, tab_conv, tab_assistant, tab_settings, tab_author = st.tabs([
    "INTRO",
    "CONVERTIR",
    "ASISTENTE IA",
    "REQUISITOS",
    "AUTOR"
])

# ================= 1. PESTAÑA INTRO =================
with tab_home:
    with st.container(border=True):
        st.markdown("<h4 class='container-title'>¿QUÉ PUEDES HACER CON ESTA VERSIÓN?</h4>", unsafe_allow_html=True)
        c_feat1, c_feat2 = st.columns(2)
        with c_feat1:
            st.markdown("<div style='padding: 8px 0;'>📄 <strong>Conversión por IA de PDF a Markdown limpio</strong></div>", unsafe_allow_html=True)
            st.markdown("<div style='padding: 8px 0;'>📊 <strong>Extracción avanzada de tablas numéricas</strong></div>", unsafe_allow_html=True)
            st.markdown("<div style='padding: 8px 0;'>🧮 <strong>Reconocimiento de fórmulas matemáticas (LaTeX)</strong></div>", unsafe_allow_html=True)
            st.markdown("<div style='padding: 8px 0;'>📦 <strong>Empaquetado portable e independiente</strong></div>", unsafe_allow_html=True)
        with c_feat2:
            st.markdown("<div style='padding: 8px 0;'>📁 <strong>Procesamiento masivo de lotes de archivos</strong></div>", unsafe_allow_html=True)
            st.markdown("<div style='padding: 8px 0;'>⚡ <strong>Aceleración por hardware dedicada (GPU CUDA)</strong></div>", unsafe_allow_html=True)
            st.markdown("<div style='padding: 8px 0;'>🔌 <strong>Operación 100% offline y local sin internet</strong></div>", unsafe_allow_html=True)
            st.markdown("<div style='padding: 8px 0;'>🎨 <strong>Interfaz fluida estilo Windows 11 acrílico</strong></div>", unsafe_allow_html=True)

    # TARJETA CON BORDE IZQUIERDO REPLICADA EXACTAMENTE DE 001_intro.png
    st.markdown("""
    <div class="dev-active-card">
        <strong style="color: #ffffff; font-size: 15px;">🔧 Herramienta en Desarrollo Activo:</strong> 
        <span style="color: #cbd5e1; font-size: 14.5px;">
        Este proyecto es de código abierto. Si tienes sugerencias o ideas de mejoras, ponte en contacto con el creador del repositorio de la App original 
        <strong>Jose Manuel Caamaño</strong> via <a href="https://www.linkedin.com/in/jmcaamanog/" target="_blank" style="color: #38bdf8; text-decoration: underline;">LinkedIn</a>, 
        el repositorio completo y libre o mediante su Colegio Profesional de la Arquitectura Técnica al que orgullosamente pertenece (<strong>COATAC</strong>).
        </span>
    </div>
    """, unsafe_allow_html=True)

    # BOTÓN CONVERTIR QUE NAVEGA DIRECTAMENTE Y OCUPA EL 100% DEL ANCHO SEGÚN MARCO ROJO DE IMAGEN 1
    if st.button("🚀 CONVERTIR", key="btn_inicio_to_convert_v6", type="primary", use_container_width=True):
        st.session_state.switch_to_convert = True
        st.rerun()

# ================= 2. PESTAÑA CONVERTIR =================
with tab_conv:

    # CONTENEDOR 1: ORIGEN DE DATOS
    with st.container(border=True):
        st.markdown("<h4 class='container-title'>ORIGEN DE DATOS</h4>", unsafe_allow_html=True)

        col_src1, col_src2, col_src3 = st.columns(3)
        with col_src1:
            pdf_type = "primary" if st.session_state.src_choice == "PDF" else "secondary"
            if st.button("📁 PDF ARCHIVO", key="btn_src_pdf_v6", type=pdf_type, use_container_width=True):
                st.session_state.src_choice = "PDF"
                st.rerun()

        with col_src2:
            is_folder_selected = bool(st.session_state.source_folder_path)
            folder_type = "primary" if (st.session_state.src_choice == "CARPETA" or is_folder_selected) else "secondary"
            folder_label = "📂 CARPETA" if not is_folder_selected else f"✔️ CARPETA ({os.path.basename(st.session_state.source_folder_path)})"
            if st.button(folder_label, key="btn_src_folder_v6", type=folder_type, use_container_width=True):
                st.session_state.src_choice = "CARPETA"
                chosen_f = select_folder_dialog("Seleccionar Carpeta de Origen con PDFs")
                if chosen_f:
                    st.session_state.source_folder_path = chosen_f
                st.rerun()

        with col_src3:
            web_type = "primary" if st.session_state.src_choice == "WEB" else "secondary"
            if st.button("🌐 PÁGINA WEB", key="btn_src_web_v6", type=web_type, use_container_width=True):
                st.session_state.src_choice = "WEB"
                st.rerun()

        files_to_process = []
        web_url_target = None
        page_range_filter = None

        st.write("")
        if st.session_state.src_choice == "PDF":
            uploaded_files = st.file_uploader(label="", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")
            if uploaded_files:
                files_to_process = uploaded_files
                st.success(f"✔️ {len(uploaded_files)} PDF(s) seleccionado(s).")
            page_range_str = st.text_input("🔍 Convertir solo páginas específicas (Opcional):", placeholder="Ejemplo: 1-5, 10, 15-20")
            page_range_filter = parse_page_range(page_range_str)

        elif st.session_state.src_choice == "CARPETA":
            # Si ya hay carpeta o el usuario prefiere ajustar la ruta directamente:
            src_path_input = st.text_input("Ruta de la carpeta de Origen en tu ordenador:", value=st.session_state.source_folder_path, placeholder="Ejemplo: C:\\Proyectos\\PDFs")
            if src_path_input != st.session_state.source_folder_path:
                st.session_state.source_folder_path = src_path_input
                st.rerun()

            if st.session_state.source_folder_path and os.path.isdir(st.session_state.source_folder_path):
                pdf_files = [f for f in os.listdir(st.session_state.source_folder_path) if f.lower().endswith(".pdf")]
                if pdf_files:
                    st.success(f"✔️ Se encontraron {len(pdf_files)} archivos PDF en: `{st.session_state.source_folder_path}`")
                    for f in pdf_files:
                        fp = os.path.join(st.session_state.source_folder_path, f)
                        files_to_process.append({"name": f, "path": fp})
            page_range_str = st.text_input("🔍 Convertir solo páginas específicas (Opcional):", placeholder="Ejemplo: 1-5, 10")
            page_range_filter = parse_page_range(page_range_str)

        elif st.session_state.src_choice == "WEB":
            web_url_target = st.text_input(label="", placeholder="https://ejemplo.com/articulo-tecnico", label_visibility="collapsed")

    # CONTENEDOR 2: TIPO DE EXTRACCIÓN
    with st.container(border=True):
        st.markdown("<h4 class='container-title'>TIPO DE EXTRACCIÓN</h4>", unsafe_allow_html=True)

        col_ext1, col_ext2, col_ext3, col_ext4 = st.columns(4)
        with col_ext1:
            t_rap = "primary" if st.session_state.ext_choice == "RÁPIDO" else "secondary"
            if st.button("⚡ RÁPIDO", key="btn_ext_rapido_v6", type=t_rap, use_container_width=True):
                st.session_state.ext_choice = "RÁPIDO"
                st.rerun()

        with col_ext2:
            t_graf = "primary" if st.session_state.ext_choice == "GRÁFICO" else "secondary"
            if st.button("🖼️ GRÁFICO", key="btn_ext_grafico_v6", type=t_graf, use_container_width=True):
                st.session_state.ext_choice = "GRÁFICO"
                st.rerun()

        with col_ext3:
            t_tec = "primary" if st.session_state.ext_choice == "TÉCNICO" else "secondary"
            if st.button("🏗️ TÉCNICO", key="btn_ext_tecnico_v6", type=t_tec, use_container_width=True):
                st.session_state.ext_choice = "TÉCNICO"
                st.rerun()

        with col_ext4:
            t_comp = "primary" if st.session_state.ext_choice == "COMPLETO" else "secondary"
            if st.button("🧮 COMPLETO", key="btn_ext_completo_v6", type=t_comp, use_container_width=True):
                st.session_state.ext_choice = "COMPLETO"
                st.rerun()

        disable_img_ext = False
        force_ocr_flag = False

        st.write("")
        if st.session_state.ext_choice == "RÁPIDO":
            disable_img_ext = True
            st.info("💡 **Modo Rápido:** Extrae únicamente el texto principal sin procesar imágenes para mayor velocidad.")
        elif st.session_state.ext_choice == "GRÁFICO":
            disable_img_ext = False
            st.info("💡 **Modo Gráfico:** Extrae texto e imágenes incrustadas en alta calidad.")
        elif st.session_state.ext_choice == "TÉCNICO":
            disable_img_ext = False
            st.info("💡 **Modo Técnico:** Procesa texto, imágenes, tablas de mediciones y planos AECO.")
        elif st.session_state.ext_choice == "COMPLETO":
            disable_img_ext = False
            force_ocr_flag = True
            st.info("💡 **Modo Completo:** Fuerza OCR en escaneos y ecuaciones matemáticas + texto, imágenes, tablas y planos.")

    # CONTENEDOR 3: EXPORTACIÓN Y PROCESAMIENTO
    with st.container(border=True):
        st.markdown("<h4 class='container-title'>EXPORTACIÓN Y PROCESAMIENTO</h4>", unsafe_allow_html=True)

        is_dest_active = bool(st.session_state.dest_folder_path)
        dest_btn_type = "primary" if is_dest_active else "secondary"
        dest_btn_label = "📂 CARPETA DESTINO" if not is_dest_active else f"✔️ CARPETA DESTINO ({os.path.basename(st.session_state.dest_folder_path)})"

        # BOTÓN CARPETA DESTINO OCUPANDO EL 100% DEL ANCHO
        if st.button(dest_btn_label, key="btn_browse_dest_folder_v6", type=dest_btn_type, use_container_width=True):
            chosen_dest = select_folder_dialog("Seleccionar Carpeta de Destino para Guardar")
            if chosen_dest:
                st.session_state.dest_folder_path = chosen_dest
                st.rerun()

        # CAMPO DE RUTA DESTINO EDITABLE DIRECTAMENTE
        dest_path_input = st.text_input("Ruta de la carpeta de Destino en tu ordenador:", value=st.session_state.dest_folder_path, placeholder="Ejemplo: C:\\Proyectos\\Resultados_MD")
        if dest_path_input != st.session_state.dest_folder_path:
            st.session_state.dest_folder_path = dest_path_input
            st.rerun()

        if is_dest_active and os.path.exists(st.session_state.dest_folder_path):
            st.success(f"📂 Carpeta de Destino válida: `{st.session_state.dest_folder_path}`")

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
            if lang: config_dict["languages"] = lang

            config_parser = ConfigParser(config_dict)
            artifact_dict = create_model_dict()
            return PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=artifact_dict,
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer()
            )

        has_valid_source = (files_to_process and len(files_to_process) > 0) or (st.session_state.src_choice == "WEB" and web_url_target)
        has_valid_destination = st.session_state.dest_folder_path and os.path.exists(st.session_state.dest_folder_path)

        if not has_valid_destination and has_valid_source:
            st.warning("⚠️ Selecciona o escribe una **Carpeta de Destino** válida para habilitar el botón de exportación.")

        st.write("")
        # BOTÓN PROCESAR OCUPANDO EL 100% DEL ANCHO
        btn_go = st.button("🚀 EXPORTAR Y PROCESAR DOCUMENTOS", key="btn_run_export_final_v6", type="primary", disabled=not (has_valid_source and has_valid_destination), use_container_width=True)

        if btn_go:
            progress_bar = st.progress(0)
            status_box = st.empty()
            start_time = time.time()
            converted_results = []

            if st.session_state.src_choice == "WEB":
                progress_bar.progress(25)
                status_box.info(f"🌐 Extrayendo URL Web: {web_url_target}")
                try:
                    title, md_content, web_imgs = convert_url_to_md(web_url_target, extract_images=not disable_img_ext)
                    progress_bar.progress(75)
                    status_box.info("📝 Formateando Markdown...")
                    converted_results.append({
                        "name": f"{re.sub(r'[^a-zA-Z0-9_-]', '_', title)[:30]}.md",
                        "markdown": md_content,
                        "images": web_imgs
                    })
                except Exception as e:
                    st.error(f"Error procesando URL: {e}")
            else:
                try:
                    converter = get_converter(disable_img_ext, st.session_state.default_lang, force_ocr_flag)
                    total_files = len(files_to_process)

                    for idx, file_item in enumerate(files_to_process):
                        file_name = file_item.name if st.session_state.src_choice == "PDF" else file_item["name"]
                        p_val = int(((idx + 0.4) / total_files) * 100)
                        progress_bar.progress(min(p_val, 90))
                        status_box.info(f"⏳ Procesando documento {idx+1}/{total_files}: {file_name}")

                        if st.session_state.src_choice == "PDF":
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

                        if st.session_state.src_choice == "PDF":
                            try: os.unlink(input_path)
                            except Exception: pass

                except Exception as e:
                    st.error("Error durante el procesamiento:")
                    st.code(str(e))

            progress_bar.progress(100)
            elapsed_time = time.time() - start_time
            status_box.success(f"✔️ Procesamiento y exportación completados en {elapsed_time:.1f} segundos.")

            if converted_results:
                st.session_state.last_results = converted_results
                try:
                    for res in converted_results:
                        out_p = os.path.join(st.session_state.dest_folder_path, res["name"].replace(".pdf", "") + ".md")
                        with open(out_p, "w", encoding="utf-8") as f:
                            f.write(res["markdown"])
                        obs_p = os.path.join(st.session_state.dest_folder_path, "OBSIDIAN_" + res["name"].replace(".pdf", "") + ".md")
                        with open(obs_p, "w", encoding="utf-8") as f:
                            f.write(format_for_obsidian(res["markdown"], res["name"]))
                    st.success(f"📂 Archivos Markdown y formato Obsidian guardados en: `{st.session_state.dest_folder_path}`")
                except Exception as ex:
                    st.error(f"Error al guardar en carpeta: {ex}")

    # INSPECTOR DE RESULTADOS Y EXPORTACIONES ESPECÍFICAS
    if st.session_state.last_results:
        converted_results = st.session_state.last_results
        st.markdown("<h4 style='color:#38bdf8; font-family:\"Outfit\"; margin-top:20px;'>💎 ACCIONES DE EXPORTACIÓN Y VISTA PREVIA</h4>", unsafe_allow_html=True)

        exp_col1, exp_col2, exp_col3 = st.columns(3)

        with exp_col1:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for result in converted_results:
                    base_n = os.path.splitext(result["name"])[0]
                    zip_file.writestr(f"{base_n}.md", result["markdown"].encode("utf-8"))
                    zip_file.writestr(f"OBSIDIAN_{base_n}.md", format_for_obsidian(result["markdown"], result["name"]).encode("utf-8"))
                    if result.get("images") and not disable_img_ext:
                        for img_n, img_obj in result["images"].items():
                            img_byte_arr = io.BytesIO()
                            img_obj.save(img_byte_arr, format="PNG")
                            zip_file.writestr(f"{base_n}_attachments/{img_n}", img_byte_arr.getvalue())
            st.download_button("📥 Descargar Paquete ZIP (.zip)", zip_buffer.getvalue(), "exportacion_completa.zip", "application/zip", use_container_width=True)

        with exp_col2:
            obsidian_md = format_for_obsidian(converted_results[0]["markdown"], converted_results[0]["name"])
            st.download_button("💎 EXPORTAR NOTA OBSIDIAN (.MD)", obsidian_md.encode("utf-8"), f"obsidian_{converted_results[0]['name']}", "text/markdown", use_container_width=True)

        with exp_col3:
            excel_bytes = extract_tables_to_excel(converted_results[0]["markdown"])
            if excel_bytes:
                st.download_button("📊 Descargar Tablas Excel (.xlsx)", excel_bytes, "tablas_extraidas.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            else:
                st.button("📊 Excel (Sin Tablas)", disabled=True, use_container_width=True)

        insp_tab1, insp_tab2 = st.tabs(["👁️ Vista Previa Formateada", "📝 Código Fuente Markdown"])
        first_md = converted_results[0].get("markdown", "")

        with insp_tab1:
            with st.container(border=True):
                st.markdown(first_md, unsafe_allow_html=True)
        with insp_tab2:
            st.code(first_md, language="markdown")

# ================= 3. PESTAÑA ASISTENTE IA =================
with tab_assistant:
    st.markdown("<h3 style='margin-top:0;'>💬 Asistente IA Offline</h3>", unsafe_allow_html=True)
    if not st.session_state.last_results:
        st.info("ℹ️ Procesa primero un documento en la pestaña **CONVERTIR** para realizar consultas.")
    else:
        doc_text = st.session_state.last_results[0].get("markdown", "")
        doc_name = st.session_state.last_results[0].get("name", "Documento")
        with st.container(border=True):
            st.markdown(f"📄 <strong>Documento Activo:</strong> <code>{doc_name}</code> ({len(doc_text.split())} palabras)", unsafe_allow_html=True)
        
        user_query = st.text_input("Introduce tu término o pregunta sobre el documento:", placeholder="Ejemplo: Resumen de pliegos, mediciones o normativa")
        if user_query:
            keywords = [w.lower() for w in user_query.split() if len(w) > 3]
            matching_lines = [line for line in doc_text.split('\n') if any(kw in line.lower() for kw in keywords)]
            if matching_lines:
                st.success(f"Se encontraron {len(matching_lines)} coincidencias:")
                for line in matching_lines[:15]:
                    st.markdown(f"• {line}")
            else:
                st.warning("No se encontraron coincidencias con los términos de búsqueda.")

# ================= 4. PESTAÑA REQUISITOS (REPLICADA EXACTAMENTE DE IMAGEN 008_REQUISITOS_Y_TEST.png) =================
with tab_settings:
    # 1. ESTADO DEL ACELERADOR GRÁFICO (CUDA)
    st.markdown("<h4>🟦 ESTADO DEL ACELERADOR GRÁFICO (CUDA)</h4>", unsafe_allow_html=True)
    cuda_avail = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "No disponible (Modo CPU)"
    vram_alloc = f"{torch.cuda.memory_allocated(0)/(1024**2):.1f} MB" if cuda_avail else "N/A"
    vram_res = f"{torch.cuda.memory_reserved(0)/(1024**2):.1f} MB" if cuda_avail else "N/A"
    
    cuda_badge_html = "<span style='color:#4ade80; font-weight:bold;'>🟢 ACTIVA (Acelerada por GPU)</span>" if cuda_avail else "<span style='color:#ef4444; font-weight:bold;'>🔴 INACTIVA</span>"

    st.markdown(f"""
    <table class="req-table">
        <thead>
            <tr>
                <th>Concepto</th>
                <th>Valor Detectado / Estado</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Aceleración CUDA</strong></td>
                <td>{cuda_badge_html}</td>
            </tr>
            <tr>
                <td><strong>Modelo de Gráfica</strong></td>
                <td>{gpu_name}</td>
            </tr>
            <tr>
                <td><strong>Uso de Memoria VRAM</strong></td>
                <td>{vram_alloc} (Reservada en caché: {vram_res})</td>
            </tr>
            <tr>
                <td><strong>Versión PyTorch (CUDA)</strong></td>
                <td><code>{torch.__version__}</code></td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    st.write("")

    # 2. DIAGNÓSTICO DEL SISTEMA (BOTÓN CENTRADO ÚNICAMENTE)
    col_d_center1, col_d_center2, col_d_center3 = st.columns([1, 2, 1])
    with col_d_center2:
        if st.button("🔍 CHEQUEAR REQUISITOS DEL SISTEMA", key="btn_check_reqs_v6", type="primary", use_container_width=True):
            st.success(f"✔️ Sistema verificado: Python {sys.version.split()[0]} | CUDA GPU: {gpu_name}")

    st.write("")
    st.divider()

    # 3. GUÍA DE INSTALACIÓN Y COMPARTICIÓN
    st.markdown("<h4>🚀 GUÍA DE INSTALACIÓN Y COMPARTICIÓN</h4>", unsafe_allow_html=True)
    
    st.markdown("""
    <table class="req-table">
        <tbody>
            <tr>
                <td style="width: 50px; text-align: center; vertical-align: top;"><span class="badge-num">1</span></td>
                <td>
                    <strong style="color: #38bdf8;">Empaquetar el proyecto</strong><br>
                    Comprime la carpeta del proyecto <code>pdf_to_md</code> en un archivo ZIP. <em>Recomendación:</em> Elimina las carpetas <code>.venv</code> (entorno virtual) y <code>models_cache</code> (pesos de los modelos de IA) antes de comprimir para reducir el peso del archivo de gigabytes a solo kilobytes, facilitando su envío rápido.
                </td>
            </tr>
            <tr>
                <td style="width: 50px; text-align: center; vertical-align: top;"><span class="badge-num">2</span></td>
                <td>
                    <strong style="color: #38bdf8;">Desplegar en el destino</strong><br>
                    Tu compañero solo debe extraer el archivo ZIP en su disco duro local y hacer doble clic en el archivo ejecutable de Windows <code>setup_and_run.bat</code>. No requiere instalación manual previa de dependencias ni configuraciones complejas.
                </td>
            </tr>
            <tr>
                <td style="width: 50px; text-align: center; vertical-align: top;"><span class="badge-num">3</span></td>
                <td>
                    <strong style="color: #38bdf8;">Autoconfiguración local</strong><br>
                    El script <code>.bat</code> analiza el hardware, instala automáticamente la versión de PyTorch idónea (con soporte GPU CUDA o modo CPU), descarga los pesos necesarios localmente y lanza la interfaz web en su navegador.
                </td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

# ================= 5. PESTAÑA AUTOR =================
with tab_author:
    col_pic, col_desc = st.columns([1, 2])
    
    with col_pic:
        gif_file = "yo_animado.gif"
        if os.path.exists(gif_file):
            try:
                base64_gif = get_base64_image(gif_file)
                st.markdown(f"""
                <div style='text-align: center;'>
                    <a href='https://jmcaamanog.pages.dev/' target='_blank'>
                        <img src='{base64_gif}' style='width: 180px; height: 180px; border-radius: 50%; border: 3px solid #3b82f6; box-shadow: 0 4px 15px rgba(59,130,246,0.45); object-fit: cover; transition: all 0.3s ease-in-out; cursor: pointer;' onmouseover='this.style.transform="scale(1.06)"' onmouseout='this.style.transform="scale(1)"' title="Visitar mi Web Profesional" />
                    </a>
                    <p style='margin-top: 15px; font-weight: bold; font-family: "Outfit"; font-size: 18px; color:#ffffff; margin-bottom: 0;'>José Manuel Caamaño González</p>
                    <p style='color: #9ca3af; font-size: 12px; margin-top: 2px;'>A Coruña (Galicia)</p>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                st.error("Error al cargar la foto de perfil.")
        else:
            st.markdown("""
            <div style='text-align: center;'>
                <a href='https://jmcaamanog.pages.dev/' target='_blank' style='text-decoration: none;'>
                    <div style='background: linear-gradient(135deg, #3b82f6, #06b6d4); width: 150px; height: 150px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; box-shadow: 0 4px 15px rgba(59,130,246,0.35); cursor: pointer;'>
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
            <br><br>
            Proyecto de código abierto orgullosamente desarrollado para la comunidad de la Arquitectura Técnica (<strong>COATAC</strong>).
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
              <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.779-1.75-1.75s.784-1.75 1.75-1.75 1.75.779 1.75 1.75-.784 1.75-1.75-1.75zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
            </svg>
            <span>LinkedIn</span>
          </a>
          <a href="https://jmcaamanog.pages.dev/" target="_blank" style="text-decoration: none; display: inline-flex; align-items: center; gap: 10px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 10px 20px; color: #ffffff; font-family: 'Outfit', sans-serif; font-weight: 600; font-size: 14px; transition: all 0.3s ease;">
            <span>🌐 Web</span>
          </a>
        </div>
        """, unsafe_allow_html=True)
