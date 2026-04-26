import json
import os
import tempfile
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from database import (
  ANALYSIS_RESULTS_FILE,
  JOB_DESCRIPTIONS_FILE,
  RESUMES_FILE,
  save_analysis_result,
  save_job_description,
  save_resume,
  get_previous_analyses,
)
from resume_parser import extract_text_from_pdf, extract_text_from_docx
from nlp_processor import preprocess_text, extract_skills, extract_entities, extract_job_requirements
from ranking_system import calculate_similarity, rank_resumes
from utils import display_resume_details, get_top_keywords, generate_chatbot_response, ai_chatbot_response

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def ensure_session_defaults():
  """Initialize all session state keys used by this page."""
  defaults = {
    "processed_resumes": None,
    "job_skills": None,
    "job_requirements": None,
    "ranked_resumes": None,
    "messages": [],
  }
  for key, default in defaults.items():
    if key not in st.session_state:
      st.session_state[key] = default


def as_list(value):
  """Normalize legacy/serialized list-like values into a list."""
  if value is None:
    return []
  if isinstance(value, list):
    return value
  if isinstance(value, (tuple, set)):
    return list(value)
  if isinstance(value, str):
    return [item.strip() for item in value.split(",") if item.strip()]
  return [value]


def format_date(value):
  """Return a compact date string from an ISO timestamp or raw value."""
  if not value:
    return "Unknown"
  text = str(value)
  if "T" in text:
    return text.split("T")[0]
  if " " in text:
    return text.split(" ")[0]
  return text


def load_json_records(path):
  """Load a JSON list from disk and fall back to an empty list."""
  try:
    if path.exists():
      with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
      return data if isinstance(data, list) else []
  except Exception as exc:
    logger.warning("Could not read %s: %s", path, exc)
  return []


def render_metric_card(label, value, note):
  note_html = f'<div class="metric-note">{note}</div>' if note else ""
  return f"""
  <div class="metric-card">
    <div class="metric-label">{label}</div>
    <div class="metric-value">{value}</div>
    {note_html}
  </div>
  """

# Set page configuration
st.set_page_config(
  page_title="AI Resume Scanner",
  page_icon="AI",
  layout="wide"
)

# Use a dark Plotly template to match the app theme
pio.templates.default = "plotly_dark"

