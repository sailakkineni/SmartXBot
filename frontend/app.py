# SmartXBot Main Entrypoint
import html
import os
import re
import sys
import streamlit as st
from dotenv import load_dotenv

# Configure backend import paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from backend.resume_parser import parse_uploaded_file
    from backend.tailor_engine import ResumeTailorEngine, load_config
    from backend.exporter import create_docx, create_pdf
except ImportError:
    from resume_parser import parse_uploaded_file
    from tailor_engine import ResumeTailorEngine, load_config
    from exporter import create_docx, create_pdf

# Load environment variables and configuration
load_dotenv()
cfg = load_config()

def render_resume_preview(resume_text: str):
    """
    Renders resume text in Streamlit with guaranteed bullet dots,
    preserved line gaps, bold headings, and gap spacing between company names & dates.
    """
    if not resume_text or not resume_text.strip():
        st.info("No resume text available.")
        return
        
    html_lines = []
    lines = resume_text.splitlines()
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_lines.append('<div style="height: 0.75rem;"></div>')
            continue
            
        escaped = html.escape(line)
        # Convert inline markdown bold (**text**) to HTML <strong>text</strong>
        formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
        
        # Check if header line
        if stripped.startswith("# "):
            clean_text = formatted.replace("# ", "").strip()
            html_lines.append(f'<div style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-top: 0.4rem; margin-bottom: 0.3rem;">{clean_text}</div>')
        elif stripped.startswith("## "):
            clean_text = formatted.replace("## ", "").strip()
            html_lines.append(f'<div style="font-size: 1.0rem; font-weight: 700; color: #1e1b4b; margin-top: 0.75rem; margin-bottom: 0.25rem; text-transform: uppercase; letter-spacing: 0.03em;">{clean_text}</div>')
        elif stripped.startswith("### "):
            clean_text = formatted.replace("### ", "").strip()
            html_lines.append(f'<div style="font-size: 0.95rem; font-weight: 600; color: #312e81; margin-top: 0.5rem; margin-bottom: 0.2rem;">{clean_text}</div>')
        # Check if bullet line (starts with •, -, *, o, ▪, etc.)
        elif re.match(r"^[\s\t]*[•\-*o▪■\u2022\u25aa\u25a0]", stripped):
            clean_bullet = re.sub(r"^[\s\t]*[•\-*o▪■\u2022\u25aa\u25a0]\s*", "", formatted)
            html_lines.append(f'<div style="display: flex; margin-bottom: 0.35rem; padding-left: 0.5rem;"><span style="color: #4338ca; font-weight: bold; margin-right: 0.55rem; font-size: 1.1rem; line-height: 1.2;">•</span><span style="color: #334155; font-size: 0.92rem; line-height: 1.45;">{clean_bullet}</span></div>')
        else:
            # Regular text line with white-space pre-wrap to preserve gaps between title/company and date
            html_lines.append(f'<div style="color: #334155; font-size: 0.92rem; margin-bottom: 0.3rem; white-space: pre-wrap; word-break: break-word;">{formatted}</div>')

    full_html = f"""
    <div style="background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 1.5rem; font-family: 'Inter', sans-serif; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        {''.join(html_lines)}
    </div>
    """
    st.markdown(full_html, unsafe_allow_html=True)


