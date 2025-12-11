import streamlit as st
import os
import json
import time
from pathlib import Path

from inference import NFeProcessor, utils

st.set_page_config(
    page_title="NFe Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Roboto', sans-serif;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    h1 {
        color: #ffffff;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .subtitle {
        color: #00FFDD;
        font-size: 1rem;
        margin-bottom: 2.5rem;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        border-bottom: 1px solid #3A3E4A;
        padding-bottom: 10px;
    }

    [data-testid='stFileUploader'] {
        background-color: #121418;
        border: 1px dashed #3A3E4A;
        border-radius: 4px;
        padding: 30px;
    }
    [data-testid='stFileUploader']:hover {
        border-color: #00FFDD;
        background-color: #16191d;
    }
    [data-testid='stFileUploader'] section {
        padding: 0;
    }

    div.stButton > button {
        background-color: #00FFDD;
        color: #000000;
        border: none;
        border-radius: 2px; /* Cantos retos = mais sério */
        padding: 0.8rem 2rem;
        font-weight: 700;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.2s ease;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #00DDBB;
        box-shadow: 0 2px 10px rgba(0, 255, 221, 0.1);
        color: black;
    }
    
    div[data-testid="stDownloadButton"] > button {
        background: transparent;
        border: 1px solid #00FFDD;
        color: #00FFDD;
        border-radius: 2px;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background: #00FFDD;
        color: black;
    }

    .streamlit-expanderHeader {
        background-color: #1E2126;
        border-radius: 2px;
        color: #E0E0E0;
        font-size: 0.9rem;
        font-weight: 500;
        border: 1px solid #2D3139;
    }

    .stProgress > div > div > div > div {
        background-color: #00FFDD;
    }

    .status-text {
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_engine():
    return NFeProcessor()

st.markdown("<h1>NFe Intelligence AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Automated Fiscal Data Extraction System</div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### SYSTEM DIAGNOSTICS")
    
    with st.spinner("Initializing..."):
        nfe_engine = load_engine()
    
    st.markdown("""
    <div style='background-color: #1E2126; padding: 15px; border-radius: 4px; border: 1px solid #2D3139; font-size: 0.85rem; color: #ccc;'>
        <div><b>MODEL:</b> LayoutLMv3-FineTuned</div>
        <div style='margin-top: 8px;'><b>INFERENCE:</b> <span style='color:#00FFDD'>ACTIVE</span></div>
        <div style='margin-top: 8px;'><b>DEVICE:</b> CUDA (GPU)</div>
        <div style='margin-top: 8px;'><b>LATENCY:</b> LOW</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><div style='font-size: 0.7rem; color: #555;'>ENTERPRISE EDITION<br>BUILD 2025.12.01</div>", unsafe_allow_html=True)


st.markdown("<p style='color: #B0B3B8; font-size: 0.9rem; margin-bottom: 10px;'>UPLOAD DOCUMENT BATCH (PDF/IMG)</p>", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Faça upload dos documentos aqui",
    type=['png', 'jpg', 'jpeg', 'pdf'], 
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    st.markdown(f"<div style='margin-top: 20px; color: #fff; font-size: 0.9rem;'>DOCUMENTS IN QUEUE: <span style='color: #00FFDD; font-weight: bold;'>{len(uploaded_files)}</span></div>", unsafe_allow_html=True)
    
    st.write("") 

    c1, c2, c3 = st.columns([3, 2, 3])
    with c2:
        process_btn = st.button("START EXTRACTION", type="primary")

    if process_btn:
        temp_dir = "temp_batch_process"
        os.makedirs(temp_dir, exist_ok=True)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_files = len(uploaded_files)
        results_list = []
        
        results_area = st.container()

        for i, uploaded_file in enumerate(uploaded_files):

            status_text.markdown(f"<p class='status-text'>PROCESSING: {uploaded_file.name}...</p>", unsafe_allow_html=True)
            progress_bar.progress((i + 1) / total_files)
            
            temp_path = os.path.join(temp_dir, f"temp_{i}_{uploaded_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                raw_result = nfe_engine.process_file(temp_path)
                formatted_result = utils.format_output(uploaded_file.name, raw_result)
                results_list.append(formatted_result)

                with results_area:
                    status_label = "[SUCESSO]"
                    if "erro" in str(formatted_result).lower() or "falha" in str(formatted_result).lower():
                         status_label = "[FALHA]"
                    
                    expander_title = f"{uploaded_file.name} - {status_label}"
                    
                    with st.expander(expander_title, expanded=False):
                        st.json(formatted_result)

            except Exception as e:
                st.error(f"SYSTEM ERROR: {uploaded_file.name}")
            
            if os.path.exists(temp_path):
                os.remove(temp_path)

        progress_bar.progress(100)
        status_text.markdown("<p class='status-text' style='color:#00FFDD'>BATCH PROCESSING COMPLETED.</p>", unsafe_allow_html=True)
        
        st.markdown("<hr style='border-color: #3A3E4A; margin-top: 30px; margin-bottom: 30px;'>", unsafe_allow_html=True)
        
        json_string = json.dumps(results_list, indent=4, ensure_ascii=False)
        
        dc1, dc2, dc3 = st.columns([3, 2, 3])
        with dc2:
            st.download_button(
                label="DOWNLOAD JSON REPORT",
                data=json_string,
                file_name="nfe_extraction_report.json",
                mime="application/json"
            )

        try:
            os.rmdir(temp_dir)
        except:
            pass

elif not uploaded_files:
    for _ in range(5): st.write("")