# Minor utility styles for sticky chat panel and chips
st.markdown(
    """
    <style>
      .sticky-panel { position: sticky; top: 1rem; }
      .chip-btn button {
        background: #13233a !important;
        color: var(--text) !important;
        border: 1px solid #1c3354 !important;
        border-radius: 999px !important;
        padding: .3rem .8rem !important;
        font-size: .85rem !important;
      }
      .chip-btn button:hover { border-color: var(--primary) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Custom CSS with a clean, professional design system
st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
      --bg: #0b1220;
      --surface: #0f172a;
      --card: #111e2e;
        --text: #e5e7eb;
        --muted: #9aa4b2;
        --primary: #4ea1f7;
        --primary-600: #3b82f6;
        --ring: rgba(78, 161, 247, 0.24);
        --shadow: 0 1px 2px rgba(0,0,0,.6), 0 8px 24px rgba(0,0,0,.5);
        --radius: 12px;
      }

    html, body, [class*="css"] {
      font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      color: var(--text);
      background: var(--bg);
    }

    .main { padding: .9rem; }

    /* Top bar */
    .topbar { position: sticky; top: 0; z-index: 1000; background: var(--bg); border-bottom: 1px solid #1f2a44; }
    .topbar-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; padding: .55rem .8rem; }
    .brand { display: flex; align-items: center; gap: .6rem; font-weight: 700; color: var(--text); }
    .brand img { width: 28px; height: 28px; }
    .status-pill {
      color: #d6e8ff;
      background: rgba(78, 161, 247, .12);
      border: 1px solid rgba(78, 161, 247, .24);
      border-radius: 999px;
      padding: .22rem .7rem;
      font-size: .82rem;
      font-weight: 600;
      white-space: nowrap;
    }

    /* Headings */
    .stTitle { color: var(--text); font-size: clamp(1.6rem, 2.6vw, 2.35rem) !important; font-weight: 700; letter-spacing: -0.01em; margin-bottom: .15rem; }
    .section-title { color: var(--text); font-weight: 600; margin: 0; }

    /* Buttons */
    .stButton button {
      background: var(--primary);
      color: #fff;
      border: 1px solid var(--primary);
      border-radius: 10px;
      padding: .5rem .95rem;
      font-weight: 600;
      box-shadow: var(--shadow);
      transition: background .15s ease, transform .05s ease;
    }
    .stButton button:hover { background: var(--primary-600); }
    .stButton button:active { transform: translateY(1px); }

    /* Inputs */
    div[data-testid="stFileUploader"], textarea, .css-ocqkz7 { /* streamlit text areas */
      border-radius: var(--radius) !important;
      border: 1px solid #e6ebf3 !important;
      box-shadow: none !important;
    }
    div[data-testid="stFileUploader"] { background: var(--card); padding: .85rem; }
    div[data-testid="stFileUploader"]:hover { box-shadow: var(--shadow); border-color: var(--primary); }

    /* Cards */
    .card { background: var(--card); border: 1px solid #243144; border-radius: var(--radius); padding: .85rem; box-shadow: var(--shadow); }
    .card.accent { border-top: 3px solid var(--primary); }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { padding: 7px 11px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: var(--surface); border-radius: 8px 8px 0 0; color: var(--text); border-bottom: 2px solid var(--primary); }

    /* DataFrame */
    div[data-testid="stDataFrame"] > div { border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); background: var(--card); }

    /* Utilities */
    .muted { color: var(--muted); }
    .hero {
      max-width: 1200px;
      margin: 0 auto .95rem auto;
      padding: .72rem;
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(17, 30, 46, 0.98) 0%, rgba(11, 18, 32, 0.98) 100%);
      border: 1px solid #243144;
      box-shadow: var(--shadow);
      display: grid;
      grid-template-columns: 1.5fr 1fr;
      gap: .65rem;
      align-items: stretch;
    }
    .hero h1 { margin: 0 0 .28rem 0; font-weight: 800; letter-spacing: -.03em; font-size: clamp(1.65rem, 2.9vw, 2.65rem); }
    .hero-copy { display: flex; flex-direction: column; justify-content: center; gap: .55rem; }
    .eyebrow {
      display: inline-flex;
      width: fit-content;
      padding: .28rem .6rem;
      border-radius: 999px;
      background: rgba(78, 161, 247, .12);
      color: #d6e8ff;
      border: 1px solid rgba(78, 161, 247, .24);
      font-size: .76rem;
      font-weight: 700;
      letter-spacing: .08em;
      text-transform: uppercase;
    }
    .hero-actions { display: flex; flex-wrap: wrap; gap: .4rem; }
    .hero-panel {
      background: rgba(15, 23, 42, .88);
      border: 1px solid #243144;
      border-radius: 16px;
      padding: .72rem;
      display: grid;
      gap: .45rem;
    }
    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: .5rem;
      margin-bottom: .9rem;
    }
    .metric-card {
      background: rgba(17, 30, 46, .92);
      border: 1px solid #243144;
      border-radius: 16px;
      padding: .72rem;
      box-shadow: var(--shadow);
    }
    .metric-label { color: var(--muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; }
    .metric-value { color: var(--text); font-size: 1.18rem; font-weight: 800; margin-top: .1rem; }
    .metric-note { color: var(--muted); font-size: .76rem; margin-top: .2rem; line-height: 1.25; }
    .surface-panel {
      background: rgba(15, 23, 42, .9);
      border: 1px solid #243144;
      border-radius: 16px;
      padding: .72rem .85rem;
      box-shadow: var(--shadow);
    }
    .surface-panel h3,
    .surface-panel h4 {
      color: var(--text);
      margin: 0;
    }
    .surface-panel p {
      color: var(--muted);
      margin: .35rem 0 0 0;
    }
    .panel-kicker {
      margin: 0;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .08em;
      font-size: .78rem;
      font-weight: 700;
    }
    .section-banner {
      text-align: center;
      padding: .7rem .9rem;
      background: var(--surface);
      border: 1px solid #243144;
      color: var(--text);
      border-radius: 10px;
      margin-bottom: .85rem;
      box-shadow: var(--shadow);
    }
    .badge { background: #13233a; color: var(--primary); border: 1px solid #1c3354; padding: .32rem .6rem; border-radius: 999px; font-weight: 600; font-size: .83rem; }
    .intro-card {
      display: grid;
      grid-template-columns: 1.2fr .8fr;
      gap: .8rem;
      align-items: center;
    }
    .intro-card ul {
      margin: .5rem 0 0 1rem;
      padding: 0;
      color: var(--muted);
    }
    .intro-card li { margin-bottom: .35rem; }

    @media (max-width: 768px) {
      .main { padding: .72rem; }
      .topbar-inner { padding: .5rem .65rem; }
      .brand { gap: .45rem; }
      .brand img { width: 24px; height: 24px; }
      .status-pill { padding: .18rem .55rem; font-size: .75rem; }
      .hero { grid-template-columns: 1fr; }
    }
    @media (min-width: 1100px) {
      .dashboard-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    }
    </style>
    """, unsafe_allow_html=True)

ensure_session_defaults()

# --- Top Navigation Bar (minimal, professional) ---
st.markdown('''
    <div class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <img src="https://img.icons8.com/ios-filled/50/1f67b1/resume.png" alt="Logo"/>
          <span>AI Resume Scanner</span>
        </div>
        <div class="status-pill">Compact view</div>
      </div>
    </div>
    <div style="height: 8px;"></div>
''', unsafe_allow_html=True)

