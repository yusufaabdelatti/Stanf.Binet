# 🧠 PsychReport AI

**A production-ready Streamlit application for generating professional psychological assessment reports using AI interpretation.**

Built with Grok AI (xAI), ReportLab, and Streamlit.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📂 File Upload | PDF, DOCX, DOC — text-based |
| 🔍 Smart Extraction | Auto-extracts demographics + 50+ test score types |
| ✏️ Editable Review | Full data editor before processing |
| 🌐 Bilingual | English & Arabic output |
| 🏢 Custom Branding | Logo, center name, clinician name |
| ✨ AI Interpretation | Grok AI — score-only input, no hallucination |
| 📊 Visualizations | Bar charts + radar charts (Plotly) |
| 📄 PDF Report | Professional ReportLab layout |
| 📝 DOCX Report | Optional Word document version |
| 📧 Email Delivery | SMTP (Gmail) with HTML email + PDF attachment |

---

## 🗂 Project Structure

```
psych_report_app/
├── app.py                        # Main Streamlit application
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
├── .streamlit/
│   ├── config.toml               # Streamlit theme & server config
│   └── secrets.toml              # 🔐 API keys (DO NOT commit)
└── utils/
    ├── __init__.py
    ├── parser.py                 # PDF/DOCX text + score extraction
    ├── validator.py              # Data validation & issue detection
    ├── ai_engine.py              # Grok API wrapper
    ├── report_generator.py       # ReportLab PDF + DOCX generation
    └── email_sender.py           # SMTP email delivery
```

---

## 🚀 Deploy to Streamlit Cloud (GitHub)

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: PsychReport AI"
git remote add origin https://github.com/YOUR_USERNAME/psych-report-ai.git
git push -u origin main
```

> ⚠️ Make sure `.streamlit/secrets.toml` is in your `.gitignore` and is **NOT** pushed to GitHub.

---

### Step 2 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Connect your GitHub repository
4. Set **Main file path** to: `app.py`
5. Click **"Deploy"**

---

### Step 3 — Add Secrets on Streamlit Cloud

1. In your deployed app dashboard, click **"⋮" → Settings → Secrets**
2. Paste the following (replace with your real values):

```toml
GROK_API_KEY = "xai-your-grok-api-key-here"

# Only needed for email feature:
EMAIL_USER = "your-gmail@gmail.com"
EMAIL_PASS = "your-gmail-app-password"
```

3. Click **Save** — the app will restart automatically.

---

## 🔑 Getting Your API Keys

### Grok API Key (Required)
1. Go to [console.x.ai](https://console.x.ai/)
2. Sign in with your X (Twitter) account
3. Create an API key under **"API Keys"**
4. Copy the key — it starts with `xai-`

### Gmail App Password (for Email feature)
Gmail no longer allows regular passwords for SMTP. You must use an **App Password**:

1. Go to your [Google Account](https://myaccount.google.com/)
2. **Security** → **2-Step Verification** (enable it if not already)
3. **Security** → **App Passwords**
4. Generate a new app password for "Mail"
5. Use that 16-character password as `EMAIL_PASS`

---

## 💻 Run Locally

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/psych-report-ai.git
cd psych-report-ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add your secrets locally
# Edit .streamlit/secrets.toml with your actual keys

# Run the app
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📋 Supported Tests & Scores

The parser automatically detects scores from these instruments (and more):

**Cognitive / IQ**
- WISC-V, WAIS-IV: FSIQ, VCI, PRI, WMI, PSI, FRI, VSI, GAI

**Academic Achievement**
- WIAT-III, WJ-IV: Reading, Math, Written Expression, Spelling

**Memory**
- CVLT, WMS: Immediate, Delayed, Visual, Auditory Memory

**Adaptive Behavior**
- ABAS, Vineland: Conceptual, Social, Practical, Composite

**Attention / ADHD**
- Conners, BASC: Inattention, Hyperactivity, ADHD Index

**Emotional / Behavioral**
- BASC-3, CBCL: Internalizing, Externalizing, Total Problems

**Executive Function**
- BRIEF-2: BRI, MI, GEC, Inhibit, Shift, Emotional Control, etc.

**Autism**
- ADOS-2: Social Communication, RRB

---

## 🔒 Privacy & Security

- Files are processed in-memory and never stored on disk
- No patient data is retained between sessions
- All API calls are made server-side via your own API key
- Reports are generated and downloaded directly to the user's device
- Email delivery uses TLS-encrypted SMTP

---

## 🛠 Troubleshooting

| Problem | Solution |
|---|---|
| "No scores detected" | Use Step 2 editor to add scores manually |
| "Grok API error 401" | Check your `GROK_API_KEY` in secrets |
| "Gmail auth failed" | Use an App Password, not your regular Gmail password |
| "PDF has no charts" | Install kaleido: `pip install kaleido` |
| Scanned PDF not working | App requires text-based PDFs (not image scans) |

---

## 📦 Dependencies

```
streamlit          >= 1.35.0   — Web application framework
pdfplumber         >= 0.11.0   — PDF text extraction (primary)
PyMuPDF            >= 1.24.0   — PDF text extraction (fallback)
python-docx        >= 1.1.2    — DOCX reading and writing
plotly             >= 5.22.0   — Interactive charts
kaleido            >= 0.2.1    — Chart export to PNG for PDF embedding
reportlab          >= 4.2.0    — Professional PDF generation
Pillow             >= 10.3.0   — Image processing
pandas             >= 2.2.0    — Data editing tables
requests           >= 2.32.0   — Grok API HTTP calls
```

---

## 📄 License

MIT License — free for personal and commercial use.

---

## 🙏 Credits

- **AI**: [Grok by xAI](https://x.ai/)
- **Framework**: [Streamlit](https://streamlit.io/)
- **PDF Engine**: [ReportLab](https://www.reportlab.com/)
- **Charts**: [Plotly](https://plotly.com/)
