"""
app.py
Universal Document-to-Entity & Knowledge Graph Extractor
Modernized UI/UX with Streamlit, PyMuPDF, and Interactive Vis.js Visualization.
"""

import os
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

from file_processor import process_uploaded_file
from file_entity_extractor import (
    extract_entities_from_document,
    generate_interactive_graph_html
)

st.set_page_config(
    page_title="Universal Entity & Ontology Extractor",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- MODERN DESIGN SYSTEM CSS -----------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hero Section */
    .hero-container {
        padding: 2.2rem 2.4rem;
        background: radial-gradient(circle at 10% 20%, rgba(37, 99, 235, 0.08) 0%, rgba(139, 92, 246, 0.05) 50%, rgba(248, 250, 252, 0) 100%),
                    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02);
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
        border: 1px solid rgba(37, 99, 235, 0.2);
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        color: #2563eb;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
    }
    
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.15;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 0.6rem 0;
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        color: #64748b;
        max-width: 780px;
        line-height: 1.6;
        margin: 0;
    }

    /* Modern Glass Card */
    .glass-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.04);
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .glass-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.06);
    }

    /* KPI Metric Cards */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.2rem;
        margin-bottom: 1.8rem;
    }
    
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.25rem 1.4rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        position: relative;
        overflow: hidden;
        transition: all 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.06);
    }
    
    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
    }
    .kpi-blue::before { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
    .kpi-purple::before { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
    .kpi-emerald::before { background: linear-gradient(90deg, #10b981, #34d399); }
    .kpi-amber::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }

    .kpi-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.02em;
        line-height: 1;
    }

    /* File Metadata Pill */
    .file-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #f1f5f9;
        color: #334155;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 600;
        border: 1px solid #e2e8f0;
    }

    /* Primary Action Button */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #4338ca 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.02rem !important;
        letter-spacing: -0.01em !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.6rem !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.35), 0 4px 6px -2px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 14px 28px -5px rgba(37, 99, 235, 0.45) !important;
    }
    .stButton>button:active {
        transform: translateY(0px) !important;
    }

    /* Taxonomy Pills */
    .tag-pill {
        display: inline-block;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #1e293b;
        padding: 6px 12px;
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 4px;
        transition: all 0.15s ease;
    }
    .tag-pill:hover {
        background: #f1f5f9;
        border-color: #cbd5e1;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    
    engine_choice = st.selectbox(
        "Intelligence Engine",
        options=[
            "Auto (AI if key exists, else Local NLP)",
            "Local High-Performance NLP (100% Offline)",
            "Google Gemini API",
            "DeepSeek / OpenRouter API"
        ],
        index=0
    )
    
    env_gemini = os.getenv("GEMINI_API_KEY", "")
    env_openrouter = os.getenv("OPENROUTER_API_KEY", "")
    
    with st.expander("🔑 Model API Credentials", expanded=bool(not env_gemini and not env_openrouter)):
        gemini_key = st.text_input(
            "Gemini API Key", 
            value=env_gemini, 
            type="password",
            help="For Gemini 2.5/3.5 Flash entity reasoning."
        )
        openrouter_key = st.text_input(
            "OpenRouter API Key", 
            value=env_openrouter, 
            type="password",
            help="For DeepSeek knowledge extraction."
        )
        
    st.markdown("### 🎯 Extraction Parameters")
    max_entities = st.slider("Entity Extraction Limit", min_value=10, max_value=150, value=60, step=5)
    
    st.divider()
    st.markdown("""
    <div style="background:#f8fafc;padding:12px;border-radius:10px;border:1px solid #e2e8f0;font-size:0.8rem;color:#64748b;">
      <strong style="color:#0f172a;">Supported Documents:</strong><br>
      📕 <b>PDF</b> (Full page extraction + outlines)<br>
      📘 <b>DOCX</b> (Structured paragraphs & tables)<br>
      📝 <b>TXT / MD</b> (Raw & markdown text)
    </div>
    """, unsafe_allow_html=True)

# ----------------- HERO HEADER -----------------
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">🧬 Autonomous ETVL Pipeline</div>
    <h1 class="hero-title">Document Entity & Ontology Extractor</h1>
    <p class="hero-subtitle">
        Upload any textbook, research paper, specification, or technical report. The system autonomously parses the text, extracts domain entities, technical definitions, and constructs an interactive Knowledge Graph.
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------- UPLOAD & CONTROLS -----------------
col_file, col_opts = st.columns([2, 1])

with col_file:
    uploaded_file = st.file_uploader(
        "Upload your document (PDF, DOCX, TXT, MD)",
        type=["pdf", "docx", "txt", "md"],
        help="Upload any single file to extract domain entities and construct an ontology."
    )

with col_opts:
    default_subject = os.getenv("TARGET_SUBJECT", "Auto-detect from file")
    target_subject = st.text_input(
        "Domain / Subject Focus",
        value=default_subject,
        help="E.g., 'Data Science', 'Machine Learning', 'Medicine', or leave as Auto-detect."
    )

if uploaded_file is not None:
    with st.spinner("Extracting content from uploaded file..."):
        file_info = process_uploaded_file(uploaded_file, uploaded_file.name)
        
    # Polished File Summary Card
    st.markdown(f"""
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:14px 18px;margin-bottom:1.2rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;box-shadow:0 2px 6px rgba(0,0,0,0.02);">
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="font-size:1.8rem;">📄</span>
        <div>
          <div style="font-weight:700;font-size:1rem;color:#0f172a;">{file_info['filename']}</div>
          <div style="font-size:0.8rem;color:#64748b;">Ready for entity & knowledge graph generation</div>
        </div>
      </div>
      <div style="display:flex;gap:8px;">
        <span class="file-badge"><b>Format:</b> {file_info['file_type']}</span>
        <span class="file-badge"><b>Words:</b> {file_info['word_count']:,}</span>
        <span class="file-badge"><b>Pages:</b> ~{file_info['total_pages']}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔍 View Extracted Document Preview", expanded=False):
        if file_info['headings']:
            st.markdown(f"**Detected Headings & Sections ({len(file_info['headings'])}):** " + ", ".join([f"`{h}`" for h in file_info['headings'][:10]]))
        st.text_area("Document Sample (First 1,200 characters)", file_info['full_text'][:1200] + ("..." if len(file_info['full_text']) > 1200 else ""), height=130)

    # Big Action Button
    if st.button("🚀 Extract Entities & Build Knowledge Graph"):
        if not file_info['full_text'].strip():
            st.error("The uploaded file does not contain extractable text. Please ensure it is not an image-only scanned document.")
        else:
            with st.spinner("Analyzing document semantics, identifying technical concepts, and constructing ontology..."):
                mode = "auto"
                if "Local" in engine_choice:
                    mode = "local"
                elif "Gemini" in engine_choice:
                    mode = "gemini"
                elif "DeepSeek" in engine_choice:
                    mode = "openrouter"
                    
                result = extract_entities_from_document(
                    text=file_info['full_text'],
                    subject=target_subject,
                    mode=mode,
                    max_entities=max_entities,
                    api_key_gemini=gemini_key,
                    api_key_openrouter=openrouter_key
                )
                st.session_state["extraction_result"] = result
                st.session_state["file_info"] = file_info

# ----------------- RESULTS DASHBOARD -----------------
if "extraction_result" in st.session_state:
    result = st.session_state["extraction_result"]
    entities = result.get("entities", [])
    relations = result.get("relations", [])
    ontology = result.get("ontology", {})
    file_info = st.session_state.get("file_info", {})
    
    st.markdown("<hr style='margin:2rem 0 1.5rem;border-color:#e2e8f0;'>", unsafe_allow_html=True)
    
    # Engine Status Bar
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.2rem;flex-wrap:wrap;gap:8px;">
      <div>
        <span style="font-size:1.3rem;font-weight:800;color:#0f172a;letter-spacing:-0.02em;">Extracted Knowledge Graph</span>
        <span style="font-size:0.85rem;color:#64748b;margin-left:8px;">Target Subject: <b style="color:#2563eb;">{result.get('subject', 'General')}</b></span>
      </div>
      <div>
        <span class="file-badge" style="background:#e0f2fe;color:#0369a1;border-color:#bae6fd;">⚡ Engine: {result.get('engine', 'NLP')}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI Grid
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.markdown(f"""
        <div class="kpi-card kpi-blue">
          <div class="kpi-label">🧬 Extracted Entities</div>
          <div class="kpi-value">{len(entities)}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_col2:
        st.markdown(f"""
        <div class="kpi-card kpi-purple">
          <div class="kpi-label">📁 Domain Categories</div>
          <div class="kpi-value">{len(ontology)}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_col3:
        st.markdown(f"""
        <div class="kpi-card kpi-emerald">
          <div class="kpi-label">🔗 Knowledge Triples</div>
          <div class="kpi-value">{len(relations)}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_col4:
        st.markdown(f"""
        <div class="kpi-card kpi-amber">
          <div class="kpi-label">📑 Document Words</div>
          <div class="kpi-value">{file_info.get('word_count', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)

    # Visual Exploration Tabs
    tab_graph, tab_table, tab_tree, tab_relations = st.tabs([
        "🕸️ Interactive Network Graph",
        "📋 Entity Data Dictionary",
        "🌳 Categorized Taxonomy",
        "🔗 Knowledge Graph Triples"
    ])
    
    with tab_graph:
        st.markdown("<div style='font-size:0.9rem;color:#64748b;margin-bottom:8px;'>Drag nodes to reposition, scroll to zoom, hover for definitions, or click <b>Fit Graph</b> to center.</div>", unsafe_allow_html=True)
        graph_html = generate_interactive_graph_html(result)
        components.html(graph_html, height=640, scrolling=False)
        
    with tab_table:
        if entities:
            df = pd.DataFrame(entities)
            col_search, col_filter = st.columns([2, 1])
            with col_filter:
                type_options = ["All Categories"] + sorted(list(df["type"].unique()))
                selected_type = st.selectbox("Category Filter", type_options)
            with col_search:
                search_query = st.text_input("🔍 Search Entity Name", placeholder="Type keywords...")
                
            filtered_df = df.copy()
            if selected_type != "All Categories":
                filtered_df = filtered_df[filtered_df["type"] == selected_type]
            if search_query:
                filtered_df = filtered_df[filtered_df["name"].str.contains(search_query, case=False, na=False)]
                
            st.dataframe(
                filtered_df,
                use_container_width=True,
                column_config={
                    "name": st.column_config.TextColumn("Entity Name", width="medium"),
                    "type": st.column_config.TextColumn("Category", width="small"),
                    "definition": st.column_config.TextColumn("Definition / Context", width="large"),
                    "confidence": st.column_config.ProgressColumn("Confidence", format="%.2f", min_value=0, max_value=1),
                    "frequency": st.column_config.NumberColumn("Score / Frequency")
                },
                hide_index=True
            )
        else:
            st.info("No entities detected in the document.")

    with tab_tree:
        st.markdown("### Hierarchical Subject Taxonomy")
        st.markdown("<p style='font-size:0.9rem;color:#64748b;'>Organized structural domains synthesized from the uploaded document.</p>", unsafe_allow_html=True)
        for category, terms in ontology.items():
            with st.expander(f"📁 **{category}** ({len(terms)} items)", expanded=True):
                pills_html = "".join([f'<span class="tag-pill">{t}</span>' for t in terms])
                st.markdown(f'<div style="line-height:2.2;">{pills_html}</div>', unsafe_allow_html=True)
                
    with tab_relations:
        st.markdown("### Synthesized Knowledge Triples (Subject $\\rightarrow$ Predicate $\\rightarrow$ Object)")
        if relations:
            rel_df = pd.DataFrame(relations)
            st.dataframe(rel_df, use_container_width=True, hide_index=True)
        else:
            st.info("No explicit relational patterns found in this document.")

    # Export Section
    st.markdown("<hr style='margin:2.5rem 0 1.5rem;border-color:#e2e8f0;'>", unsafe_allow_html=True)
    st.markdown("### 💾 Export Knowledge Graph")
    
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        json_data = json.dumps(result, indent=2)
        st.download_button(
            label="📥 Download JSON Graph",
            data=json_data,
            file_name="extracted_ontology.json",
            mime="application/json"
        )
        
    with exp_col2:
        if entities:
            csv_data = pd.DataFrame(entities).to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV Dictionary",
                data=csv_data,
                file_name="extracted_entities.csv",
                mime="text/csv"
            )
            
    with exp_col3:
        graph_html = generate_interactive_graph_html(result)
        st.download_button(
            label="📥 Download Interactive HTML Report",
            data=graph_html,
            file_name="knowledge_graph_viewer.html",
            mime="text/html"
        )
