import os
import tempfile
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from database import save_analysis_result, save_job_description, save_resume, get_previous_analyses
from resume_parser import extract_text_from_pdf, extract_text_from_docx
from nlp_processor import preprocess_text, extract_skills, extract_entities, extract_job_requirements
from ranking_system import calculate_similarity, rank_resumes
from utils import display_resume_details, get_top_keywords, generate_chatbot_response, ai_chatbot_response

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="AI Resume Scanner",
    page_icon="📄",
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

        .main { padding: 2rem; }

        /* Top bar */
        .topbar { position: sticky; top: 0; z-index: 1000; background: var(--bg); border-bottom: 1px solid #1f2a44; }
        .topbar-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; padding: .85rem 1rem; }
        .brand { display: flex; align-items: center; gap: .6rem; font-weight: 700; color: var(--text); }
        .brand img { width: 28px; height: 28px; }
        .nav a { color: var(--text); text-decoration: none; font-weight: 500; opacity: .8; padding: .25rem .4rem; border-radius: 6px; }
        .nav a:hover { opacity: 1; background: var(--surface); }

        /* Headings */
        .stTitle { color: var(--text); font-size: clamp(1.8rem, 3.5vw, 3rem) !important; font-weight: 700; letter-spacing: -0.01em; }
        .section-title { color: var(--text); font-weight: 600; margin: 0; }

        /* Buttons */
        .stButton button {
            background: var(--primary);
            color: #fff;
            border: 1px solid var(--primary);
            border-radius: 10px;
            padding: .65rem 1.2rem;
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
        div[data-testid="stFileUploader"] { background: var(--card); padding: 1.1rem; }
        div[data-testid="stFileUploader"]:hover { box-shadow: var(--shadow); border-color: var(--primary); }

        /* Cards */
        .card { background: var(--card); border: 1px solid #243144; border-radius: var(--radius); padding: 1.25rem; box-shadow: var(--shadow); }
        .card.accent { border-top: 3px solid var(--primary); }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] { gap: 2px; }
        .stTabs [data-baseweb="tab"] { padding: 10px 14px; font-weight: 600; }
        .stTabs [aria-selected="true"] { background: var(--surface); border-radius: 8px 8px 0 0; color: var(--text); border-bottom: 2px solid var(--primary); }

        /* DataFrame */
        div[data-testid="stDataFrame"] > div { border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); background: var(--card); }

        /* Utilities */
        .muted { color: var(--muted); }
        .hero { max-width: 1000px; margin: 0 auto 2rem auto; padding: 2rem; border-radius: 18px; background: linear-gradient(180deg, #0f172a 0%, #0b1220 100%); border: 1px solid #1f2a44; box-shadow: var(--shadow); }
        .hero h1 { margin: 0 0 .5rem 0; font-weight: 800; letter-spacing: -.02em; }
        .badges { display: flex; flex-wrap: wrap; gap: .6rem; justify-content: center; }
        .badge { background: #13233a; color: var(--primary); border: 1px solid #1c3354; padding: .4rem .7rem; border-radius: 999px; font-weight: 600; font-size: .9rem; }

        @media (max-width: 768px) { .main { padding: 1rem; } }
        </style>
        """, unsafe_allow_html=True)

# --- Top Navigation Bar (minimal, professional) ---
st.markdown('''
        <div class="topbar">
            <div class="topbar-inner">
                <div class="brand">
                    <img src="https://img.icons8.com/ios-filled/50/1f67b1/resume.png" alt="Logo"/>
                    <span>AI Resume Scanner</span>
                </div>
                <div class="nav" style="display:flex; gap: 1rem;">
                    <a href="#resume-analysis">Resume Analysis</a>
                    <a href="#analysis-history">History</a>
                    <a href="mailto:contact@example.com">Contact</a>
                </div>
            </div>
        </div>
        <div style="height: 8px;"></div>
''', unsafe_allow_html=True)

# --- Hero Section (clean, subtle gradient) ---
st.markdown('''
<div class="hero">
    <h1>AI‑Powered Resume Scanner</h1>
    <p class="muted" style="font-size: 1.05rem; margin: 0 0 1rem 0;">Screen, rank, and compare resumes with advanced AI — a faster, fairer way to shortlist.</p>
    <div class="badges">
        <div class="badge">Upload Resumes</div>
        <div class="badge">AI Skill Matching</div>
        <div class="badge">Instant Ranking</div>
        <div class="badge">Interactive Insights</div>
    </div>
</div>
''', unsafe_allow_html=True)

# Add anchor tags for navigation
st.markdown('<a id="resume-analysis"></a>', unsafe_allow_html=True)

# Application title and description with animated elements
st.title("AI-Powered Resume Scanner")
st.markdown("""
<div class="card accent" style='padding: 1.5rem; border-radius: 12px;'>
    <h3 style='color: var(--text); margin-bottom: 1rem; font-weight: 700;'>👋 Welcome to the Resume Scanner!</h3>
    <p class='muted' style='font-size: 1.05rem; margin-bottom: 1rem;'>This intelligent application uses AI to help you:</p>
    <div style='animation: slideIn 1s ease-in-out;'>
        <div style='display: flex; align-items: center; margin-bottom: 0.7rem;'>
            <div style='background-color: var(--primary); color: #0b1220; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight: 800;'>1</div>
            <div>Match candidate resumes with job descriptions using advanced NLP</div>
        </div>
        <div style='display: flex; align-items: center; margin-bottom: 0.7rem;'>
            <div style='background-color: var(--primary); color: #0b1220; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight: 800;'>2</div>
            <div>Analyze multiple resumes simultaneously to save time</div>
        </div>
        <div style='display: flex; align-items: center; margin-bottom: 0.7rem;'>
            <div style='background-color: var(--primary); color: #0b1220; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight: 800;'>3</div>
            <div>Get detailed skill matching and ranking results</div>
        </div>
        <div style='display: flex; align-items: center; margin-bottom: 0.7rem;'>
            <div style='background-color: var(--primary); color: #0b1220; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight: 800;'>4</div>
            <div>Visualize candidate comparisons with interactive charts</div>
        </div>
        <div style='display: flex; align-items: center; margin-bottom: 0.7rem;'>
            <div style='background-color: var(--primary); color: #0b1220; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight: 800;'>5</div>
            <div>Save and access previous analysis results anytime</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Add tab views for Resume Analysis and History
tab1, tab2, tab3 = st.tabs(["Resume Analysis", "Analysis History", "Resume Viewer"])

# Main page controls with enhanced UI
with tab1:
    st.markdown("""
        <div style='text-align: center; padding: 1.2rem; background: var(--surface); border: 1px solid #243144; color: var(--text); border-radius: 10px; margin-bottom: 2rem; box-shadow: var(--shadow);'>
            <h2 class='section-title' style='margin: 0; display: flex; align-items: center; justify-content: center;'>
                <span style='margin-right: 10px; font-size: 1.3rem;'>⚡</span>Analysis Controls<span style='margin-left: 10px; font-size: 1.3rem;'>⚡</span>
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Create columns for input controls
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Job Description Input with enhanced styling
        st.markdown("""
            <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin-bottom: 1rem; animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: var(--primary); margin-bottom: 0.5rem; display: flex; align-items: center;'>
                    <span style='margin-right: 8px;'>📝</span>Job Description
                </h3>
                <p style='color: var(--muted); font-size: 0.9rem; margin-bottom: 0.5rem;'>Paste the job requirements below. The more detailed it is, the better the matching will be.</p>
            </div>
        """, unsafe_allow_html=True)
        
        job_description = st.text_area("", height=200, placeholder="E.g., Looking for a Python developer with 3+ years of experience in web development, knowledge of Django, Flask, and database systems...")
    
    with col2:
        # Resume Upload with enhanced styling
        st.markdown("""
            <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin-bottom: 1rem; animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: var(--primary); margin-bottom: 0.5rem; display: flex; align-items: center;'>
                    <span style='margin-right: 8px;'>📎</span>Resume Upload
                </h3>
                <p style='color: var(--muted); font-size: 0.9rem; margin-bottom: 0.5rem;'>Upload one or more resumes in PDF or DOCX format to analyze against the job description.</p>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader("", type=["pdf", "docx"], accept_multiple_files=True)
        
        # Analysis Settings with enhanced styling
        st.markdown("""
            <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin-top: 1.5rem; animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: var(--primary); margin-bottom: 0.5rem; display: flex; align-items: center;'>
                    <span style='margin-right: 8px;'>⚙️</span>Analysis Settings
                </h3>
                <p style='color: var(--muted); font-size: 0.9rem; margin-bottom: 0.5rem;'>Customize how candidates are filtered and displayed in the results.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            min_skill_match = st.slider("Min Match %", 0, 100, 50)
        with col_b:
            top_n = st.slider("Top Candidates", 1, 20, 5)
    
    # Process Button (centered with enhanced styling)
    col3, col4, col5 = st.columns([1, 2, 1])
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        process_button = st.button("🔍 Analyze Resumes", use_container_width=True)

# Initialize session state if not already done
if 'processed_resumes' not in st.session_state:
    st.session_state.processed_resumes = None
if 'job_skills' not in st.session_state:
    st.session_state.job_skills = None
if 'job_requirements' not in st.session_state:
    st.session_state.job_requirements = None
if 'ranked_resumes' not in st.session_state:
    st.session_state.ranked_resumes = None
# Add session state for chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []


# Process the uploaded resumes
if process_button and uploaded_files and job_description:
    status_text = st.empty()
    progress_bar = st.progress(0)
    status_text.text("Processing resumes and job description...")
    with st.spinner('Processing resumes and job description...'):
        # Create a list to store resume data
        resumes_data = []

        # Process job description with enhanced extraction
        preprocessed_jd = preprocess_text(job_description)
        job_skills = extract_skills(preprocessed_jd)
        job_entities = extract_entities(preprocessed_jd)
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
        for uploaded_file in uploaded_files:
            progress_bar.progress((uploaded_files.index(uploaded_file) + 1) / len(uploaded_files))
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
                    continue  # Skip unsupported file types

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
                os.unlink(temp_file_path)

        if not resumes_data:
            st.error("No resumes were successfully processed. Please check your files and try again.")
        else:
            status_text.text("✅ Processing complete!")
            progress_bar.progress(100)
            # Rank the resumes
            ranked_resumes = rank_resumes(resumes_data)
            st.session_state.processed_resumes = resumes_data
            st.session_state.ranked_resumes = ranked_resumes
            st.success(f"Successfully processed {len(resumes_data)} resumes!")

# Display results if available
if st.session_state.ranked_resumes:
    # Display enhanced job requirements summary
    if hasattr(st.session_state, 'job_requirements') and st.session_state.job_requirements:
        st.markdown("---")
        st.markdown("""
        <div class="card" style='animation: slideIn 0.5s ease-in-out;'>
            <h3 style='color: var(--primary); margin-bottom: 1rem; display: flex; align-items: center;'>
                <span style='margin-right: 8px;'>📋</span>Job Requirements Analysis
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        req = st.session_state.job_requirements
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if req['required_skills']:
                st.markdown("**Required Skills:**")
                for skill in req['required_skills'][:8]:  # Show top 8
                    st.markdown(f"• {skill}")
            
            if req['experience_years']:
                st.markdown("**Experience Required:**")
                for exp in req['experience_years']:
                    st.markdown(f"• {exp}")
        
        with col2:
            if req['preferred_skills']:
                st.markdown("**Preferred Skills:**")
                for skill in req['preferred_skills'][:8]:  # Show top 8
                    st.markdown(f"• {skill}")
                    
            if req['education_requirements']:
                st.markdown("**Education:**")
                for edu in req['education_requirements']:
                    st.markdown(f"• {edu}")
        
        with col3:
            if req['certifications']:
                st.markdown("**Certifications:**")
                for cert in req['certifications']:
                    st.markdown(f"• {cert}")
                    
            if req['job_type']:
                st.markdown("**Job Type:**")
                for jtype in req['job_type']:
                    st.markdown(f"• {jtype}")

    st.markdown("---")
    st.markdown(
        '''
        <div style='text-align: center; padding: 1.2rem; background: var(--surface); border: 1px solid #243144; color: var(--text); border-radius: 10px; margin-bottom: 2rem; box-shadow: var(--shadow);'>
            <h2 class='section-title' style='margin: 0; display: flex; align-items: center; justify-content: center;'>
                <span style='margin-right: 10px; font-size: 1.3rem;'>📊</span>Analysis Results<span style='margin-left: 10px; font-size: 1.3rem;'>📊</span>
            </h2>
        </div>
        ''', unsafe_allow_html=True)

    # Filter resumes based on minimum skill match
    filtered_resumes = [
        r for r in st.session_state.ranked_resumes
        if r['match_percentage'] >= min_skill_match
    ]

    # Display top N candidates
    st.markdown(f'''
        <div class="card" style='animation: slideIn 0.5s ease-in-out;'>
            <h3 style='color: var(--primary); margin-bottom: 1rem;'>Top {min(top_n, len(filtered_resumes))} Candidates (Min. {min_skill_match}% Match)</h3>
        </div>
    ''', unsafe_allow_html=True)

    if not filtered_resumes:
        st.warning(f"No candidates meet the minimum match percentage of {min_skill_match}%. Try adjusting the slider.")
    else:
        # Display candidates in expanders
        for i, resume in enumerate(filtered_resumes[:top_n]):
            with st.expander(f"**{i+1}. {resume['filename']}** (Match: {resume['match_percentage']}%):"):
                display_resume_details(resume)

        # --- Visualization Section ---
        st.markdown("---")
        st.markdown(
            '''
            <div class="card" style='animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: var(--primary); margin-bottom: 1rem;'>Candidate Comparison</h3>
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
                <div style='background-color: var(--surface); padding: 1rem; border-radius: 10px; border-left: 4px solid var(--primary); margin-bottom: 1rem;'>
                    <h4 style='color: var(--primary); margin-bottom: 0.5rem;'>Match Percentage Comparison</h4>
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
            st.plotly_chart(fig_match, use_container_width=True)

        with viz_col2:
            # Bar chart for number of matching skills
            st.markdown(
                '''
                <div style='background-color: var(--surface); padding: 1rem; border-radius: 10px; border-left: 4px solid var(--primary); margin-bottom: 1rem;'>
                    <h4 style='color: var(--primary); margin-bottom: 0.5rem;'>Matching Skills Count</h4>
                </div>
                ''', unsafe_allow_html=True)
            chart_data['matching_skill_count'] = chart_data['matching_skills'].apply(len)
            fig_skills = px.bar(
                chart_data,
                x='candidate_label',
                y='matching_skill_count',
                title="",
                labels={'candidate_label': 'Candidate', 'matching_skill_count': '# Matching Skills'},
                color='matching_skill_count',
                color_continuous_scale=px.colors.sequential.Greens
            )
            fig_skills.update_layout(xaxis_title=None, yaxis_title="# Skills", showlegend=False)
            st.plotly_chart(fig_skills, use_container_width=True)

        # --- Keyword Analysis ---
        st.markdown("---")
        st.markdown(
            '''
            <div class="card" style='animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: var(--primary); margin-bottom: 1rem;'>Common Matching Skills</h3>
                <p style='color: var(--muted); font-size: 0.9rem;'>Most frequent skills found in the top candidates that match the job description.</p>
            </div>
            ''', unsafe_allow_html=True)
        top_keywords_df = get_top_keywords(filtered_resumes[:top_n], st.session_state.job_skills)
        if not top_keywords_df.empty:
            st.dataframe(top_keywords_df, use_container_width=True)
        else:
            st.info("No common matching skills found among the top candidates.")

        # --- Chat Assistant (sticky right panel) ---
        st.markdown("---")
        left_col, right_col = st.columns([3, 2], gap="large")

        with right_col:
            st.markdown(
                '''
                <div class="card sticky-panel" style='animation: slideIn 0.5s ease-in-out;'>
                    <h3 style='color: var(--primary); margin-bottom: .6rem; display: flex; align-items: center;'>
                        <span style='margin-right: 8px;'>🤖</span>Shortlisting Assistant
                    </h3>
                    <p class='muted' style='font-size: 0.9rem; margin-bottom: .6rem;'>Ask questions or use quick prompts below.</p>
                </div>
                ''', unsafe_allow_html=True)

            # Toolbar: context toggles, clear, export
            with st.container():
                c1, c2 = st.columns(2)
                include_summary = c1.checkbox("Include summary", value=True, help="Include top candidates overview in AI context")
                include_jd = c2.checkbox("Include job skills", value=True, help="Include extracted job skills in AI context")

                t1, t2 = st.columns([1, 1])
                if t1.button("Clear chat", use_container_width=True):
                    st.session_state.messages = []
                # Export transcript
                transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                st.download_button("Export chat", data=transcript or "", file_name="assistant_chat.txt", mime="text/plain", use_container_width=True, key="export_chat_btn")

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

# Analysis History Tab with enhanced UI
with tab2:
    # Animated header
    st.markdown("""
    <div style='text-align: center; padding: 1.2rem; background: var(--surface); border: 1px solid #243144; color: var(--text); border-radius: 10px; margin: 1rem 0 2rem 0; box-shadow: var(--shadow);'>
        <h2 class='section-title' style='margin: 0; display: flex; align-items: center; justify-content: center;'>
            <span style='margin-right: 10px; font-size: 1.5rem;'>📜</span>Analysis History<span style='margin-left: 10px; font-size: 1.5rem;'>📜</span>
        </h2>
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
                <h3 style='color: var(--primary); margin-bottom: 1rem;'>No Previous Analyses</h3>
                <p style='color: var(--muted); max-width: 500px; margin: 0 auto;'>Once you analyze resumes using the Resume Analysis tab, your analysis history will appear here for future reference.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # History table with enhanced styling
            st.markdown("""
            <div style='background-color: var(--surface); padding: 1rem; border-radius: 10px; border-left: 4px solid var(--primary); margin-bottom: 1.5rem; animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: var(--primary); margin-bottom: 0.5rem; display: flex; align-items: center;'>
                    <span style='margin-right: 8px;'>📊</span>Analysis Summary
                </h3>
                <p style='color: var(--muted); font-size: 0.9rem; margin-bottom: 0.5rem;'>Recent resume analyses and their matching scores</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create DataFrame for display
            history_data = [{
                'Date': analysis['created_at'].split('T')[0] if 'T' in analysis['created_at'] else analysis['created_at'].split(' ')[0],
                'Candidate': analysis['candidate_name'],
                'Match %': int(analysis['similarity_score'] * 100),
                'Resume File': analysis['filename']
            } for analysis in previous_analyses]
            
            hist_df = pd.DataFrame(history_data)
            st.dataframe(hist_df, use_container_width=True)
            
            # Detailed analysis view with enhanced styling
            st.markdown("""
            <div style='background-color: var(--surface); padding: 1rem; border-radius: 10px; border-left: 4px solid var(--primary); margin: 2rem 0 1rem 0; animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: var(--primary); margin-bottom: 0.5rem; display: flex; align-items: center;'>
                    <span style='margin-right: 8px;'>🔍</span>Detailed Analysis
                </h3>
                <p style='color: var(--muted); font-size: 0.9rem; margin-bottom: 0.5rem;'>Click on each analysis to see detailed information</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display detailed expandable analysis cards
            for i, analysis in enumerate(previous_analyses):
                matching_skills = analysis.get('matching_skills', [])
                score = int(analysis['similarity_score'] * 100)
                
                # Use custom styling for each expander
                with st.expander(f"{i+1}. {analysis['candidate_name']} - {score}% match"):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style='background-color: var(--surface); padding: 1rem; border-radius: 8px; box-shadow: var(--shadow); margin-bottom: 1rem;'>
                            <h4 style='color: var(--primary); margin-bottom: 0.7rem; font-size: 1.1rem;'>Candidate Information</h4>
                            <p><strong>Name:</strong> {analysis['candidate_name']}</p>
                            <p><strong>Resume:</strong> {analysis['filename']}</p>
                            <p><strong>Analysis Date:</strong> {analysis['created_at']}</p>
                            <p><strong>Match Score:</strong> <span style='color: {"#2e7d32" if score >= 75 else "#ff9800" if score >= 50 else "#d32f2f"}; font-weight: bold;'>{score}%</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <h4 style='color: var(--primary); margin-bottom: 0.7rem; font-size: 1.1rem;'>Job Description</h4>
                        """, unsafe_allow_html=True)
                        st.text_area("", analysis['description'][:400] + "..." if len(analysis['description']) > 400 else analysis['description'], height=120)
                    
                    # Display matching skills with better formatting
                    st.markdown("""
                    <h4 style='color: var(--primary); margin: 1rem 0 0.7rem 0; font-size: 1.1rem;'>Matching Skills</h4>
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
                        st.markdown("<p style='color: #d32f2f;'>No matching skills found</p>", unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading previous analyses: {str(e)}")

# Resume Viewer Tab
with tab3:
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 1.2rem; background: var(--surface); border: 1px solid #243144; color: var(--text); border-radius: 10px; margin: 1rem 0 2rem 0; box-shadow: var(--shadow);'>
        <h2 class='section-title' style='margin: 0; display: flex; align-items: center; justify-content: center;'>
            <span style='margin-right: 10px; font-size: 1.5rem;'>📄</span>Resume Viewer<span style='margin-left: 10px; font-size: 1.5rem;'>📄</span>
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Load all saved resumes from database
    try:
        import json
        import os
        
        resumes_file = os.path.join('data', 'resumes.json')
        if os.path.exists(resumes_file):
            with open(resumes_file, 'r', encoding='utf-8') as f:
                all_resumes = json.load(f)
        else:
            all_resumes = []
        
        if not all_resumes:
            st.markdown("""
            <div style='text-align: center; padding: 3rem 1rem; background-color: var(--surface); border-radius: 10px; border: 1px dashed var(--primary); margin: 2rem 0; animation: fadeIn 1s ease-in-out;'>
                <h3 style='color: var(--primary); margin-bottom: 1rem;'>No Resumes Available</h3>
                <p style='color: var(--muted); max-width: 500px; margin: 0 auto;'>Upload and analyze some resumes first using the Resume Analysis tab, then return here to view them.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Search and filter controls
            st.markdown("""
            <div class="card" style='animation: slideIn 0.5s ease-in-out; margin-bottom: 1rem;'>
                <h3 style='color: var(--primary); margin-bottom: 0.5rem;'>📋 Browse Resumes</h3>
                <p style='color: var(--muted); font-size: 0.9rem;'>Search by name, skills, or content. Click on any resume to view details.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Search functionality
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input("🔍 Search resumes (name, skills, content)", placeholder="e.g., Python, John Doe, machine learning")
            with col2:
                sort_by = st.selectbox("Sort by", ["Newest", "Oldest", "Name A-Z", "Name Z-A"])
            
            # Filter resumes based on search
            filtered_resumes = all_resumes
            if search_term:
                search_lower = search_term.lower()
                filtered_resumes = []
                for resume in all_resumes:
                    # Search in candidate name, filename, skills, and text content
                    searchable_content = (
                        resume.get('candidate_name', '').lower() + ' ' +
                        resume.get('filename', '').lower() + ' ' +
                        ' '.join(resume.get('skills', [])).lower() + ' ' +
                        resume.get('text', '').lower()[:500]  # First 500 chars for performance
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
            st.markdown(f"**Found {len(filtered_resumes)} resume(s)**")
            
            if not filtered_resumes:
                st.info("No resumes match your search criteria. Try a different search term.")
            else:
                # Display resumes in a clean grid
                for i, resume in enumerate(filtered_resumes):
                    candidate_name = resume.get('candidate_name', 'Unknown')
                    filename = resume.get('filename', 'Unknown')
                    skills = resume.get('skills', [])
                    created_at = resume.get('created_at', 'Unknown')
                    resume_text = resume.get('text', '')
                    
                    # Clean up the date
                    if 'T' in created_at:
                        created_at = created_at.split('T')[0]
                    
                    with st.expander(f"📄 {candidate_name} ({filename})"):
                        col1, col2 = st.columns([2, 3])
                        
                        with col1:
                            st.markdown(f"""
                            <div style='background-color: var(--surface); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                                <h4 style='color: var(--primary); margin-bottom: 0.5rem;'>Candidate Info</h4>
                                <p><strong>Name:</strong> {candidate_name}</p>
                                <p><strong>File:</strong> {filename}</p>
                                <p><strong>Uploaded:</strong> {created_at}</p>
                                <p><strong>Text Length:</strong> {len(resume_text)} characters</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Display skills as badges
                            if skills:
                                st.markdown("**Skills Found:**")
                                skills_html = ""
                                for skill in skills[:15]:  # Show first 15 skills
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
                                    st.markdown(f"*... and {len(skills) - 15} more skills*")
                            else:
                                st.markdown("*No skills detected*")
                        
                        with col2:
                            st.markdown("**Resume Content Preview:**")
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
                                if st.button(f"📋 Copy Text", key=f"copy_{i}"):
                                    st.code(resume_text, language="text")
                            with button_col2:
                                if st.button(f"🔍 Full Analysis", key=f"analyze_{i}"):
                                    # Extract entities for this resume
                                    entities = extract_entities(resume_text)
                                    st.markdown("**Extracted Entities:**")
                                    if entities:
                                        for entity_text, entity_type in entities:
                                            st.markdown(f"• **{entity_type}:** {entity_text}")
                                    else:
                                        st.markdown("*No entities detected*")
    
    except Exception as e:
        st.error(f"Error loading resumes: {str(e)}")
        st.info("Make sure you have analyzed some resumes first in the Resume Analysis tab.")

# --- Footer ---
st.markdown('''
    <footer style="margin-top: 3rem; padding: 2rem 0 1rem 0; background: var(--surface); text-align: center; border-top: 1px solid #243144; box-shadow: var(--shadow);">
        <div style="color: var(--text); font-weight: 700; font-size: 1.05rem;">&copy; 2025 AI Resume Scanner &mdash; All Rights Reserved</div>
        <div style="color: var(--muted); font-size: 0.95rem; margin-top: 0.3rem;">Contact: <a href="mailto:contact@example.com" style="color: var(--primary); text-decoration: underline;">contact@example.com</a></div>
    </footer>
''', unsafe_allow_html=True)

# --- Homepage AI Chatbot Assistant ---
if "homepage_messages" not in st.session_state:
    st.session_state.homepage_messages = []

st.markdown("""
<div class="card accent" style='padding: 1.5rem; border-radius: 12px;'>
    <h3 style='color: var(--text); margin-bottom: 1rem; font-weight: 700;'>🤖 Need help with requirements?</h3>
    <p class='muted' style='font-size: 1.05rem; margin-bottom: 1rem;'>Ask the AI assistant anything about job descriptions, skills, or how to use the Resume Scanner.</p>
</div>
""", unsafe_allow_html=True)

for message in st.session_state.homepage_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if homepage_prompt := st.chat_input("Ask the AI assistant about requirements, job descriptions, or skills..."):
    st.session_state.homepage_messages.append({"role": "user", "content": homepage_prompt})
    with st.chat_message("user"):
        st.markdown(homepage_prompt)
    with st.chat_message("assistant"):
        ai_response = ai_chatbot_response(homepage_prompt)
        st.markdown(ai_response)
    st.session_state.homepage_messages.append({"role": "assistant", "content": ai_response})