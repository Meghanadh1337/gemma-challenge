import streamlit as st
import hashlib
import json
import plotly.graph_objects as go
from parser import parse_pdfs
from auditor_logic import run_forensic_audit

# Set page config for a truly premium "Institutional" feel
st.set_page_config(
    page_title="Shadow Auditor | Forensic Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- PREMIUM CSS OVERHAUL (Accessibility + High Contrast) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0f172a; /* Slate 900 */
        color: #f8fafc; /* Slate 50 */
    }

    .main {
        padding: 2rem 5rem;
    }

    /* Card Styling */
    .glass-card {
        background: rgba(30, 41, 59, 0.7); /* Slate 800 */
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 24px -1px rgba(0, 0, 0, 0.2);
    }

    /* Typography Accessibility */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
    
    p, li {
        line-height: 1.6;
        font-size: 1.05rem;
        color: #cbd5e1; /* Slate 300 */
    }

    /* Metric Overrides */
    [data-testid="stMetric"] {
        background: #1e293b;
        border-radius: 12px;
        padding: 1.5rem !important;
        border: 1px solid #334155;
    }
    [data-testid="stMetricValue"] { color: #10b981 !important; font-weight: 700; } /* Emerald 500 */
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; }

    /* Layman vs Expert Distinctiveness */
    .expert-text {
        border-left: 4px solid #10b981;
        padding: 1.5rem;
        background: rgba(16, 185, 129, 0.05);
        border-radius: 0 8px 8px 0;
        margin-bottom: 1rem;
    }
    
    .layman-text {
        border-left: 4px solid #6366f1; /* Indigo 500 */
        padding: 1.5rem;
        background: rgba(99, 102, 241, 0.05);
        border-radius: 0 8px 8px 0;
        color: #e2e8f0;
        font-style: italic;
    }

    .stButton>button {
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -5px rgba(16, 185, 129, 0.4);
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #10b981 !important;
        border-bottom: 2px solid #10b981 !important;
    }
    </style>
""", unsafe_allow_html=True)

def create_radar_chart(metrics):
    categories = ['Receivables', 'Auditor', 'Buzzwords', 'Narrative', 'Integrity']
    values = [metrics.get(k, 0) for k in ['receivables_vs_revenue', 'auditor_turnover', 'buzzword_vs_cashflow', 'risk_factor_shift', 'integrity_of_disclosures']]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values, theta=categories, fill='toself', name='Risk Profile',
        line_color='#10b981', fillcolor='rgba(16, 185, 129, 0.2)'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1], gridcolor="#334155", tickfont=dict(color="#94a3b8")),
        bgcolor="rgba(0,0,0,0)", angularaxis=dict(gridcolor="#334155", tickfont=dict(color="#f8fafc"))),
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=30, b=30), height=400
    )
    return fig

# --- TITLE & CONFIG ---
st.markdown("<h1 style='text-align: center; font-size: 3rem;'>⚖️ SHADOW AUDITOR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; margin-bottom: 3rem;'>Institutional Forensic Intelligence Platform</p>", unsafe_allow_html=True)

uploaded_files = st.file_uploader("Drop Forensic Evidence (PDFs)", type="pdf", accept_multiple_files=True)
if st.button("EXECUTE FORENSIC AUDIT", type="primary", use_container_width=True):
    if not uploaded_files: st.warning("Requires PDF evidence.")
    else: st.session_state.trigger_audit = True

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
        with st.status("Performing Multi-Document Forensics...", expanded=True) as status:
            full_text = parse_pdfs(unique_files)
            raw_report = run_forensic_audit(full_text)
            st.session_state.last_report = raw_report
            st.session_state.trigger_audit = False

if "last_report" in st.session_state:
    try:
        report_data = st.session_state.last_report
        json_str = report_data.split("=== SHADOW_AUDITOR_RESULT ===")[1].split("=== END_RESULT ===")[0]
        data = json.loads(json_str)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- TOP LEVEL KPI BANNER ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1: st.metric("FRAUD RISK SCORE", f"{data['score']}/100")
        with kpi2: st.markdown(f"### STATUS: <span style='color:#10b981'>{data['level']}</span>", unsafe_allow_html=True)
        with kpi3: st.markdown(f"### ARCHETYPE: <span style='color:#f43f5e'>{data.get('archetype', 'N/A')}</span>", unsafe_allow_html=True)
        with kpi4: st.markdown(f"### SECTOR: <span style='color:#3b82f6'>{data['industry']}</span>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- TABBED INTELLIGENCE SUITE ---
        tab1, tab2, tab3 = st.tabs(["📊 EXECUTIVE DOSSIER", "🔍 TECHNICAL AUDIT", "📄 EVIDENCE VAULT"])

        with tab1:
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.markdown("### Executive Summary")
                st.markdown(f"<div class='expert-text'>{data['summary']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='layman-text'><b>The Simple Story:</b><br>{data['summary_layman']}</div>", unsafe_allow_html=True)
            with col_b:
                st.markdown("### Risk Vector Analysis")
                st.plotly_chart(create_radar_chart(data['metrics']), use_container_width=True)
                st.info(data.get('industry_context', ''))

        with tab2:
            st.markdown("### Narrative Drift Detected")
            d_col1, d_col2 = st.columns(2)
            with d_col1: st.markdown(f"<div class='expert-text'>{data['drift']}</div>", unsafe_allow_html=True)
            with d_col2: st.markdown(f"<div class='layman-text'><b>Translation:</b><br>{data['drift_layman']}</div>", unsafe_allow_html=True)
            
            st.divider()
            
            st.markdown("### Deterministic Math & Ratios")
            for r in data['ratios']:
                st.markdown(f"<div class='glass-card'><h4>{r['name']}</h4>", unsafe_allow_html=True)
                st.latex(r['formula'])
                st.markdown(f"**Result:** `{r['value']}` | **Audit:** {r['audit']}</div>", unsafe_allow_html=True)

            st.divider()
            
            st.markdown("### Expert vs Layman Deep-Dive")
            a_col1, a_col2 = st.columns(2)
            with a_col1: st.markdown(f"<div class='expert-text'>{data['expert']}</div>", unsafe_allow_html=True)
            with a_col2: st.markdown(f"<div class='layman-text'><b>Translation:</b><br>{data['expert_layman']}</div>", unsafe_allow_html=True)

        with tab3:
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                st.markdown("### Actionable Next Steps")
                st.write(data['next_steps'])
            with e_col2:
                st.markdown("### Verifiable Evidence (Citations)")
                st.markdown(data['citations'])
            
            st.divider()
            with st.expander("AI REASONING TRACE (TRANSPARENCY LOG)"):
                st.markdown(f"```text\n{data['thought_trace']}\n```")

        if st.button("CLEAR & RESET AUDIT"):
            for key in st.session_state.keys(): del st.session_state[key]
            st.rerun()

    except Exception as e:
        st.error(f"Intelligence Processing Error: {e}")
        st.write(st.session_state.last_report)
else:
    st.markdown("<div style='text-align: center; margin-top: 5rem; color: #64748b;'>Awaiting forensic evidence for ingestion...</div>", unsafe_allow_html=True)
