import streamlit as st
import hashlib
import json
from parser import parse_pdfs
from auditor_logic import run_forensic_audit

# Set page config
st.set_page_config(
    page_title="Shadow Auditor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- NEUTRAL MATERIAL DESIGN CSS (Adaptive Light/Dark) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* Material Design Cards */
    .material-card {
        background-color: var(--secondary-background-color);
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        transition: all 0.3s cubic-bezier(.25,.8,.25,1);
    }
    
    .material-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15), 0 4px 4px rgba(0,0,0,0.15);
    }

    /* Typography */
    h1, h2, h3, h4 {
        font-weight: 500 !important;
        color: var(--text-color) !important;
    }
    
    .subtitle {
        color: var(--text-color);
        opacity: 0.7;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        text-align: center;
    }

    /* Distinctive Text Blocks */
    .expert-block {
        border-left: 4px solid #1976D2; /* Material Blue */
        padding: 16px;
        background-color: rgba(25, 118, 210, 0.05);
        border-radius: 0 4px 4px 0;
        margin-bottom: 16px;
    }
    
    .layman-block {
        border-left: 4px solid #43A047; /* Material Green */
        padding: 16px;
        background-color: rgba(67, 160, 71, 0.05);
        border-radius: 0 4px 4px 0;
        font-style: italic;
    }
    
    .metric-label {
        font-weight: 500;
        margin-bottom: 4px;
        display: block;
    }
    </style>
""", unsafe_allow_html=True)

# --- TITLE & CONFIG ---
st.markdown("<h1 style='text-align: center;'>⚖️ Shadow Auditor</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Institutional Forensic Intelligence Platform</div>", unsafe_allow_html=True)

uploaded_files = st.file_uploader("Upload SEC Filings or Financial Documents (PDF)", type="pdf", accept_multiple_files=True)
if st.button("EXECUTE FORENSIC AUDIT", type="primary", use_container_width=True):
    if not uploaded_files: 
        st.warning("Please upload PDF evidence to begin.")
    else: 
        st.session_state.trigger_audit = True

if uploaded_files:
    unique_files = []
    seen_hashes = set()
    for f in uploaded_files:
        content = f.read()
        if hashlib.sha256(content).hexdigest() not in seen_hashes:
            seen_hashes.add(hashlib.sha256(content).hexdigest())
            unique_files.append(content)
        f.seek(0)

    if st.session_state.get("trigger_audit"):
        with st.status("Analyzing Financial Records and Computing Ratios...", expanded=True) as status:
            full_text = parse_pdfs(unique_files)
            st.write("Extracting facts and computing deterministic metrics...")
            raw_report = run_forensic_audit(full_text)
            st.session_state.last_report = raw_report
            st.session_state.trigger_audit = False
            status.update(label="Audit Complete!", state="complete", expanded=False)

if "last_report" in st.session_state:
    try:
        report_data = st.session_state.last_report
        
        # Check if it's an integrity error payload
        if report_data.startswith("{") and "error" in report_data:
            err_data = json.loads(report_data)
            st.error(err_data["error"])
            st.stop()
            
        json_str = report_data.split("=== SHADOW_AUDITOR_RESULT ===")[1].split("=== END_RESULT ===")[0]
        data = json.loads(json_str)


        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; margin-bottom: 2rem;'><span style='background-color: var(--secondary-background-color); padding: 8px 16px; border-radius: 20px; font-weight: 500; font-size: 0.95rem; border: 1px solid rgba(255,255,255,0.1); color: #94a3b8;'>📄 {data.get('upload_context', 'Financial Documents')}</span></div>", unsafe_allow_html=True)
        
        # --- PROMINENT AI REASONING TRACE ---
        st.markdown("### 🧠 AI Reasoning Trace (Real-time cognition)")
        with st.expander("View internal reasoning logs", expanded=True):
            st.info(data.get('thought_trace', 'Reasoning trace captured.'))

        st.markdown("<br/>", unsafe_allow_html=True)

        # --- KPI BANNER ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1: st.metric("FRAUD RISK SCORE", f"{data['score']}/100")
        with kpi2: st.metric("STATUS", data['level'])
        with kpi3: st.metric("ARCHETYPE", data.get('archetype', 'N/A'))
        with kpi4: st.metric("SECTOR", data['industry'])

        st.markdown("<br>", unsafe_allow_html=True)

        # --- TABBED VIEW ---
        tab1, tab2, tab3 = st.tabs(["Executive Dossier", "Technical Audit", "Evidence Vault"])

        with tab1:
            col_a, col_b = st.columns([1.2, 0.8])
            with col_a:
                st.markdown("### Executive Summary")
                st.markdown(f"<div class='expert-block'>{data['summary']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='layman-block'><b>In Plain English:</b><br>{data['summary_layman']}</div>", unsafe_allow_html=True)
            with col_b:
                st.markdown("### Risk Vector Analysis")
                st.markdown("<div class='material-card'>", unsafe_allow_html=True)
                for metric_name, metric_value in data['metrics'].items():
                    clean_name = metric_name.replace('_', ' ').title()
                    st.markdown(f"<span class='metric-label'>{clean_name}</span>", unsafe_allow_html=True)
                    st.progress(float(metric_value))
                st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown("### Narrative Drift Analysis")
            st.markdown(f"<div class='expert-block'>{data['drift']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='layman-block'><b>What this means:</b><br>{data['drift_layman']}</div>", unsafe_allow_html=True)
            
            st.markdown("<hr/>", unsafe_allow_html=True)
            
            st.markdown("### Deterministic Ratios (Sector Specific)")
            for r in data['ratios']:
                st.markdown(f"""
                <div class='material-card'>
                    <h4 style='margin-top:0;'>{r['name']}</h4>
                    <p><b>Formula:</b> <code>{r['formula']}</code></p>
                    <p><b>Calculated Value:</b> <strong style='font-size:1.2rem; color:#D32F2F;'>{r['value']}</strong></p>
                    <p><b>Audit Finding:</b> {r['audit']}</p>
                </div>
                """, unsafe_allow_html=True)

        with tab3:
            st.markdown("### Actionable Next Steps")
            st.markdown(f"<div class='material-card'>{data['next_steps']}</div>", unsafe_allow_html=True)
            
            st.markdown("### Verifiable Citations")
            st.markdown(f"<div class='material-card'><pre style='white-space: pre-wrap;'>{data['citations']}</pre></div>", unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("CLEAR DASHBOARD"):
            for key in st.session_state.keys(): del st.session_state[key]
            st.rerun()

    except Exception as e:
        st.error(f"Processing Error: {e}")
        st.write(st.session_state.last_report)