# --- Hero Section (clean, subtle gradient) ---
st.markdown("""
<div class="hero">
  <div class="hero-copy">
    <span class="eyebrow">Resume screening</span>
    <h1>AI Resume Scanner</h1>
    <p class="muted" style="font-size: .96rem; margin: 0;">Rank PDF and DOCX resumes fast.</p>
    <div class="hero-actions">
      <div class="badge">PDF/DOCX</div>
      <div class="badge">Ranked</div>
      <div class="badge">Saved</div>
    </div>
  </div>
  <div class="hero-panel">
    <div class="metric-label">Flow</div>
    <div class="metric-value" style="font-size: 1.08rem;">Brief -> files -> rank</div>
    <div class="metric-note">One pass, one view.</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Add anchor tags for navigation
st.markdown('<a id="resume-analysis"></a>', unsafe_allow_html=True)

resume_records = load_json_records(RESUMES_FILE)
analysis_records = load_json_records(ANALYSIS_RESULTS_FILE)
job_records = load_json_records(JOB_DESCRIPTIONS_FILE)
latest_analysis = get_previous_analyses(limit=1)
latest_candidate = "No analyses yet"
latest_score = "N/A"
if latest_analysis:
  latest_candidate = latest_analysis[0].get("candidate_name", "Unknown")
  latest_score = f"{int(latest_analysis[0].get('similarity_score', 0) * 100)}%"

st.markdown(
  f"""
  <div class="dashboard-grid">
    {render_metric_card("Stored resumes", len(resume_records), "")}
    {render_metric_card("Saved analyses", len(analysis_records), "")}
    {render_metric_card("Job descriptions", len(job_records), "")}
    {render_metric_card("Latest result", latest_score, latest_candidate)}
  </div>
  """,
  unsafe_allow_html=True,
)

# Add tab views for Analyze and History
tab1, tab2, tab3 = st.tabs(["Analyze", "History", "Library"])

# Main page controls with enhanced UI
with tab1:
  st.markdown("""
    <div class='surface-panel' style='margin-bottom: 1.5rem;'>
      <p class='panel-kicker'>Analyze</p>
      <h2 class='section-title' style='margin: .2rem 0 .35rem 0;'>Scan</h2>
      <p style='margin: 0;'>Brief, files, filters.</p>
    </div>
  """, unsafe_allow_html=True)

# Create columns for input controls
  col1, col2 = st.columns([1, 1])

  with col1:
    # Role brief Input with enhanced styling
    st.markdown("""
      <div class='surface-panel' style='margin-bottom: 1rem; animation: slideIn 0.5s ease-in-out;'>
        <h3>Role brief</h3>
        <p>Paste the brief.</p>
      </div>
    """, unsafe_allow_html=True)

    job_description = st.text_area(
      "Job description",
      height=170,
      placeholder="Paste the role brief here...",
      label_visibility="collapsed"
    )

  with col2:
    # Files with enhanced styling
    st.markdown("""
      <div class='surface-panel' style='margin-bottom: 1rem; animation: slideIn 0.5s ease-in-out;'>
        <h3>Files</h3>
        <p>Upload PDF/DOCX resumes.</p>
      </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
      "Resume files",
      type=["pdf", "docx"],
      accept_multiple_files=True,
      label_visibility="collapsed"
    )

    # Filters with enhanced styling
    st.markdown("""
      <div class='surface-panel' style='margin-top: 1.5rem; animation: slideIn 0.5s ease-in-out;'>
        <h3>Filters</h3>
        <p>Set shortlist limits.</p>
      </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
      min_skill_match = st.slider("Min match", 0, 100, 50)
    with col_b:
      top_n = st.slider("Top", 1, 20, 5)

  # Process Button (centered with enhanced styling)
  col3, col4, col5 = st.columns([1, 2, 1])
  with col4:
    process_button = st.button("Analyze", width="stretch")

# Process the uploaded resumes
if process_button and (not uploaded_files or not job_description.strip()):
  st.warning("Please enter a job description and upload at least one resume before analyzing.")

if process_button and uploaded_files and job_description.strip():
  status_text = st.empty()
  progress_bar = st.progress(0)
  status_text.text("Processing resumes and job description...")
  with st.spinner('Processing resumes and job description...'):
    # Create a list to store resume data
    resumes_data = []

    # Reset stale results before starting a new analysis run.
    st.session_state.processed_resumes = None
    st.session_state.ranked_resumes = None

    # Process job description with enhanced extraction
    preprocessed_jd = preprocess_text(job_description)
    job_skills = extract_skills(preprocessed_jd)
    job_requirements = extract_job_requirements(job_description)

    st.session_state.job_skills = job_skills
    st.session_state.job_requirements = job_requirements

    # Save job description to database
    try:
      job_id = save_job_description(job_description, job_skills)
      logger.info(f"Job description saved with ID: {job_id}")
    except Exception as e:
      logger.error(f"Failed to save job description: {str(e)}")
      job_id = None

    # Process each uploaded resume
    for index, uploaded_file in enumerate(uploaded_files, start=1):
      progress_bar.progress(index / len(uploaded_files))
      # Get file extension
      file_extension = os.path.splitext(uploaded_file.name)[1].lower()

      # Create a temporary file to store the uploaded file
      with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name

      try:
        # Extract text based on file type
        if file_extension == '.pdf':
          resume_text = extract_text_from_pdf(temp_file_path)
        elif file_extension == '.docx':
          resume_text = extract_text_from_docx(temp_file_path)
        else:
          continue # Skip unsupported file types

        # Preprocess the resume text
        preprocessed_text = preprocess_text(resume_text)

        # Extract skills and entities from the resume
        resume_skills = extract_skills(preprocessed_text)
        resume_entities = extract_entities(preprocessed_text)

        # Calculate similarity score
        similarity_score = calculate_similarity(
          preprocessed_jd,
          preprocessed_text,
          job_skills,
          resume_skills
        )

        # Determine matching skills
        matching_skills = list(set(job_skills) & set(resume_skills))

        # Get candidate name (use the first person entity or filename if none found)
        candidate_name = None
        for entity in resume_entities:
          if entity[1] == 'PERSON':
            candidate_name = entity[0]
            break

        if not candidate_name:
          candidate_name = os.path.splitext(uploaded_file.name)[0]

        # Add to resumes data
        resumes_data.append({
          'filename': uploaded_file.name,
          'candidate_name': candidate_name,
          'text': resume_text,
          'preprocessed_text': preprocessed_text,
          'skills': resume_skills,
          'matching_skills': matching_skills,
          'similarity_score': similarity_score,
          'match_percentage': int(similarity_score * 100)
        })

        # Save resume and analysis result to database
        if job_id:
          try:
            # Save resume
            resume_id = save_resume(
              uploaded_file.name,
              candidate_name,
              resume_text,
              resume_skills
            )

            # Save analysis result
            result_id = save_analysis_result(
              job_id,
              resume_id,
              similarity_score,
              matching_skills
            )

            logger.info(f"Resume and analysis saved: {resume_id}, {result_id}")
          except Exception as e:
            logger.error(f"Failed to save resume or analysis: {str(e)}")

      except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {str(e)}")

      finally:
        # Remove the temporary file
        if os.path.exists(temp_file_path):
          os.unlink(temp_file_path)

    if not resumes_data:
      st.session_state.processed_resumes = None
      st.session_state.ranked_resumes = None
      st.error("No resumes were successfully processed. Please check your files and try again.")
    else:
      status_text.text(" Processing complete!")
      progress_bar.progress(100)
      # Rank the resumes
      ranked_resumes = rank_resumes(resumes_data)
      st.session_state.processed_resumes = resumes_data
      st.session_state.ranked_resumes = ranked_resumes
      st.success(f"Successfully processed {len(resumes_data)} resumes!")

# Display results if available
if st.session_state.get("ranked_resumes"):
  # Display enhanced job requirements summary
  if st.session_state.get('job_requirements'):
    st.markdown("---")
    st.markdown("""
    <div class='surface-panel' style='animation: slideIn 0.5s ease-in-out; margin-bottom: 1rem;'>
      <h3>Requirements</h3>
    </div>
    """, unsafe_allow_html=True)

    req = st.session_state.job_requirements
    col1, col2, col3 = st.columns(3)

    with col1:
      if req['required_skills']:
        st.markdown("**Required Skills:**")
        for skill in req['required_skills'][:8]: # Show top 8
          st.markdown(f"- {skill}")

      if req['experience_years']:
        st.markdown("**Experience Required:**")
        for exp in req['experience_years']:
          st.markdown(f"- {exp}")

    with col2:
      if req['preferred_skills']:
        st.markdown("**Preferred Skills:**")
        for skill in req['preferred_skills'][:8]: # Show top 8
          st.markdown(f"- {skill}")

      if req['education_requirements']:
        st.markdown("**Education:**")
        for edu in req['education_requirements']:
          st.markdown(f"- {edu}")

    with col3:
      if req['certifications']:
        st.markdown("**Certifications:**")
        for cert in req['certifications']:
          st.markdown(f"- {cert}")

      if req['job_type']:
        st.markdown("**Job Type:**")
        for jtype in req['job_type']:
          st.markdown(f"- {jtype}")

  st.markdown("---")
  st.markdown("""
    <div class='section-banner'>
      <h2 class='section-title'>Results</h2>
    </div>
  """, unsafe_allow_html=True)

  # Filter resumes based on minimum skill match
  filtered_resumes = [
    r for r in st.session_state.ranked_resumes
    if r['match_percentage'] >= min_skill_match
  ]

  # Display top N candidates
  st.markdown(f"""
    <div class='surface-panel' style='animation: slideIn 0.5s ease-in-out; margin-bottom: 1rem;'>
      <h3>Top {min(top_n, len(filtered_resumes))}</h3>
      <p>Min match: {min_skill_match}%</p>
    </div>
  """, unsafe_allow_html=True)

  if not filtered_resumes:
    st.warning(f"No candidates meet the minimum match percentage of {min_skill_match}%. Try adjusting the slider.")
  else:
    # Display candidates in expanders
    for i, resume in enumerate(filtered_resumes[:top_n]):
      with st.expander(f"{i+1}. {resume['filename']} - {resume['match_percentage']}% match"):
        display_resume_details(resume)

    # --- Visualization Section ---
    st.markdown("---")
    st.markdown(
      '''
      <div class='surface-panel' style='animation: slideIn 0.5s ease-in-out; margin-bottom: 1rem;'>
        <h3>Compare</h3>
      </div>
      ''', unsafe_allow_html=True)

    # Prepare data for charts
    chart_data = pd.DataFrame(filtered_resumes[:top_n])
    chart_data['candidate_label'] = chart_data['filename'].apply(lambda x: x[:15] + '...' if len(x) > 15 else x) # Shorten labels

    # Create columns for charts
    viz_col1, viz_col2 = st.columns(2)

    with viz_col1:
      # Bar chart for match percentage
      st.markdown(
        '''
        <div class='surface-panel' style='margin-bottom: 1rem;'>
          <h4>Match %</h4>
        </div>
        ''', unsafe_allow_html=True)
      fig_match = px.bar(
        chart_data,
        x='candidate_label',
        y='match_percentage',
        title="",
        labels={'candidate_label': 'Candidate', 'match_percentage': 'Match %'},
        color='match_percentage',
        color_continuous_scale=px.colors.sequential.Blues
      )
      fig_match.update_layout(xaxis_title=None, yaxis_title="Match %", showlegend=False)
      st.plotly_chart(fig_match, width="stretch")

    with viz_col2:
      # Bar chart for number of matching skills
      st.markdown(
        '''
        <div class='surface-panel' style='margin-bottom: 1rem;'>
          <h4>Skills</h4>
        </div>
        ''', unsafe_allow_html=True)
      chart_data['matching_skill_count'] = chart_data['matching_skills'].apply(len)
      fig_skills = px.bar(
        chart_data,
        x='candidate_label',
        y='matching_skill_count',
        title="",
        labels={'candidate_label': 'Candidate', 'matching_skill_count': 'Skills'},
        color='matching_skill_count',
        color_continuous_scale=px.colors.sequential.Greens
      )
      fig_skills.update_layout(xaxis_title=None, yaxis_title="Skills", showlegend=False)
      st.plotly_chart(fig_skills, width="stretch")

    # --- Keyword Analysis ---
    st.markdown("---")
    st.markdown(
      '''
      <div class='surface-panel' style='animation: slideIn 0.5s ease-in-out; margin-bottom: 1rem;'>
        <h3>Skills</h3>
        <p>Most common matches.</p>
      </div>
      ''', unsafe_allow_html=True)
    top_keywords_df = get_top_keywords(filtered_resumes[:top_n], st.session_state.get("job_skills") or [])
    if not top_keywords_df.empty:
      st.dataframe(top_keywords_df, width="stretch")
    else:
      st.info("No common skills found.")

    # --- Chat Assistant (sticky right panel) ---
    st.markdown("---")
    left_col, right_col = st.columns([3, 2], gap="large")

    with right_col:
      st.markdown(
        '''
        <div class='surface-panel sticky-panel' style='animation: slideIn 0.5s ease-in-out;'>
          <h3>Ask</h3>
          <p style='font-size: 0.9rem; margin-bottom: .6rem;'>Quick prompts.</p>
        </div>
        ''', unsafe_allow_html=True)

      # Toolbar: context toggles, clear, export
      with st.container():
        c1, c2 = st.columns(2)
        include_summary = c1.checkbox("Top candidates", value=True, help="Include top candidates in AI context")
        include_jd = c2.checkbox("Job skills", value=True, help="Include extracted job skills in AI context")

        t1, t2 = st.columns([1, 1])
        if t1.button("Clear", width="stretch"):
          st.session_state.messages = []
        # Export transcript
        transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        st.download_button("Export", data=transcript or "", file_name="assistant_chat.txt", mime="text/plain", width="stretch", key="export_chat_btn")

      # Quick suggestion chips
      st.markdown("<div class='muted' style='margin:.5rem 0 .3rem 0;'>Quick prompts</div>", unsafe_allow_html=True)
      q1, q2, q3 = st.columns(3)
      q4, q5, _ = st.columns(3)
      quick_prompt = None
      if q1.button("Compare top 2", key="qp1", help="Compare the two best candidates"):
        quick_prompt = "Compare the top 2 candidates and explain key differences."
      if q2.button("Who has Python?", key="qp2"):
        quick_prompt = "Which candidates list Python as a skill?"
      if q3.button("Show top 3", key="qp3"):
        quick_prompt = "Show the top 3 candidates with reasons."
      if q4.button("Missing skills C1", key="qp4", help="Missing skills for candidate 1"):
        quick_prompt = "List missing skills for candidate 1 vs the job description."
      if q5.button("Summarize matches", key="qp5"):
        quick_prompt = "Summarize the overall matches and notable strengths."

      # Render chat history
      for message in st.session_state.messages:
        with st.chat_message(message["role"]):
          st.markdown(message["content"])

      # Accept user input or quick prompt
      user_query = st.chat_input("Ask the assistant about the candidates...")
      if quick_prompt and not user_query:
        user_query = quick_prompt

      if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
          st.markdown(user_query)

        with st.chat_message("assistant"):
          with st.spinner("Thinking..."):
            candidates_for_chatbot = filtered_resumes[:top_n]
            # Compose a context-aware prompt for the AI
            context_parts = [
              "You are an AI assistant helping shortlist resumes.",
            ]
            if include_summary:
              context_parts.append("The following are the top candidates:")
              for i, r in enumerate(candidates_for_chatbot):
                skills_str = ", ".join([str(s) for s in (r.get('skills') or [])])
                context_parts.append(f"Candidate {i+1}: {r['filename']} (Match: {r['match_percentage']}%), Skills: {skills_str}")
            if include_jd:
              job_skills_list = [str(s) for s in (st.session_state.get('job_skills') or [])]
              context_parts.append(f"Job skills required: {', '.join(job_skills_list)}.")
            context_parts.append(f"User question: {user_query}")
            context = "\n".join(context_parts)

            ai_response = ai_chatbot_response(context)
            if not ai_response or '[AI Assistant unavailable' in ai_response:
              response = generate_chatbot_response(user_query, candidates_for_chatbot, st.session_state.job_skills)
            else:
              response = ai_response
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown('<a id="analysis-history"></a>', unsafe_allow_html=True)

# History Tab with enhanced UI
with tab2:
  # Concise section header
  st.markdown("""
  <div class='card accent' style='padding: 1rem 1.25rem; margin: 1rem 0 1.5rem 0; border-radius: 16px;'>
    <p style='margin: 0; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); font-size: .78rem; font-weight: 700;'>History</p>
    <h2 class='section-title' style='margin: .2rem 0 .35rem 0;'>Runs</h2>
    <p class='muted' style='margin: 0;'>Recent matches and scores.</p>
  </div>
  """, unsafe_allow_html=True)

# Get previous analyses from the database
  try:
    previous_analyses = get_previous_analyses(limit=20)

    if not previous_analyses:
      # Enhanced empty state message
      st.markdown("""
      <div style='text-align: center; padding: 3rem 1rem; background-color: var(--surface); border-radius: 10px; border: 1px dashed var(--primary); margin: 2rem 0; animation: fadeIn 1s ease-in-out;'>
        <img src="https://cdn.iconscout.com/icon/free/png-256/free-data-not-found-1965034-1662569.png" width="80" style='opacity: 0.6; margin-bottom: 1rem;'>
        <h3 style='color: var(--primary); margin-bottom: 1rem;'>No runs yet</h3>
        <p style='color: var(--muted); max-width: 500px; margin: 0 auto;'>Run an analysis to save history here.</p>
      </div>
      """, unsafe_allow_html=True)
    else:
      # History table with enhanced styling
      st.markdown("""
      <div style='background-color: var(--surface); padding: 1rem; border-radius: 10px; border-left: 4px solid var(--primary); margin-bottom: 1.5rem; animation: slideIn 0.5s ease-in-out;'>
        <h3 style='color: var(--primary); margin-bottom: 0.5rem; display: flex; align-items: center;'>
          Recent
        </h3>
        <p style='color: var(--muted); font-size: 0.9rem; margin-bottom: 0.5rem;'>Matches and scores.</p>
      </div>
      """, unsafe_allow_html=True)

      # Create DataFrame for display
      history_data = [{
        'Date': format_date(analysis.get('created_at')),
        'Candidate': analysis['candidate_name'],
        'Match %': int(analysis['similarity_score'] * 100),
        'Resume File': analysis['filename']
      } for analysis in previous_analyses]

      hist_df = pd.DataFrame(history_data)
      st.dataframe(hist_df, width="stretch")

      # Detailed analysis view with enhanced styling
      st.markdown("""
      <div style='background-color: var(--surface); padding: 1rem; border-radius: 10px; border-left: 4px solid var(--primary); margin: 2rem 0 1rem 0; animation: slideIn 0.5s ease-in-out;'>
        <h3 style='color: var(--primary); margin-bottom: 0.5rem; display: flex; align-items: center;'>
          Open a run
        </h3>
        <p style='color: var(--muted); font-size: 0.9rem; margin-bottom: 0.5rem;'>Open a run for details.</p>
      </div>
      """, unsafe_allow_html=True)

      # Display detailed expandable analysis cards
      for i, analysis in enumerate(previous_analyses):
        matching_skills = as_list(analysis.get('matching_skills', []))
        score = int(analysis['similarity_score'] * 100)

        # Use custom styling for each expander
        with st.expander(f"{i+1}. {analysis['candidate_name']} - {score}% match"):
          col1, col2 = st.columns([1, 1])

          with col1:
            st.markdown(f"""
            <div style='background-color: var(--surface); padding: 1rem; border-radius: 8px; box-shadow: var(--shadow); margin-bottom: 1rem;'>
              <h4 style='color: var(--primary); margin-bottom: 0.7rem; font-size: 1.1rem;'>Info</h4>
              <p><strong>Name:</strong> {analysis['candidate_name']}</p>
              <p><strong>File:</strong> {analysis['filename']}</p>
              <p><strong>Date:</strong> {analysis['created_at']}</p>
              <p><strong>Score:</strong> <span style='color: {"#2e7d32" if score >= 75 else "#ff9800" if score >= 50 else "#d32f2f"}; font-weight: bold;'>{score}%</span></p>
            </div>
            """, unsafe_allow_html=True)

          with col2:
            st.markdown("""
            <h4 style='color: var(--primary); margin-bottom: 0.7rem; font-size: 1.1rem;'>Brief</h4>
            """, unsafe_allow_html=True)
            description_preview = analysis.get('description', '')
            description_preview = description_preview[:400] + "..." if len(description_preview) > 400 else description_preview
            st.text_area(
              "Brief preview",
              description_preview,
              height=120,
              key=f"analysis_desc_{analysis.get('id', i)}",
              disabled=True,
              label_visibility="collapsed",
            )

          # Display matching skills with better formatting
          st.markdown("""
          <h4 style='color: var(--primary); margin: 1rem 0 0.7rem 0; font-size: 1.1rem;'>Match</h4>
          """, unsafe_allow_html=True)

          if matching_skills:
            # Display skills as badges in a flexbox layout
            skills_html = ""
            for skill in matching_skills:
              skills_html += f"""
              <div style='background-color: #13233a;
                    color: var(--primary);
                    padding: 0.4rem 0.8rem;
                    border-radius: 50px;
                    font-size: 0.9rem;
                    display: inline-block;
                    margin: 0.3rem 0.4rem 0.3rem 0;
                    border: 1px solid #1c3354;'>
                {skill}
              </div>
              """
            st.markdown(f"""
            <div style='display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;'>
              {skills_html}
            </div>
            """, unsafe_allow_html=True)
          else:
            st.markdown("<p style='color: #d32f2f;'>None</p>", unsafe_allow_html=True)

  except Exception as e:
    st.error(f"Error loading previous analyses: {str(e)}")

# Library Tab
with tab3:
  # Concise section header
  st.markdown("""
  <div class='card accent' style='padding: 1rem 1.25rem; margin: 1rem 0 1.5rem 0; border-radius: 16px;'>
    <p style='margin: 0; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); font-size: .78rem; font-weight: 700;'>Library</p>
    <h2 class='section-title' style='margin: .2rem 0 .35rem 0;'>Library</h2>
    <p class='muted' style='margin: 0;'>Search saved resumes by name, skills, or text.</p>
  </div>
  """, unsafe_allow_html=True)

# Load all saved resumes from database
  try:
    import json
    resumes_file = RESUMES_FILE
    if resumes_file.exists():
      with open(resumes_file, 'r', encoding='utf-8') as f:
        all_resumes = json.load(f)
    else:
      all_resumes = []

    if not all_resumes:
      st.markdown("""
      <div class='surface-panel' style='text-align: center; padding: 3rem 1rem; border-style: dashed; margin: 2rem 0; animation: fadeIn 1s ease-in-out;'>
        <h3 style='margin-bottom: 1rem;'>No resumes yet</h3>
        <p style='max-width: 500px; margin: 0 auto;'>Run Analyze to build the library.</p>
      </div>
      """, unsafe_allow_html=True)
    else:
      # Search and filter controls
      st.markdown("""
      <div class='surface-panel' style='animation: slideIn 0.5s ease-in-out; margin-bottom: 1rem;'>
        <h3>Saved</h3>
        <p style='font-size: 0.9rem;'>Search names, skills, or text.</p>
      </div>
      """, unsafe_allow_html=True)

      # Search functionality
      col1, col2 = st.columns([3, 1])
      with col1:
        search_term = st.text_input("Search resumes", placeholder="Search resumes...", label_visibility="collapsed")
      with col2:
        sort_by = st.selectbox("Sort by", ["Newest", "Oldest", "Name A-Z", "Name Z-A"])

      # Filter resumes based on search
      filtered_resumes = all_resumes
      if search_term:
        search_lower = search_term.lower()
        filtered_resumes = []
        for resume in all_resumes:
          # Search in candidate name, filename, skills, and text content
          resume_skills = as_list(resume.get('skills', []))
          searchable_content = (
            resume.get('candidate_name', '').lower() + ' ' +
            resume.get('filename', '').lower() + ' ' +
            ' '.join(str(skill) for skill in resume_skills).lower() + ' ' +
            resume.get('text', '').lower()[:500] # First 500 chars for performance
          )
          if search_lower in searchable_content:
            filtered_resumes.append(resume)

      # Sort resumes
      if sort_by == "Newest":
        filtered_resumes.sort(key=lambda x: x.get('created_at', ''), reverse=True)
      elif sort_by == "Oldest":
        filtered_resumes.sort(key=lambda x: x.get('created_at', ''))
      elif sort_by == "Name A-Z":
        filtered_resumes.sort(key=lambda x: x.get('candidate_name', '').lower())
      elif sort_by == "Name Z-A":
        filtered_resumes.sort(key=lambda x: x.get('candidate_name', '').lower(), reverse=True)

      # Display results count
      st.markdown(f"**{len(filtered_resumes)} resumes**")

      if not filtered_resumes:
        st.info("No resumes match your search criteria. Try a different search term.")
      else:
        # Display resumes in a clean grid
        for i, resume in enumerate(filtered_resumes):
          candidate_name = resume.get('candidate_name', 'Unknown')
          filename = resume.get('filename', 'Unknown')
          skills = as_list(resume.get('skills', []))
          created_at = format_date(resume.get('created_at', 'Unknown'))
          resume_text = resume.get('text', '')

          with st.expander(f"{candidate_name} ({filename})"):
            col1, col2 = st.columns([2, 3])

            with col1:
              st.markdown(f"""
              <div style='background-color: var(--surface); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                <h4 style='color: var(--primary); margin-bottom: 0.5rem;'>Info</h4>
                <p><strong>Name:</strong> {candidate_name}</p>
                <p><strong>File:</strong> {filename}</p>
                <p><strong>Date:</strong> {created_at}</p>
                <p><strong>Chars:</strong> {len(resume_text)}</p>
              </div>
              """, unsafe_allow_html=True)

              # Display skills as badges
              if skills:
                st.markdown("**Skills**")
                skills_html = ""
                for skill in skills[:15]: # Show first 15 skills
                  skills_html += f"""
                  <div style='background-color: #13233a;
                        color: var(--primary);
                        padding: 0.3rem 0.6rem;
                        border-radius: 50px;
                        font-size: 0.8rem;
                        display: inline-block;
                        margin: 0.2rem 0.3rem 0.2rem 0;
                        border: 1px solid #1c3354;'>
                    {skill}
                  </div>
                  """
                st.markdown(f"""
                <div style='display: flex; flex-wrap: wrap; gap: 0.3rem; margin-top: 0.5rem;'>
                  {skills_html}
                </div>
                """, unsafe_allow_html=True)

                if len(skills) > 15:
                  st.markdown(f"*... +{len(skills) - 15} skills*")
              else:
                st.markdown("*No skills detected*")

            with col2:
              st.markdown("**Preview**")
              # Show first 800 characters of resume content
              preview_text = resume_text[:800] if resume_text else "No text content available"
              if len(resume_text) > 800:
                preview_text += "..."

              st.markdown(f"""
              <div style='background-color: var(--surface); padding: 1rem; border-radius: 8px; max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 0.9rem; line-height: 1.4; white-space: pre-wrap;'>
                {preview_text}
              </div>
              """, unsafe_allow_html=True)

              # Action buttons
              button_col1, button_col2 = st.columns(2)
              with button_col1:
                if st.button("Copy", key=f"copy_{i}"):
                  st.code(resume_text, language="text")
              with button_col2:
                if st.button("Entities", key=f"analyze_{i}"):
                  # Extract entities for this resume
                  entities = extract_entities(resume_text)
                  st.markdown("**Entities**")
                  if entities:
                    for entity_text, entity_type in entities:
                      st.markdown(f"- **{entity_type}:** {entity_text}")
                  else:
                    st.markdown("*No entities detected*")

  except Exception as e:
    st.error(f"Error loading resumes: {str(e)}")
    st.info("Run Analyze first.")
