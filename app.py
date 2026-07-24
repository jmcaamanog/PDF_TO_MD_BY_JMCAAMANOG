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
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0
if "src_choice" not in st.session_state:
    st.session_state.src_choice = "PDF"
if "ext_choice" not in st.session_state:
    st.session_state.ext_choice = "TÉCNICO"
if "default_lang" not in st.session_state:
    st.session_state.default_lang = "es"
if "last_results" not in st.session_state:
    st.session_state.last_results = []

# Estilos CSS de Alta Calidad (+25% Más Ancho, Pestañas Redondeadas y Marcos Centrados)
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

    /* MARCOS Y CONTENEDORES CON TÍTULO EN ESQUINA SUPERIOR IZQUIERDA */
    .step-container {
        background: rgba(17, 24, 39, 0.65);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        transition: all 0.3s ease;
        position: relative;
    }
    
    .step-container:hover {
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
    }

    .container-title {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px;
        color: #3b82f6 !important;
        margin-top: 0 !important;
        margin-bottom: 18px !important;
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
    
    /* PESTAÑAS PRINCIPALES REDONDEADAS Y MÁS ANCHAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(17, 24, 39, 0.5);
        padding: 8px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        justify-content: center;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 12px;
        color: #9ca3af;
        font-weight: 700;
        font-size: 14px;
        font-family: 'Outfit', sans-serif;
        text-transform: uppercase;
        border: none;
        padding: 0 32px;
        transition: all 0.25s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6, #06b6d4) !important;
        color: #ffffff !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
    }

    /* BOTONES PRIMARIOS */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6, #06b6d4) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 14px 28px !important;
        font-family: 'Outfit', sans-serif;
        font-size: 15px;
        font-weight: 700;
        border-radius: 10px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        width: 100%;
        text-transform: uppercase;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4);
    }

    /* TARJETAS DE SELECCIÓN TIPO SEGMENTED CONTROL */
    .mode-card-selected {
        background: rgba(59, 130, 246, 0.15) !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        color: #ffffff;
        font-weight: bold;
    }

    .metric-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-family: 'Outfit', sans-serif;
        font-size: 26px;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 12px;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.5px;
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
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; margin-top: 5px;">
  <div style="display: flex; align-items: center; gap: 16px;">
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="url(#blue-cyan-grad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
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
      <h1 style="margin: 0; font-family: 'Outfit', sans-serif; font-weight: 800; background: linear-gradient(135deg, #3b82f6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 30px; text-transform: uppercase;">PDF to .MD by jmcaamanog</h1>
      <p style='font-size: 14px !important; color: #9ca3af; margin: 0;'>Herramienta de extracción inteligente de documentos para Arquitectura Técnica y AECO</p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------- 5 PESTAÑAS PRINCIPALES REDONDEADAS -----------------
tab_home, tab_conv, tab_assistant, tab_settings, tab_author = st.tabs([
    "🏠 INICIO",
    "⚡ CONVERTIR",
    "💬 ASISTENTE IA",
    "⚙️ AJUSTES",
    "👨‍💻 AUTOR"
])

# ================= 1. PESTAÑA INICIO =================
with tab_home:
    st.markdown("<h2 style='margin-top:0; font-size: 24px;'>Bienvenido a PDF to .MD</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p style='color: #cbd5e1; margin-bottom: 25px;'>Conversión inteligente y extracción local de documentos técnicos AECO a Markdown estructurado.</p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="step-container">
        <h4 class="container-title">¿QUÉ PUEDES HACER CON ESTA VERSIÓN?</h4>
    """, unsafe_allow_html=True)

    # 2 COLUMNAS SOLO TITULOS SIN DESCRIPCION
    c_feat1, c_feat2 = st.columns(2)
    with c_feat1:
        st.markdown("<div style='padding: 8px 0;'>📄 <strong>CONVERSIÓN INTELIGENTE DE PDFs AECO</strong></div>", unsafe_allow_html=True)
        st.markdown("<div style='padding: 8px 0;'>🖼️ <strong>EXTRACCIÓN DE FOTOGRAFÍAS Y PLANOS</strong></div>", unsafe_allow_html=True)
        st.markdown("<div style='padding: 8px 0;'>📊 <strong>RECONSTRUCCIÓN DE TABLAS Y EXCEL (.XLSX)</strong></div>", unsafe_allow_html=True)
    with c_feat2:
        st.markdown("<div style='padding: 8px 0;'>🚀 <strong>EXPORTACIÓN PARA OBSIDIAN VAULT (.MD)</strong></div>", unsafe_allow_html=True)
        st.markdown("<div style='padding: 8px 0;'>🌐 <strong>EXTRACTOR WEB (PÁGINAS URL A MARKDOWN)</strong></div>", unsafe_allow_html=True)
        st.markdown("<div style='padding: 8px 0;'>💬 <strong>ASISTENTE IA OFFLINE Y DIAGNÓSTICO</strong></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="step-container" style="border-color: rgba(6, 182, 212, 0.4);">
        <h4 class="container-title" style="color: #06b6d4 !important;">🚀 HERRAMIENTA EN DESARROLLO ACTIVO</h4>
        <p style="margin-bottom: 0; color: #cbd5e1;">Desarrollada para la comunidad de la Arquitectura Técnica (<strong>COATAC</strong>). Procesamiento 100% privado y local sin envío de datos a la nube.</p>
    </div>
    """, unsafe_allow_html=True)

    col_c_btn1, col_c_btn2, col_c_btn3 = st.columns([1, 2, 1])
    with col_c_btn2:
        if st.button("🚀 COMENZAR A CONVERTIR DOCUMENTOS", key="btn_inicio_to_convert"):
            st.info("💡 Por favor, haz clic arriba en la pestaña **⚡ CONVERTIR** para iniciar el flujo.")