# Page Configuration
st.set_page_config(
    page_title="SmartXBot | ATS Resume Tailor",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Tailwind-inspired Modern UI Styling
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(49, 46, 129, 0.3);
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #c7d2fe;
        font-size: 1.05rem;
        margin-bottom: 0;
    }
    
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4338ca, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-lbl {
        color: #64748b;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }
    
    .pill {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    .pill-p1 { background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
    .pill-p2 { background-color: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
    .pill-p3 { background-color: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; }
    .pill-supported { background-color: #dcfce7; color: #166534; border: 1px solid #86efac; }
    .pill-partial { background-color: #ffedd5; color: #9a3412; border: 1px solid #fdba74; }
    .pill-missing { background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Sample Data Loaders for Instant Demo
SAMPLE_JD = """Senior Technical Project Manager / Business Analyst
Location: Remote / New York, NY
Company: Apex Cloud Solutions

Responsibilities:
- Lead Agile cross-functional teams to deliver enterprise SaaS applications on AWS cloud infrastructure.
- Drive requirements gathering, workflow analysis, User Acceptance Testing (UAT), and system documentation.
- Manage project schedules, backlog refinement, sprint planning, and issue tracking using Jira and Confluence.
- Establish risk management, issue escalation protocols, budget management, and change management procedures.
- Collaborate with stakeholders, vendor management, and technical leads to maintain project lifecycles.
- Leverage AI tools (ChatGPT, Gemini, Copilot) to optimize project documentation and status reporting.

Qualifications:
- 5+ years of experience in Technical Project Management or Business Analysis.
- Strong knowledge of Agile, Scrum, Waterfall, and PMI methodologies.
- Hands-on experience with Jira, ServiceNow, SQL, Python, APIs, and SaaS platforms.
- PMP or Certified Scrum Master (CSM) certification preferred.
"""

SAMPLE_RESUME = """ALEX MORGAN
Email: alex.morgan@email.com | Phone: (555) 019-2831 | New York, NY

PROFESSIONAL SUMMARY
Results-driven Project Manager with 5 years of experience managing software development projects and coordinating technical teams. Skilled in task tracking, stakeholder management, and project execution.

TECHNICAL SKILLS
- Project Tools: Jira, Trello, MS Excel, Word, PowerPoint
- Methodologies: Agile, Scrum, Kanban
- Technical Exposure: Basic Python, SQL, REST APIs, Web Applications

PROFESSIONAL EXPERIENCE
Project Manager | TechFlow Inc. | 2022 – Present
- Coordinated cross-functional engineering teams during product release cycles.
- Managed task backlogs in Jira and organized daily standup meetings for 8 developers.
- Gathered requirements from business users and drafted functional specification docs.
- Assisted with UAT testing prior to quarterly deployments.

Associate Business Analyst | DataSystems LLC | 2019 – 2022
- Conducted workflow analysis and created process flow diagrams for internal tools.
- Supported project schedules, status reporting, and tracking project risks.
- Interfaced with external vendors to clarify technical requirements.

EDUCATION
B.S. in Information Systems | State University, 2019
"""

# Header Banner
st.markdown("""
<div class="main-header">
    <h1>🚀 SmartXBot</h1>
    <p>Upload your Job Description & Candidate Resume to generate a high-scoring, ATS-Optimized Resume</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/google-logo.png", width=44)
    st.title("⚙️ Optimization Settings")
    
    aggressiveness = st.selectbox(
        "Tailoring Strategy",
        options=["Standard Optimization", "Aggressive ATS Keyword Alignment", "Conservative Match"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 💡 Features")
    st.markdown("""
    - Upload **PDF**, **DOCX**, **TXT**
    - **Keyword Coverage & ATS Score**
    - **Side-by-Side Comparison**
    - **One-click Word & PDF Export**
    """)



# Callbacks for File Uploaders
def handle_jd_upload():
    if st.session_state.jd_upload is not None:
        parsed_text = parse_uploaded_file(st.session_state.jd_upload)
        st.session_state.jd_text = parsed_text
        st.session_state.jd_text_area = parsed_text

def handle_res_upload():
    if st.session_state.res_upload is not None:
        file_obj = st.session_state.res_upload
        parsed_text = parse_uploaded_file(file_obj)
        st.session_state.resume_text = parsed_text
        if hasattr(file_obj, "getvalue"):
            st.session_state.resume_bytes = file_obj.getvalue()

# Session State Initialization
if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "resume_bytes" not in st.session_state:
    st.session_state.resume_bytes = None
if "jd_text_area" not in st.session_state:
    st.session_state.jd_text_area = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "tailored_result" not in st.session_state:
    st.session_state.tailored_result = None

# Main Interface Tabs
tab_input, tab_analysis, tab_resume, tab_export = st.tabs([
    "📥 1. Inputs & Files",
    "📊 2. Keyword & Match Analysis",
    "✨ 3. Tailored Resume Preview",
    "💾 4. Export & Download"
])

# ============================================================
# TAB 1: INPUTS & FILES
# ============================================================
with tab_input:
    st.subheader("Step 1: Provide Job Description & Candidate Resume")
    
    col_demo1, col_demo2 = st.columns([1, 4])
    with col_demo1:
        if st.button("🧪 Load Demo Samples", use_container_width=True):
            st.session_state.jd_text = SAMPLE_JD
            st.session_state.resume_text = SAMPLE_RESUME
            st.session_state.jd_text_area = SAMPLE_JD
            st.rerun()
            
    col_jd, col_res = st.columns(2)
    
    with col_jd:
        st.markdown("#### 🎯 Job Description (JD)")
        uploaded_jd = st.file_uploader(
            "Upload JD (.pdf, .docx, .txt)",
            type=["pdf", "docx", "txt"],
            key="jd_upload",
            on_change=handle_jd_upload
        )
        if uploaded_jd and not st.session_state.jd_text:
            st.session_state.jd_text = parse_uploaded_file(uploaded_jd)
            st.session_state.jd_text_area = st.session_state.jd_text
            
        jd_input_text = st.text_area(
            "Or paste Job Description text here:",
            height=300,
            key="jd_text_area"
        )
        st.session_state.jd_text = jd_input_text

    with col_res:
        st.markdown("#### 📄 Candidate Resume")
        uploaded_res = st.file_uploader(
            "Upload Resume File (.pdf, .docx, .txt)",
            type=["pdf", "docx", "txt"],
            key="res_upload",
            on_change=handle_res_upload
        )
        if uploaded_res and not st.session_state.resume_text:
            st.session_state.resume_text = parse_uploaded_file(uploaded_res)
        
        if st.session_state.resume_text:
            st.success("✅ Candidate Resume File Loaded & Formatted")
            with st.expander("👁️ View Extracted Document Preview", expanded=True):
                render_resume_preview(st.session_state.resume_text)
        else:
            st.info("📌 Please upload your Candidate Resume file (.pdf or .docx).")

    st.markdown("---")
    
    col_btn, _ = st.columns([2, 3])
    with col_btn:
        run_process = st.button("🚀 Analyze & Tailor Resume", type="primary", use_container_width=True)

    if run_process:
        # Fallback checks for uploaded files
        if not st.session_state.jd_text and st.session_state.get("jd_upload"):
            st.session_state.jd_text = parse_uploaded_file(st.session_state.jd_upload)
        if not st.session_state.resume_text and st.session_state.get("res_upload"):
            st.session_state.resume_text = parse_uploaded_file(st.session_state.res_upload)

        if not st.session_state.jd_text.strip():
            st.warning("⚠️ Please enter or upload a Job Description.")
        elif not st.session_state.resume_text.strip():
            st.warning("⚠️ Please upload a Candidate Resume file.")
        else:
            with st.spinner("⚡ Extracting keywords, analyzing ATS match, and generating tailored resume..."):
                try:
                    engine = ResumeTailorEngine()
                    
                    # Run ATS Gap Analysis
                    analysis = engine.analyze_match(
                        jd_text=st.session_state.jd_text,
                        resume_text=st.session_state.resume_text
                    )
                    st.session_state.analysis_result = analysis
                    
                    # Run Resume Tailoring Engine
                    tailored = engine.generate_tailored_resume(
                        jd_text=st.session_state.jd_text,
                        resume_text=st.session_state.resume_text,
                        mode=aggressiveness
                    )
                    st.session_state.tailored_result = tailored
                    
                    st.success("✅ Analysis & Resume Tailoring Complete! Navigate tabs to view results.")
                except Exception as e:
                    st.error(f"❌ Error during processing: {str(e)}")

# ============================================================
# TAB 2: KEYWORD & MATCH ANALYSIS
# ============================================================
with tab_analysis:
    if not st.session_state.analysis_result:
        st.info("💡 Run 'Analyze & Tailor Resume' in Step 1 to generate keyword & match metrics.")
    else:
        an = st.session_state.analysis_result
        
        st.subheader("📌 ATS Compatibility Overview")
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        
        with mcol1:
            score = an.get("overall_ats_score", 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{score}%</div>
                <div class="metric-lbl">Overall ATS Match</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mcol2:
            sec_summary = an.get("section_scores", {}).get("summary", 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{sec_summary}%</div>
                <div class="metric-lbl">Summary Match</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mcol3:
            sec_skills = an.get("section_scores", {}).get("skills", 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{sec_skills}%</div>
                <div class="metric-lbl">Skills Match</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mcol4:
            sec_exp = an.get("section_scores", {}).get("experience", 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{sec_exp}%</div>
                <div class="metric-lbl">Experience Match</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"**Analysis Summary**: {an.get('summary_analysis', '')}")

        st.subheader("🏷️ Extracted Keyword & Requirement Coverage")
        keywords_list = an.get("keywords", [])
        
        filter_status = st.radio(
            "Filter by Candidate Evidence Status:",
            ["All", "SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED"],
            horizontal=True
        )
        
        filtered_keywords = [
            k for k in keywords_list 
            if filter_status == "All" or k.get("status") == filter_status
        ]
        
        cols = st.columns(3)
        for idx, kw in enumerate(filtered_keywords):
            col = cols[idx % 3]
            kw_name = kw.get("keyword", "")
            cat = kw.get("category", "")
            prio = kw.get("priority", "P3")
            status = kw.get("status", "UNSUPPORTED")
            
            status_class = "pill-supported" if status == "SUPPORTED" else ("pill-partial" if status == "PARTIALLY_SUPPORTED" else "pill-missing")
            prio_class = "pill-p1" if prio == "P1" else ("pill-p2" if prio == "P2" else "pill-p3")
            
            with col:
                st.markdown(f"""
                <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.85rem; margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: #0f172a; font-size: 0.95rem;">{kw_name}</strong>
                        <span class="pill {prio_class}">{prio}</span>
                    </div>
                    <div style="margin-top: 0.4rem;">
                        <span style="font-size: 0.75rem; color: #64748b;">Cat: {cat}</span> • 
                        <span class="pill {status_class}" style="font-size: 0.7rem;">{status}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #475569; margin-top: 0.4rem;">
                        <em>{kw.get('recommendation', '')}</em>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        col_rec1, col_rec2 = st.columns(2)
        with col_rec1:
            st.subheader("✅ Key Strengths")
            for str_item in an.get("key_strengths", []):
                st.markdown(f"- {str_item}")
        with col_rec2:
            st.subheader("⚠️ Critical Gaps to Address")
            for gap in an.get("critical_gaps", []):
                st.markdown(f"- {gap}")

# ============================================================
# TAB 3: TAILORED RESUME PREVIEW
# ============================================================
with tab_resume:
    if not st.session_state.tailored_result:
        st.info("💡 Run 'Analyze & Tailor Resume' in Step 1 to preview your tailored resume.")
    else:
        tailored = st.session_state.tailored_result
        tailored_md = tailored.get("tailored_resume", "")
        improvements = tailored.get("bullet_improvements", [])
        
        st.subheader("✨ Side-by-Side Resume Comparison")
        
        col_orig, col_tail = st.columns(2)
        with col_orig:
            st.markdown("### 📄 Original Resume")
            render_resume_preview(st.session_state.resume_text)
            
        with col_tail:
            st.markdown("### 🎯 Tailored Resume (ATS Optimized)")
            render_resume_preview(tailored_md)

        st.markdown("---")
        st.subheader("🔍 Bullet-by-Bullet ATS Optimizations")
        for imp in improvements:
            with st.expander(f"✨ Improved Bullet: {imp.get('original', '')[:60]}..."):
                st.markdown(f"**Original**: {imp.get('original', '')}")
                st.markdown(f"**Tailored (ATS)**: {imp.get('tailored', '')}")
                st.markdown(f"**Keywords Added**: `{', '.join(imp.get('added_keywords', []))}`")
                st.markdown(f"**Reasoning**: {imp.get('reason', '')}")

# ============================================================
# TAB 4: EXPORT & DOWNLOAD
# ============================================================
with tab_export:
    if not st.session_state.tailored_result:
        st.info("💡 Run 'Analyze & Tailor Resume' in Step 1 to generate downloadable resume formats.")
    else:
        tailored_md = st.session_state.tailored_result.get("tailored_resume", "")
        
        st.subheader("💾 Export Tailored Resume")
        st.write("Download your ATS-tailored resume in your preferred file format:")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            improvements = st.session_state.tailored_result.get("bullet_improvements", [])
            docx_bytes = create_docx(
                tailored_md,
                original_docx_bytes=st.session_state.get("resume_bytes"),
                bullet_improvements=improvements
            )
            st.download_button(
                label="📄 Download as Word (.docx)",
                data=docx_bytes,
                file_name="tailored_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
            
        with col_dl2:
            pdf_bytes = create_pdf(tailored_md)
            st.download_button(
                label="📕 Download as PDF (.pdf)",
                data=pdf_bytes,
                file_name="tailored_resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with col_dl3:
            st.download_button(
                label="📝 Download as Markdown (.md)",
                data=tailored_md,
                file_name="tailored_resume.md",
                mime="text/markdown",
                use_container_width=True
            )

        st.markdown("---")
        st.subheader("📋 Raw Markdown Code")
        st.code(tailored_md, language="markdown")
