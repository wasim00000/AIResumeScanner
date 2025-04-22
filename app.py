import streamlit as st
import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from io import BytesIO
import logging

from resume_parser import extract_text_from_pdf, extract_text_from_docx
from nlp_processor import preprocess_text, extract_skills, extract_entities
from ranking_system import calculate_similarity, rank_resumes
from utils import display_resume_details, get_top_keywords
from database import (
    save_job_description, 
    save_resume, 
    save_analysis_result, 
    get_previous_analyses
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="AI Resume Scanner",
    page_icon="📄",
    layout="wide"
)

# Custom CSS with animations and responsive design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    .main {
        padding: 2rem;
        background-color: #f8f9fa;
        animation: fadeIn 0.8s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .stTitle {
        color: #1f67b1;
        font-size: clamp(2rem, 4vw, 3.5rem) !important;
        padding-bottom: 1.5rem;
        font-weight: 700;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .stMarkdown {
        font-size: clamp(1rem, 1.2vw, 1.3rem);
        line-height: 1.6;
    }
    
    .stButton button {
        background-color: #1f67b1;
        color: white;
        border-radius: 8px;
        padding: 0.6rem 2.5rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(31, 103, 177, 0.2);
        animation: pulse 2s infinite;
    }
    
    .stButton button:hover {
        background-color: #155085;
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(31, 103, 177, 0.3);
    }
    
    div[data-testid="stFileUploader"] {
        padding: 1.5rem;
        border: 2px dashed #1f67b1;
        border-radius: 10px;
        margin: 1rem 0;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.7);
    }
    
    div[data-testid="stFileUploader"]:hover {
        border-color: #155085;
        background: rgba(240, 248, 255, 0.9);
        transform: translateY(-3px);
    }
    
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin: 0.7rem 0;
        transition: all 0.3s ease;
        overflow: hidden;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        animation: slideIn 0.5s ease-in-out;
    }
    
    div[data-testid="stExpander"]:hover {
        border-color: #1f67b1;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stExpander"] > div:first-child {
        background-color: #f5f9ff;
        padding: 0.8rem;
        transition: background-color 0.3s ease;
    }
    
    div[data-testid="stExpander"] > div:first-child:hover {
        background-color: #e9f2ff;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 16px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(31, 103, 177, 0.1);
        border-radius: 5px 5px 0 0;
        color: #1f67b1;
        border-bottom: 2px solid #1f67b1;
    }
    
    /* Cards and containers */
    .card {
        padding: 1.5rem;
        border-radius: 10px;
        background: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        border-left: 5px solid #1f67b1;
    }
    
    .card:hover {
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        transform: translateY(-3px);
    }
    
    /* Make dataframes prettier */
    div[data-testid="stDataFrame"] > div {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
    /* For mobile responsiveness */
    @media screen and (max-width: 768px) {
        .main {
            padding: 1rem;
        }
        
        .stTitle {
            padding-bottom: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Application title and description with animated elements
st.title("AI-Powered Resume Scanner")
st.markdown("""
<div class="card" style='background: linear-gradient(to right, #ffffff, #f0f8ff); padding: 1.5rem; border-radius: 12px; border-left: 5px solid #1f67b1; margin-bottom: 2rem; animation: fadeIn 1s ease-in-out;'>
    <h3 style='color: #1f67b1; margin-bottom: 1rem; font-weight: 600;'>👋 Welcome to the Resume Scanner!</h3>
    <p style='font-size: 1.1rem; margin-bottom: 1rem;'>This intelligent application uses AI to help you:</p>
    <div style='animation: slideIn 1s ease-in-out;'>
        <div style='display: flex; align-items: center; margin-bottom: 0.7rem;'>
            <div style='background-color: #1f67b1; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight: bold;'>1</div>
            <div>Match candidate resumes with job descriptions using advanced NLP</div>
        </div>
        <div style='display: flex; align-items: center; margin-bottom: 0.7rem;'>
            <div style='background-color: #1f67b1; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight: bold;'>2</div>
            <div>Analyze multiple resumes simultaneously to save time</div>
        </div>
        <div style='display: flex; align-items: center; margin-bottom: 0.7rem;'>
            <div style='background-color: #1f67b1; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight: bold;'>3</div>
            <div>Get detailed skill matching and ranking results</div>
        </div>
        <div style='display: flex; align-items: center; margin-bottom: 0.7rem;'>
            <div style='background-color: #1f67b1; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight: bold;'>4</div>
            <div>Visualize candidate comparisons with interactive charts</div>
        </div>
        <div style='display: flex; align-items: center; margin-bottom: 0.7rem;'>
            <div style='background-color: #1f67b1; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; justify-content: center; align-items: center; margin-right: 10px; font-weight: bold;'>5</div>
            <div>Save and access previous analysis results anytime</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Add tab views for Resume Analysis and History
tab1, tab2 = st.tabs(["Resume Analysis", "Analysis History"])

# Main page controls with enhanced UI
with tab1:
    st.markdown("""
        <div style='text-align: center; padding: 1.2rem; background: linear-gradient(90deg, #1f67b1 0%, #4e85c5 100%); color: white; border-radius: 10px; margin-bottom: 2rem; box-shadow: 0 4px 8px rgba(0,0,0,0.1); animation: fadeIn 0.8s ease-in-out;'>
            <h2 style='margin: 0; font-weight: 600; display: flex; align-items: center; justify-content: center;'>
                <span style='margin-right: 10px; font-size: 1.5rem;'>⚡</span>Analysis Controls<span style='margin-left: 10px; font-size: 1.5rem;'>⚡</span>
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Create columns for input controls
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Job Description Input with enhanced styling
        st.markdown("""
            <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin-bottom: 1rem; animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: #1f67b1; margin-bottom: 0.5rem; display: flex; align-items: center;'>
                    <span style='margin-right: 8px;'>📝</span>Job Description
                </h3>
                <p style='color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;'>Paste the job requirements below. The more detailed it is, the better the matching will be.</p>
            </div>
        """, unsafe_allow_html=True)
        
        job_description = st.text_area("", height=200, placeholder="E.g., Looking for a Python developer with 3+ years of experience in web development, knowledge of Django, Flask, and database systems...")
    
    with col2:
        # Resume Upload with enhanced styling
        st.markdown("""
            <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin-bottom: 1rem; animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: #1f67b1; margin-bottom: 0.5rem; display: flex; align-items: center;'>
                    <span style='margin-right: 8px;'>📎</span>Resume Upload
                </h3>
                <p style='color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;'>Upload one or more resumes in PDF or DOCX format to analyze against the job description.</p>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader("", type=["pdf", "docx"], accept_multiple_files=True)
        
        # Analysis Settings with enhanced styling
        st.markdown("""
            <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin-top: 1.5rem; animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: #1f67b1; margin-bottom: 0.5rem; display: flex; align-items: center;'>
                    <span style='margin-right: 8px;'>⚙️</span>Analysis Settings
                </h3>
                <p style='color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;'>Customize how candidates are filtered and displayed in the results.</p>
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
if 'ranked_resumes' not in st.session_state:
    st.session_state.ranked_resumes = None

# Process the uploaded resumes
if process_button and uploaded_files and job_description:
    status_text = st.empty()
    progress_bar = st.progress(0)
    status_text.text("Processing resumes and job description...")
    with st.spinner('Processing resumes and job description...'):
        # Create a list to store resume data
        resumes_data = []

        # Process job description
        preprocessed_jd = preprocess_text(job_description)
        job_skills = extract_skills(preprocessed_jd)
        job_entities = extract_entities(preprocessed_jd)

        st.session_state.job_skills = job_skills
        
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

# Show results in the Analysis tab if available
if st.session_state.ranked_resumes and st.session_state.job_skills:
    with tab1:
        # Animated results header
        st.markdown("""
        <div style='text-align: center; padding: 1.2rem; background: linear-gradient(90deg, #155085 0%, #1f67b1 100%); color: white; border-radius: 10px; margin: 2rem 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1); animation: fadeIn 1s ease-in-out;'>
            <h2 style='margin: 0; font-weight: 600; display: flex; align-items: center; justify-content: center;'>
                <span style='margin-right: 10px; font-size: 1.5rem;'>🏆</span>Resume Ranking Results<span style='margin-left: 10px; font-size: 1.5rem;'>🏆</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
        # Get the ranked resumes
        ranked_resumes = st.session_state.ranked_resumes
        job_skills = st.session_state.job_skills
    
        # Filter by minimum match percentage
        filtered_resumes = [r for r in ranked_resumes if r['match_percentage'] >= min_skill_match]
    
        # Take only top N
        top_resumes = filtered_resumes[:top_n]
    
        if not top_resumes:
            st.warning(f"No resumes meet the minimum skill match criteria of {min_skill_match}%.")
        else:
            # Display results in columns
            col1, col2 = st.columns([2, 1])
    
            with col1:
                # Enhanced Top Candidates Section
                st.markdown("""
                <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin-bottom: 1rem; animation: slideIn 0.5s ease-in-out;'>
                    <h3 style='color: #1f67b1; margin-bottom: 0.5rem; display: flex; align-items: center;'>
                        <span style='margin-right: 8px;'>👥</span>Top Candidates
                    </h3>
                </div>
                """, unsafe_allow_html=True)
    
                # Create a DataFrame for display
                display_data = [{
                    'Candidate': resume['candidate_name'],
                    'Match %': resume['match_percentage'],
                    'Matching Skills': ', '.join(resume['matching_skills'][:5]) + 
                                     ('...' if len(resume['matching_skills']) > 5 else '')
                } for resume in top_resumes]
    
                df_display = pd.DataFrame(display_data)
                st.dataframe(df_display, use_container_width=True)
    
                # Detailed candidate view with enhanced styling
                st.markdown("""
                <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin: 1.5rem 0 1rem 0; animation: slideIn 0.5s ease-in-out;'>
                    <h3 style='color: #1f67b1; margin-bottom: 0.5rem; display: flex; align-items: center;'>
                        <span style='margin-right: 8px;'>📋</span>Candidate Details
                    </h3>
                    <p style='color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;'>Click on each candidate to view detailed information</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Use custom CSS class for expanders
                for i, resume in enumerate(top_resumes):
                    with st.expander(f"{i+1}. {resume['candidate_name']} ({resume['match_percentage']}% match)"):
                        display_resume_details(resume)
    
            with col2:
                # Enhanced Visualizations Section
                st.markdown("""
                <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin-bottom: 1rem; animation: slideIn 0.5s ease-in-out;'>
                    <h3 style='color: #1f67b1; margin-bottom: 0.5rem; display: flex; align-items: center;'>
                        <span style='margin-right: 8px;'>📊</span>Visualizations
                    </h3>
                </div>
                """, unsafe_allow_html=True)
    
                # Bar chart of top candidates with enhanced styling
                fig1 = px.bar(
                    display_data, 
                    x='Match %', 
                    y='Candidate', 
                    orientation='h',
                    title='<b>Resume Match Percentages</b>',
                    labels={'x': 'Match Percentage (%)', 'y': 'Candidate'},
                    color='Match %',
                    color_continuous_scale='viridis',
                    height=350
                )
                
                # Enhance the chart appearance
                fig1.update_layout(
                    plot_bgcolor='rgba(240,248,255,0.3)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Roboto, sans-serif", size=12),
                    margin=dict(l=10, r=10, t=40, b=10),
                    xaxis=dict(gridcolor='rgba(200,200,200,0.2)'),
                    yaxis=dict(gridcolor='rgba(200,200,200,0.2)'),
                    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Roboto, sans-serif")
                )
                
                st.plotly_chart(fig1, use_container_width=True)
    
                # Keywords frequency analysis with enhanced styling
                if job_skills:
                    st.markdown("""
                    <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin: 1.5rem 0 1rem 0; animation: slideIn 0.5s ease-in-out;'>
                        <h3 style='color: #1f67b1; margin-bottom: 0.5rem; display: flex; align-items: center;'>
                            <span style='margin-right: 8px;'>🔍</span>Top Required Skills
                        </h3>
                        <p style='color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;'>Most common skills found in the analyzed resumes</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    top_kw = get_top_keywords(ranked_resumes, job_skills)
    
                    fig2 = px.bar(
                        top_kw, 
                        x='frequency', 
                        y='keyword',
                        orientation='h',
                        title='<b>Most Common Skills in Top Resumes</b>',
                        labels={'frequency': 'Frequency', 'keyword': 'Skill'},
                        color='frequency',
                        color_continuous_scale='viridis',
                        height=350
                    )
                    
                    # Enhance the chart appearance
                    fig2.update_layout(
                        plot_bgcolor='rgba(240,248,255,0.3)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Roboto, sans-serif", size=12),
                        margin=dict(l=10, r=10, t=40, b=10),
                        xaxis=dict(gridcolor='rgba(200,200,200,0.2)'),
                        yaxis=dict(gridcolor='rgba(200,200,200,0.2)'),
                        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Roboto, sans-serif")
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
    
else:
    with tab1:
        if not process_button:
            # Display instructions
            st.info("Please upload resume files and enter a job description, then click 'Analyze Resumes'.")
        elif not uploaded_files:
            st.warning("Please upload at least one resume file.")
        elif not job_description:
            st.warning("Please enter a job description.")

# Analysis History Tab with enhanced UI
with tab2:
    # Animated header
    st.markdown("""
    <div style='text-align: center; padding: 1.2rem; background: linear-gradient(90deg, #155085 0%, #1f67b1 100%); color: white; border-radius: 10px; margin: 1rem 0 2rem 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1); animation: fadeIn 0.8s ease-in-out;'>
        <h2 style='margin: 0; font-weight: 600; display: flex; align-items: center; justify-content: center;'>
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
            <div style='text-align: center; padding: 3rem 1rem; background-color: #f8f9fa; border-radius: 10px; border: 1px dashed #1f67b1; margin: 2rem 0; animation: fadeIn 1s ease-in-out;'>
                <img src="https://cdn.iconscout.com/icon/free/png-256/free-data-not-found-1965034-1662569.png" width="80" style='opacity: 0.6; margin-bottom: 1rem;'>
                <h3 style='color: #1f67b1; margin-bottom: 1rem;'>No Previous Analyses</h3>
                <p style='color: #666; max-width: 500px; margin: 0 auto;'>Once you analyze resumes using the Resume Analysis tab, your analysis history will appear here for future reference.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # History table with enhanced styling
            st.markdown("""
            <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin-bottom: 1.5rem; animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: #1f67b1; margin-bottom: 0.5rem; display: flex; align-items: center;'>
                    <span style='margin-right: 8px;'>📊</span>Analysis Summary
                </h3>
                <p style='color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;'>Recent resume analyses and their matching scores</p>
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
            <div style='background-color: #f5f9ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #1f67b1; margin: 2rem 0 1rem 0; animation: slideIn 0.5s ease-in-out;'>
                <h3 style='color: #1f67b1; margin-bottom: 0.5rem; display: flex; align-items: center;'>
                    <span style='margin-right: 8px;'>🔍</span>Detailed Analysis
                </h3>
                <p style='color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;'>Click on each analysis to see detailed information</p>
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
                        <div style='background-color: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 1rem;'>
                            <h4 style='color: #1f67b1; margin-bottom: 0.7rem; font-size: 1.1rem;'>Candidate Information</h4>
                            <p><strong>Name:</strong> {analysis['candidate_name']}</p>
                            <p><strong>Resume:</strong> {analysis['filename']}</p>
                            <p><strong>Analysis Date:</strong> {analysis['created_at']}</p>
                            <p><strong>Match Score:</strong> <span style='color: {"#2e7d32" if score >= 75 else "#ff9800" if score >= 50 else "#d32f2f"}; font-weight: bold;'>{score}%</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <h4 style='color: #1f67b1; margin-bottom: 0.7rem; font-size: 1.1rem;'>Job Description</h4>
                        """, unsafe_allow_html=True)
                        st.text_area("", analysis['description'][:400] + "..." if len(analysis['description']) > 400 else analysis['description'], height=120)
                    
                    # Display matching skills with better formatting
                    st.markdown("""
                    <h4 style='color: #1f67b1; margin: 1rem 0 0.7rem 0; font-size: 1.1rem;'>Matching Skills</h4>
                    """, unsafe_allow_html=True)
                    
                    if matching_skills:
                        # Display skills as badges in a flexbox layout
                        skills_html = ""
                        for skill in matching_skills:
                            skills_html += f"""
                            <div style='background-color: rgba(31, 103, 177, 0.1); 
                                        color: #1f67b1; 
                                        padding: 0.4rem 0.8rem; 
                                        border-radius: 50px; 
                                        font-size: 0.9rem;
                                        display: inline-block;
                                        margin: 0.3rem 0.4rem 0.3rem 0;
                                        border: 1px solid rgba(31, 103, 177, 0.2);'>
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