# ================= 2. PESTAÑA CONVERTIR (MARCOS DE CONTENEDOR 100% REPARTIDOS) =================
with tab_conv:

    # CONTENEDOR 1: ORIGEN DE DATOS
    st.markdown("""
    <div class="step-container">
        <h4 class="container-title">ORIGEN DE DATOS</h4>
    """, unsafe_allow_html=True)

    col_src1, col_src2, col_src3 = st.columns(3)
    with col_src1:
        if st.button("📁 PDF ARCHIVO", key="btn_src_pdf"):
            st.session_state.src_choice = "PDF"
    with col_src2:
        if st.button("📂 CARPETA ARCHIVOS", key="btn_src_folder"):
            st.session_state.src_choice = "CARPETA"
    with col_src3:
        if st.button("🌐 PÁGINA WEB", key="btn_src_web"):
            st.session_state.src_choice = "WEB"

    files_to_process = []
    web_url_target = None
    page_range_filter = None

    st.markdown("<div style='margin-top: 15px;'>", unsafe_allow_html=True)
    if st.session_state.src_choice == "PDF":
        uploaded_files = st.file_uploader("Arrastra o selecciona tus archivos PDF:", type=["pdf"], accept_multiple_files=True)
        if uploaded_files:
            files_to_process = uploaded_files
            st.success(f"✔️ {len(uploaded_files)} PDF(s) listo(s) para procesar.")
        page_range_str = st.text_input("🔍 Convertir solo páginas específicas (Opcional):", placeholder="Ejemplo: 1-5, 10, 15-20")
        page_range_filter = parse_page_range(page_range_str)

    elif st.session_state.src_choice == "CARPETA":
        folder_path = st.text_input("Ruta absoluta de la carpeta de PDFs:", placeholder="Ejemplo: C:\\Proyectos\\PDFs")
        page_range_str = st.text_input("🔍 Convertir solo páginas específicas (Opcional):", placeholder="Ejemplo: 1-5, 10")
        page_range_filter = parse_page_range(page_range_str)
        if folder_path and os.path.isdir(folder_path):
            pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
            if pdf_files:
                st.success(f"✔️ Se encontraron {len(pdf_files)} archivos PDF.")
                for f in pdf_files:
                    fp = os.path.join(folder_path, f)
                    files_to_process.append({"name": f, "path": fp})

    elif st.session_state.src_choice == "WEB":
        web_url_target = st.text_input("Dirección Web (URL):", placeholder="https://ejemplo.com/articulo-tecnico")

    st.markdown("</div></div>", unsafe_allow_html=True)

    # CONTENEDOR 2: TIPO DE EXTRACCIÓN (4 OPCIONES EN 4 COLUMNAS DE ANCHO COMPLETO)
    st.markdown("""
    <div class="step-container">
        <h4 class="container-title">TIPO DE EXTRACCIÓN</h4>
    """, unsafe_allow_html=True)

    col_ext1, col_ext2, col_ext3, col_ext4 = st.columns(4)
    with col_ext1:
        if st.button("⚡ RÁPIDO", key="btn_ext_rapido"):
            st.session_state.ext_choice = "RÁPIDO"
    with col_ext2:
        if st.button("🖼️ GRÁFICO", key="btn_ext_grafico"):
            st.session_state.ext_choice = "GRÁFICO"
    with col_ext3:
        if st.button("🏗️ TÉCNICO", key="btn_ext_tecnico"):
            st.session_state.ext_choice = "TÉCNICO"
    with col_ext4:
        if st.button("🧮 COMPLETO", key="btn_ext_completo"):
            st.session_state.ext_choice = "COMPLETO"

    disable_img_ext = False
    force_ocr_flag = False

    st.markdown("<div style='margin-top: 15px;'>", unsafe_allow_html=True)
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

    st.markdown("</div></div>", unsafe_allow_html=True)

    # CONTENEDOR 3: EXPORTACIÓN Y PROCESAMIENTO
    st.markdown("""
    <div class="step-container">
        <h4 class="container-title">EXPORTACIÓN Y PROCESAMIENTO</h4>
    """, unsafe_allow_html=True)

    custom_output_folder = st.text_input("📂 Carpeta de Destino en el ordenador (Opcional):", placeholder="Deja vacío para descargar directamente el archivo .ZIP / .MD desde el navegador")

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

    can_export = (files_to_process and len(files_to_process) > 0) or (st.session_state.src_choice == "WEB" and web_url_target)

    if can_export:
        if st.button("🚀 EXPORTAR Y PROCESAR DOCUMENTOS", key="btn_run_export_final"):
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

                if custom_output_folder and os.path.isdir(custom_output_folder):
                    try:
                        for res in converted_results:
                            out_p = os.path.join(custom_output_folder, res["name"].replace(".pdf", "") + ".md")
                            with open(out_p, "w", encoding="utf-8") as f:
                                f.write(res["markdown"])
                        st.success(f"📂 Archivos guardados directamente en: `{custom_output_folder}`")
                    except Exception as ex:
                        st.error(f"Error al guardar en la carpeta seleccionada: {ex}")

    st.markdown("</div>", unsafe_allow_html=True)

    # MOSTRAR RESULTADOS
    if st.session_state.last_results:
        converted_results = st.session_state.last_results
        st.markdown("<h4 style='color:#38bdf8; font-family:\"Outfit\"; margin-top:20px;'>📦 DESCARGAS & INSPECTOR DE RESULTADOS</h4>", unsafe_allow_html=True)
        
        m_col1, m_col2, m_col3 = st.columns(3)
        total_words = sum(len(res.get("markdown", "").split()) for res in converted_results)
        total_imgs = sum(len(res.get("images", {})) for res in converted_results if res.get("images"))

        with m_col1: st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(converted_results)}</div><div class='metric-label'>Documentos</div></div>", unsafe_allow_html=True)
        with m_col2: st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_words:,}</div><div class='metric-label'>Palabras</div></div>", unsafe_allow_html=True)
        with m_col3: st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_imgs}</div><div class='metric-label'>Imágenes</div></div>", unsafe_allow_html=True)

        st.write("")
        exp_col1, exp_col2, exp_col3 = st.columns(3)

        with exp_col1:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for result in converted_results:
                    base_n = os.path.splitext(result["name"])[0]
                    zip_file.writestr(f"{base_n}.md", result["markdown"].encode("utf-8"))
                    if result.get("images") and not disable_img_ext:
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

        insp_tab1, insp_tab2 = st.tabs(["👁️ Vista Previa Formateada", "📝 Código Fuente Markdown"])
        first_md = converted_results[0].get("markdown", "")

        with insp_tab1:
            st.markdown("<div class='step-container' style='max-height: 380px; overflow-y: auto;'>", unsafe_allow_html=True)
            st.markdown(first_md, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with insp_tab2:
            st.code(first_md, language="markdown")

# ================= 3. PESTAÑA ASISTENTE IA =================
with tab_assistant:
    st.markdown("<h3 style='margin-top:0;'>💬 Asistente IA Offline</h3>", unsafe_allow_html=True)
    if not st.session_state.last_results:
        st.info("ℹ️ Procesa primero un documento en la pestaña **⚡ CONVERTIR** para realizar consultas.")
    else:
        doc_text = st.session_state.last_results[0].get("markdown", "")
        doc_name = st.session_state.last_results[0].get("name", "Documento")
        st.markdown(f"<div class='step-container'>📄 <strong>Documento Activo:</strong> <code>{doc_name}</code> ({len(doc_text.split())} palabras)</div>", unsafe_allow_html=True)
        
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

# ================= 4. PESTAÑA AJUSTES =================
with tab_settings:
    st.markdown("<h3 style='margin-top:0;'>⚙️ Ajustes del Sistema y Diagnóstico</h3>", unsafe_allow_html=True)
    
    sub_set1, sub_set2, sub_set3 = st.tabs(["🤖 Ajustes de IA", "📊 Estado Acelerador Gráfico", "📖 Guía de Instalación"])
    
    with sub_set1:
        st.markdown("<h4 class='container-title'>CONFIGURACIÓN DE IDIOMA Y MEMORIA</h4>", unsafe_allow_html=True)
        st.session_state.default_lang = st.selectbox("Idioma Principal del Documento:", ["es", "en", "gl", "ca", "eu", "fr", "de"], index=0)
        st.write("")
        if st.button("🧹 PURGAR MEMORIA VRAM & CACHÉ DEL PROYECTO", key="btn_purge_settings_v2"):
            st.cache_resource.clear()
            st.cache_data.clear()
            if torch.cuda.is_available(): torch.cuda.empty_cache()
            st.success("✔️ Memoria RAM y VRAM liberadas correctamente.")
            
    with sub_set2:
        st.markdown("<h4 class='container-title'>ESTADO DEL ACELERADOR HARDWARE</h4>", unsafe_allow_html=True)
        cuda_avail = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "No disponible (Modo CPU)"
        vram_alloc = f"{torch.cuda.memory_allocated(0)/(1024**2):.1f} MB" if cuda_avail else "N/A"
        vram_res = f"{torch.cuda.memory_reserved(0)/(1024**2):.1f} MB" if cuda_avail else "N/A"
        
        st.markdown(f"""
        <table style='width:100%; border-collapse: collapse; font-size: 14px;'>
            <tr style='border-bottom:1px solid rgba(255,255,255,0.08);'>
                <td style='padding:10px 0; font-weight:bold; color:#38bdf8;'>Aceleración CUDA</td>
                <td style='padding:10px 0;'>{'🟢 ACTIVA (GPU Acelerada)' if cuda_avail else '🔴 INACTIVA (CPU)'}</td>
            </tr>
            <tr style='border-bottom:1px solid rgba(255,255,255,0.08);'>
                <td style='padding:10px 0; color:#9ca3af;'>Modelo de Gráfica</td>
                <td style='padding:10px 0;'>{gpu_name}</td>
            </tr>
            <tr style='border-bottom:1px solid rgba(255,255,255,0.08);'>
                <td style='padding:10px 0; color:#9ca3af;'>VRAM Reservada / Asignada</td>
                <td style='padding:10px 0;'>{vram_res} / {vram_alloc}</td>
            </tr>
            <tr style='border-bottom:1px solid rgba(255,255,255,0.08);'>
                <td style='padding:10px 0; color:#9ca3af;'>Versión de PyTorch</td>
                <td style='padding:10px 0;'><code>{torch.__version__}</code></td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        
        st.write("")
        if st.button("🔍 EJECUTAR DIAGNÓSTICO DEL SISTEMA", key="btn_diag_sys"):
            st.info(f"Sistema Operativo: {sys.platform} | Python: {sys.version.split()[0]} | CUDA disponible: {cuda_avail}")

    with sub_set3:
        st.markdown("<h4 class='container-title'>GUÍA DE INSTALACIÓN Y COMPATIBILIDAD</h4>", unsafe_allow_html=True)
        st.markdown("""
        <ul>
            <li><strong>Requisitos de Hardware:</strong> Recomendado GPU NVIDIA con 4GB+ VRAM para aceleración CUDA.</li>
            <li><strong>Caché de Modelos:</strong> Todos los pesos de IA se almacenan localmente en <code>./models_cache</code> dentro del proyecto para evitar ocupar disco C:.</li>
            <li><strong>Contenedor Docker:</strong> Puedes ejecutar <code>run_docker.bat</code> para aislar el entorno en un contenedor.</li>
        </ul>
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
              <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.779-1.75-1.75s.784-1.75 1.75-1.75 1.75.779 1.75 1.75-.784 1.75-1.75 1.75zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
            </svg>
            <span>LinkedIn</span>
          </a>
          <a href="https://jmcaamanog.pages.dev/" target="_blank" style="text-decoration: none; display: inline-flex; align-items: center; gap: 10px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 10px 20px; color: #ffffff; font-family: 'Outfit', sans-serif; font-weight: 600; font-size: 14px; transition: all 0.3s ease;">
            <span>🌐 Web</span>
          </a>
        </div>
        """, unsafe_allow_html=True)
