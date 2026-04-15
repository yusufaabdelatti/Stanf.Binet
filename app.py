"""
app.py
PsychReport AI — Psychological Assessment Report Generator
Main Streamlit Application
"""

import io
import re
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from PIL import Image
from datetime import datetime

from utils.parser import extract_data_from_file
from utils.validator import validate_extracted_data, get_field_label
from utils.ai_engine import generate_interpretation
from utils.report_generator import generate_pdf_report, generate_docx_report
from utils.email_sender import send_report_via_email

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PsychReport AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1080px; }

/* Step header */
.step-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    color: white;
    padding: 1rem 1.6rem;
    border-radius: 12px;
    margin-bottom: 1.4rem;
    display: flex;
    align-items: center;
    gap: 14px;
}
.step-badge {
    background: rgba(255,255,255,0.2);
    border-radius: 50%;
    width: 34px; height: 34px;
    display: inline-flex;
    align-items: center; justify-content: center;
    font-weight: 700; font-size: 1rem; flex-shrink: 0;
}
.step-title { font-size: 1.15rem; font-weight: 600; margin: 0; }
.step-sub   { font-size: 0.82rem; opacity: 0.8; margin: 2px 0 0 0; }

/* Cards */
.card {
    background: white;
    border-radius: 12px;
    padding: 1.6rem 1.8rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
    margin-bottom: 1.4rem;
}

/* Alert boxes */
.alert-warning {
    background: #fffbeb; border: 1px solid #fcd34d;
    border-left: 4px solid #f59e0b;
    border-radius: 8px; padding: 0.8rem 1.1rem; margin: 0.5rem 0;
    font-size: 0.88rem;
}
.alert-error {
    background: #fef2f2; border: 1px solid #fca5a5;
    border-left: 4px solid #ef4444;
    border-radius: 8px; padding: 0.8rem 1.1rem; margin: 0.5rem 0;
    font-size: 0.88rem;
}
.alert-success {
    background: #f0fdf4; border: 1px solid #86efac;
    border-left: 4px solid #22c55e;
    border-radius: 8px; padding: 0.8rem 1.1rem; margin: 0.5rem 0;
    font-size: 0.88rem;
}
.alert-info {
    background: #eff6ff; border: 1px solid #93c5fd;
    border-left: 4px solid #3b82f6;
    border-radius: 8px; padding: 0.8rem 1.1rem; margin: 0.5rem 0;
    font-size: 0.88rem;
}

/* Interpretation */
.interp-box {
    background: #f8faff;
    border: 1px solid #c7d7f5;
    border-radius: 10px;
    padding: 1.4rem 1.8rem;
    line-height: 1.9;
    font-size: 0.95rem;
    color: #1e293b;
    white-space: pre-wrap;
}

/* Metric mini cards */
.mini-metric {
    background: #f0f4ff;
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    border-left: 4px solid #2563eb;
    margin-bottom: 0.5rem;
}
.mini-label { font-size: 0.72rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing:.05em; }
.mini-value { font-size: 1.3rem; font-weight: 700; color: #1e3a5f; margin-top: 3px; }

/* Sidebar */
.sidebar-brand { text-align: center; padding: 1rem 0 1.5rem; }

/* Buttons */
.stButton>button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton>button:hover { transform: translateY(-1px) !important; }

/* Data editor */
.stDataEditor { border-radius: 8px !important; }

/* Progress step bar */
.progress-bar-wrap {
    display: flex; align-items: center;
    gap: 0; margin: 0 0 2rem 0;
    background: #f1f5f9;
    border-radius: 40px;
    padding: 4px;
    overflow: hidden;
}
.pb-step {
    flex: 1; padding: 7px 4px;
    text-align: center;
    font-size: 0.78rem; font-weight: 600;
    border-radius: 36px;
    transition: all 0.3s;
    color: #94a3b8;
}
.pb-active { background: #2563eb; color: white; }
.pb-done   { background: #22c55e; color: white; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
_defaults = {
    "step": 1,
    "raw_extracted": None,       # dict from parser
    "confirmed_demographics": None,
    "confirmed_scores": None,
    "language": "English",
    "logo_bytes": None,
    "center_name": "",
    "clinician_name": "",
    "interpretation": None,
    "pdf_bytes": None,
    "docx_bytes": None,
    "bar_fig": None,
    "radar_fig": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def go_to_step(n: int):
    st.session_state.step = n


def step_header(number: int, title: str, subtitle: str = ""):
    sub_html = f"<p class='step-sub'>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div class="step-header">
        <span class="step-badge">{number}</span>
        <div>
            <p class="step-title">{title}</p>
            {sub_html}
        </div>
    </div>""", unsafe_allow_html=True)


def progress_bar():
    step_labels = ["Upload", "Review", "Language & Brand", "Generate", "Deliver"]
    parts = []
    for i, label in enumerate(step_labels, start=1):
        if i < st.session_state.step:
            cls = "pb-step pb-done"
            txt = f"✓ {label}"
        elif i == st.session_state.step:
            cls = "pb-step pb-active"
            txt = label
        else:
            cls = "pb-step"
            txt = label
        parts.append(f'<div class="{cls}">{txt}</div>')
    st.markdown(f'<div class="progress-bar-wrap">{"".join(parts)}</div>', unsafe_allow_html=True)


def alert(msg: str, kind: str = "info"):
    icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
    st.markdown(
        f'<div class="alert-{kind}">{icons.get(kind,"")} {msg}</div>',
        unsafe_allow_html=True,
    )


def classification_badge(score) -> str:
    try:
        s = int(score)
    except (ValueError, TypeError):
        return "—"
    if s >= 130:
        return "🟣 Very Superior"
    elif s >= 120:
        return "🔵 Superior"
    elif s >= 110:
        return "🟦 High Average"
    elif s >= 90:
        return "🟢 Average"
    elif s >= 80:
        return "🟡 Low Average"
    elif s >= 70:
        return "🟠 Borderline"
    else:
        return "🔴 Extremely Low"


def build_bar_chart(scores: list[dict]) -> go.Figure:
    valid = [s for s in scores if str(s.get("score", "")).strip() not in ("", "None")]
    if not valid:
        return None

    names  = [s["test"] for s in valid]
    values = [int(s["score"]) for s in valid]

    # Color by score band
    bar_colors = []
    for v in values:
        if v >= 130:   bar_colors.append("#7c3aed")
        elif v >= 120: bar_colors.append("#2563eb")
        elif v >= 110: bar_colors.append("#0891b2")
        elif v >= 90:  bar_colors.append("#16a34a")
        elif v >= 80:  bar_colors.append("#d97706")
        elif v >= 70:  bar_colors.append("#ea580c")
        else:          bar_colors.append("#dc2626")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names, y=values,
        marker_color=bar_colors,
        text=values,
        textposition="outside",
        textfont=dict(size=12, family="Inter"),
        hovertemplate="<b>%{x}</b><br>Score: %{y}<extra></extra>",
    ))

    # Reference lines
    for val, label, color in [(70,"Borderline","#ea580c"), (90,"Average","#16a34a"), (110,"High Avg","#0891b2"), (130,"Superior","#7c3aed")]:
        fig.add_hline(
            y=val, line_dash="dot", line_color=color, line_width=1,
            annotation_text=label, annotation_position="right",
            annotation_font_size=9, annotation_font_color=color,
        )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter", size=11, color="#1e293b"),
        margin=dict(t=40, b=120, l=60, r=80),
        yaxis=dict(range=[40, max(values) + 20], gridcolor="#f1f5f9", title="Standard Score"),
        xaxis=dict(tickangle=-35, tickfont=dict(size=10)),
        showlegend=False,
        height=430,
    )
    return fig


def build_radar_chart(scores: list[dict]) -> go.Figure:
    valid = [s for s in scores if str(s.get("score", "")).strip() not in ("", "None")]
    if len(valid) < 3:
        return None

    names  = [s["test"] for s in valid]
    values = [int(s["score"]) for s in valid]

    # Wrap long names
    short_names = [n[:25] + ("…" if len(n) > 25 else "") for n in names]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=short_names + [short_names[0]],
        fill="toself",
        fillcolor="rgba(37,99,235,0.15)",
        line=dict(color="#2563eb", width=2),
        marker=dict(size=6, color="#2563eb"),
        hovertemplate="<b>%{theta}</b><br>Score: %{r}<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="white",
            radialaxis=dict(
                range=[40, 150],
                tickvals=[70, 85, 100, 115, 130],
                gridcolor="#e2e8f0",
                linecolor="#e2e8f0",
                tickfont=dict(size=9),
            ),
            angularaxis=dict(tickfont=dict(size=9)),
        ),
        paper_bgcolor="white",
        font=dict(family="Inter", size=10, color="#1e293b"),
        margin=dict(t=40, b=40, l=80, r=80),
        showlegend=False,
        height=420,
    )
    return fig


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div style="font-size:2.4rem">🧠</div>
        <div style="font-weight:700;font-size:1.18rem;color:#1e3a5f;margin-top:6px">PsychReport AI</div>
        <div style="font-size:0.78rem;color:#64748b;margin-top:2px">Clinical Assessment Platform</div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    step_icons = {1:"📂", 2:"🔍", 3:"🌐", 4:"✨", 5:"📤"}
    step_names = {1:"Upload File", 2:"Review Data", 3:"Language & Brand", 4:"Generate Report", 5:"Deliver"}
    for n in range(1, 6):
        cur = st.session_state.step
        if n < cur:
            label = f"✅ {step_names[n]}"
            color = "#22c55e"
        elif n == cur:
            label = f"▶ {step_icons[n]} {step_names[n]}"
            color = "#2563eb"
        else:
            label = f"  {step_icons[n]} {step_names[n]}"
            color = "#94a3b8"
        st.markdown(
            f'<div style="padding:6px 10px;border-radius:6px;color:{color};font-size:0.88rem;font-weight:{"600" if n==st.session_state.step else "400"}">{label}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    if st.session_state.step > 1:
        if st.button("↩ Reset / Start Over", use_container_width=True):
            for k, v in _defaults.items():
                st.session_state[k] = v
            st.rerun()

    st.markdown(
        '<div style="font-size:0.72rem;color:#94a3b8;text-align:center;padding-top:1rem">Powered by Grok AI · v1.0.0</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# STEP 1: FILE UPLOAD
# ─────────────────────────────────────────────
if st.session_state.step == 1:
    progress_bar()
    step_header(1, "Upload Assessment File", "Upload a PDF or DOCX file containing the psychological assessment")

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Drag & drop your file here, or click to browse",
            type=["pdf", "docx", "doc"],
            help="Supported formats: PDF, DOCX, DOC",
        )

        if uploaded:
            col1, col2, col3 = st.columns(3)
            col1.metric("File Name", uploaded.name)
            col2.metric("File Size", f"{uploaded.size / 1024:.1f} KB")
            col3.metric("File Type", uploaded.name.split(".")[-1].upper())

            st.markdown("---")

            if st.button("🔍 Extract Data", type="primary", use_container_width=True):
                with st.spinner("Extracting data from file… This may take a moment."):
                    try:
                        file_bytes = uploaded.read()
                        result = extract_data_from_file(file_bytes, uploaded.name)
                        st.session_state.raw_extracted = result
                        go_to_step(2)
                        alert("Data extracted successfully! Please review and confirm below.", "success")
                        st.rerun()
                    except Exception as e:
                        alert(f"Extraction failed: {str(e)}", "error")
        else:
            st.markdown("""
            <div style="text-align:center;padding:3rem 1rem;color:#94a3b8;">
                <div style="font-size:3rem">📄</div>
                <p style="margin-top:1rem;font-size:0.95rem">No file selected yet</p>
                <p style="font-size:0.82rem">Upload a PDF or DOCX assessment file to get started</p>
            </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Tips
    with st.expander("💡 Tips for best extraction results"):
        st.markdown("""
        - **Text-based PDFs** work best (not scanned images)
        - Ensure the file uses standard formatting with clear labels like `Full Scale IQ: 95`
        - Tables with score values are automatically detected
        - You can manually edit any extracted values in the next step
        - If scores aren't detected, you can add them manually in Step 2
        """)


# ─────────────────────────────────────────────
# STEP 2: REVIEW & EDIT DATA
# ─────────────────────────────────────────────
elif st.session_state.step == 2:
    progress_bar()
    step_header(2, "Review & Confirm Extracted Data", "Edit any incorrect values before generating the report")

    data = st.session_state.raw_extracted

    # Run validation
    validation = validate_extracted_data(
        data.get("demographics", {}),
        data.get("scores", []),
    )

    # Validation summary
    cols = st.columns(3)
    cols[0].metric("Demographics Fields", len(data.get("demographics", {})))
    cols[1].metric("Scores Detected",     len(data.get("scores", [])))
    cols[2].metric(
        "Issues Found",
        f"{validation['errors']} errors, {validation['warnings']} warnings",
    )

    # Show issues
    if validation["errors"] > 0 or validation["warnings"] > 0:
        with st.expander(f"⚠️ Validation Issues ({validation['errors']} errors, {validation['warnings']} warnings)", expanded=True):
            for issue in validation["demo_issues"] + validation["score_issues"]:
                kind = "error" if issue["severity"] == "error" else "warning"
                alert(issue["message"], kind)

    st.markdown("---")

    # ── DEMOGRAPHICS EDITOR ──
    st.markdown("### 👤 Patient Demographics")
    st.markdown("Review and correct the extracted demographic information.")

    demo = data.get("demographics", {})
    demo_conf = data.get("demo_confidence", {})

    DEMO_ORDER = ["name", "age", "gender", "dob", "date_assessed", "education", "referral_reason", "clinician"]
    DEMO_LABELS = {
        "name": "Patient Name",
        "age": "Age",
        "gender": "Gender",
        "dob": "Date of Birth",
        "date_assessed": "Date Assessed",
        "education": "Education Level",
        "referral_reason": "Referral Reason",
        "clinician": "Clinician",
    }

    cols_per_row = 2
    field_list = DEMO_ORDER
    demo_edits = {}

    for i in range(0, len(field_list), cols_per_row):
        row_fields = field_list[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for j, field in enumerate(row_fields):
            val = demo.get(field, "") or ""
            conf = demo_conf.get(field, "low")
            label = DEMO_LABELS.get(field, field)
            suffix = " ⚠️" if conf == "low" or not val else ""
            with cols[j]:
                demo_edits[field] = st.text_input(
                    f"{label}{suffix}",
                    value=val,
                    key=f"demo_{field}",
                    help="⚠️ Low confidence — please verify" if conf == "low" else None,
                )

    st.markdown("---")

    # ── SCORES EDITOR ──
    st.markdown("### 📊 Test Scores")
    st.markdown("Edit scores directly in the table. Scores outside 40–160 will be flagged.")

    scores = data.get("scores", [])

    # Prepare DataFrame
    if scores:
        df = pd.DataFrame(scores)[["test", "score", "percentile", "classification", "confidence"]]
        df.columns = ["Test / Scale", "Score", "Percentile", "Classification", "Confidence"]
        df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
        df["Percentile"] = pd.to_numeric(df["Percentile"], errors="coerce")
    else:
        df = pd.DataFrame(columns=["Test / Scale", "Score", "Percentile", "Classification", "Confidence"])

    alert(
        "You can add new rows, edit values, or delete rows. "
        "The **Confidence** column is for reference only — feel free to ignore it.",
        "info",
    )

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Test / Scale": st.column_config.TextColumn("Test / Scale", width="large"),
            "Score": st.column_config.NumberColumn("Score", min_value=1, max_value=200, step=1),
            "Percentile": st.column_config.NumberColumn("Percentile", min_value=1, max_value=99, step=1),
            "Classification": st.column_config.TextColumn("Classification"),
            "Confidence": st.column_config.TextColumn("Confidence", disabled=True, width="small"),
        },
        key="scores_editor",
    )

    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✅ Confirm & Continue", type="primary", use_container_width=True):
            # Convert edited df back to list of dicts
            confirmed_scores = []
            for _, row in edited_df.iterrows():
                test_name = str(row.get("Test / Scale", "")).strip()
                if not test_name:
                    continue
                confirmed_scores.append({
                    "test": test_name,
                    "score": row.get("Score", ""),
                    "percentile": row.get("Percentile", ""),
                    "classification": str(row.get("Classification", "")).strip(),
                    "confidence": str(row.get("Confidence", "")).strip(),
                })

            st.session_state.confirmed_demographics = demo_edits
            st.session_state.confirmed_scores = confirmed_scores

            # Pre-generate charts
            st.session_state.bar_fig   = build_bar_chart(confirmed_scores)
            st.session_state.radar_fig = build_radar_chart(confirmed_scores)

            go_to_step(3)
            st.rerun()
    with col2:
        if st.button("← Back", use_container_width=True):
            go_to_step(1)
            st.rerun()


# ─────────────────────────────────────────────
# STEP 3: LANGUAGE & BRANDING
# ─────────────────────────────────────────────
elif st.session_state.step == 3:
    progress_bar()
    step_header(3, "Language & Branding", "Customize the report language and your organization's identity")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 🌐 Report Language")
        language = st.radio(
            "Select output language",
            ["English", "Arabic"],
            index=0 if st.session_state.language == "English" else 1,
            help="The entire report (AI interpretation included) will be generated in this language.",
        )
        st.session_state.language = language

        if language == "Arabic":
            alert("The AI will generate the full interpretation in formal Arabic (Modern Standard Arabic).", "info")

        st.markdown("---")
        st.markdown("#### 👤 Clinician Info")
        clinician_name = st.text_input(
            "Clinician / Psychologist Name (optional)",
            value=st.session_state.clinician_name,
            placeholder="e.g. Dr. Sarah Al-Mansouri",
        )
        st.session_state.clinician_name = clinician_name

    with col_right:
        st.markdown("#### 🏢 Organization Branding")
        center_name = st.text_input(
            "Center / Organization Name",
            value=st.session_state.center_name,
            placeholder="e.g. Al Noor Psychology Center",
        )
        st.session_state.center_name = center_name

        st.markdown("**Logo Upload**")
        logo_upload = st.file_uploader(
            "Upload your logo (PNG, JPG)",
            type=["png", "jpg", "jpeg"],
            help="Recommended: square logo, at least 200×200 px",
        )
        if logo_upload:
            st.session_state.logo_bytes = logo_upload.read()
            img = Image.open(io.BytesIO(st.session_state.logo_bytes))
            st.image(img, width=120, caption="Logo preview")
        elif st.session_state.logo_bytes:
            img = Image.open(io.BytesIO(st.session_state.logo_bytes))
            st.image(img, width=120, caption="Logo (previously uploaded)")

    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✅ Continue to Report Generation", type="primary", use_container_width=True):
            go_to_step(4)
            st.rerun()
    with col2:
        if st.button("← Back", use_container_width=True):
            go_to_step(2)
            st.rerun()


# ─────────────────────────────────────────────
# STEP 4: GENERATE REPORT
# ─────────────────────────────────────────────
elif st.session_state.step == 4:
    progress_bar()
    step_header(4, "Generate Report", "AI interprets the scores and builds your professional PDF report")

    demographics = st.session_state.confirmed_demographics or {}
    scores       = st.session_state.confirmed_scores or []
    language     = st.session_state.language
    center_name  = st.session_state.center_name
    clinician    = st.session_state.clinician_name

    # ── SCORE PREVIEW ──
    st.markdown("#### 📊 Score Visualization")
    chart_tab1, chart_tab2 = st.tabs(["Bar Chart", "Radar Chart"])

    with chart_tab1:
        fig_bar = st.session_state.bar_fig
        if fig_bar:
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            alert("No numeric scores available for chart generation.", "warning")

    with chart_tab2:
        fig_radar = st.session_state.radar_fig
        if fig_radar:
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            alert("At least 3 numeric scores are required for a radar chart.", "info")

    st.markdown("---")

    # ── AI INTERPRETATION ──
    st.markdown("#### ✨ AI Clinical Interpretation")

    if st.session_state.interpretation:
        alert("Interpretation already generated. You can regenerate it below.", "success")
        st.markdown(
            f'<div class="interp-box">{st.session_state.interpretation}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

    col_gen, col_regen = st.columns([2, 1])
    with col_gen:
        gen_button_label = "🔄 Regenerate Interpretation" if st.session_state.interpretation else "✨ Generate AI Interpretation"
        if st.button(gen_button_label, type="primary", use_container_width=True):
            with st.spinner("Sending scores to Grok AI… Generating clinical interpretation…"):
                try:
                    interp = generate_interpretation(demographics, scores, language)
                    st.session_state.interpretation = interp
                    st.rerun()
                except ValueError as e:
                    alert(str(e), "error")
                except RuntimeError as e:
                    alert(str(e), "error")
                except Exception as e:
                    alert(f"Unexpected error: {str(e)}", "error")

    st.markdown("---")

    # ── PDF GENERATION ──
    st.markdown("#### 📄 Build PDF Report")

    include_radar = st.checkbox("Include radar chart in PDF", value=True)
    include_docx  = st.checkbox("Also generate DOCX version", value=False)

    if st.session_state.interpretation:
        if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
            with st.spinner("Building your professional PDF report…"):
                try:
                    pdf_bytes = generate_pdf_report(
                        demographics=demographics,
                        scores=scores,
                        interpretation=st.session_state.interpretation,
                        language=language,
                        center_name=center_name,
                        clinician_name=clinician,
                        logo_bytes=st.session_state.logo_bytes,
                        bar_fig=st.session_state.bar_fig,
                        radar_fig=st.session_state.radar_fig if include_radar else None,
                    )
                    st.session_state.pdf_bytes = pdf_bytes

                    if include_docx:
                        docx_bytes = generate_docx_report(
                            demographics=demographics,
                            scores=scores,
                            interpretation=st.session_state.interpretation,
                            language=language,
                            center_name=center_name,
                            clinician_name=clinician,
                            logo_bytes=st.session_state.logo_bytes,
                        )
                        st.session_state.docx_bytes = docx_bytes

                    go_to_step(5)
                    st.rerun()
                except Exception as e:
                    alert(f"PDF generation failed: {str(e)}", "error")
    else:
        alert("Please generate the AI interpretation before building the PDF.", "warning")

    st.markdown("---")
    if st.button("← Back", use_container_width=True):
        go_to_step(3)
        st.rerun()


# ─────────────────────────────────────────────
# STEP 5: DELIVER
# ─────────────────────────────────────────────
elif st.session_state.step == 5:
    progress_bar()
    step_header(5, "Deliver Report", "Download or email the finished report")

    alert("✅ Your report is ready!", "success")

    demographics = st.session_state.confirmed_demographics or {}
    patient_name = demographics.get("name", "patient")
    safe_name    = re.sub(r'[^a-zA-Z0-9_\-]', '_', patient_name)
    date_str     = datetime.now().strftime("%Y%m%d")
    pdf_filename = f"PsychReport_{safe_name}_{date_str}.pdf"
    docx_filename = f"PsychReport_{safe_name}_{date_str}.docx"

    tab_download, tab_email = st.tabs(["⬇️ Option A — Download", "📧 Option B — Send via Email"])

    # ── DOWNLOAD ──
    with tab_download:
        st.markdown("### Download Your Report")

        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.pdf_bytes:
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=st.session_state.pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
            else:
                alert("No PDF available. Please go back and generate the report.", "warning")

        with col2:
            if st.session_state.docx_bytes:
                st.download_button(
                    label="⬇️ Download DOCX Report",
                    data=st.session_state.docx_bytes,
                    file_name=docx_filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            else:
                st.markdown(
                    '<div style="color:#94a3b8;font-size:0.88rem;padding:.5rem">DOCX not generated. Go back to Step 4 and enable the DOCX option.</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown("#### 📄 Report Preview")
        if st.session_state.bar_fig:
            st.plotly_chart(st.session_state.bar_fig, use_container_width=True)

        if st.session_state.interpretation:
            st.markdown("**Clinical Interpretation Preview**")
            st.markdown(
                f'<div class="interp-box">{st.session_state.interpretation[:1200]}{"…" if len(st.session_state.interpretation) > 1200 else ""}</div>',
                unsafe_allow_html=True,
            )

    # ── EMAIL ──
    with tab_email:
        st.markdown("### Send Report via Email")
        alert("The PDF report will be sent as an email attachment.", "info")

        recipient = st.text_input(
            "Recipient Email Address",
            placeholder="doctor@example.com",
        )

        if st.button("📧 Send Report", type="primary", use_container_width=True):
            if not st.session_state.pdf_bytes:
                alert("No PDF to send. Please go back and generate the report first.", "error")
            elif not recipient or "@" not in recipient:
                alert("Please enter a valid email address.", "error")
            else:
                with st.spinner(f"Sending report to {recipient}…"):
                    success, message = send_report_via_email(
                        recipient_email=recipient,
                        pdf_bytes=st.session_state.pdf_bytes,
                        patient_name=patient_name,
                        center_name=st.session_state.center_name,
                        clinician_name=st.session_state.clinician_name,
                        language=st.session_state.language,
                        pdf_filename=pdf_filename,
                    )
                if success:
                    alert(message, "success")
                else:
                    alert(message, "error")

        with st.expander("ℹ️ Email setup instructions"):
            st.markdown("""
            To enable email delivery, add these to your Streamlit secrets:
            ```toml
            EMAIL_USER = "your-gmail@gmail.com"
            EMAIL_PASS = "your-app-password"
            ```
            **Important:** Use a [Gmail App Password](https://support.google.com/accounts/answer/185833),
            not your regular Gmail password.
            Gmail → Account Settings → Security → 2-Step Verification → App Passwords.
            """)

    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back to Generate", use_container_width=True):
            go_to_step(4)
            st.rerun()
    with col2:
        if st.button("🔄 Start New Report", use_container_width=True):
            for k, v in _defaults.items():
                st.session_state[k] = v
            st.rerun()
