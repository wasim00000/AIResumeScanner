import streamlit as st
import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from io import BytesIO

from resume_parser import extract_text_from_pdf, extract_text_from_docx
from nlp_processor import preprocess_text, extract_skills, extract_entities
from ranking_system import calculate_similarity, rank_resumes
from utils import display_resume_details, get_top_keywords

# Set page configuration
st.set_page_config(
    page_title="AI Resume Scanner",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
        background-color: #f8f9fa;
    }
    .stTitle {
        color: #1f67b1;
        font-size: 3rem !important;
        padding-bottom: 2rem;
    }
    .stMarkdown {
        font-size: 1.2rem;
    }
    .stButton button {
        background-color: #1f67b1;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #155085;
    }
    div[data-testid="stFileUploader"] {
        padding: 1rem;
        border: 2px dashed #1f67b1;
        border-radius: 5px;
        margin: 1rem 0;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Application title and description
st.title("AI-Powered Resume Scanner")
st.markdown("""
<div style='background-color: white; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #1f67b1; margin-bottom: 2rem;'>
    <h4 style='color: #1f67b1; margin-bottom: 0.5rem;'>Welcome to the Resume Scanner!</h4>
    <p>This intelligent application helps you:</p>
    <ul>
        <li>Match candidate resumes with job descriptions using advanced NLP</li>
        <li>Analyze multiple resumes simultaneously</li>
        <li>Get detailed skill matching and ranking results</li>
        <li>Visualize candidate comparisons</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Create sidebar for inputs
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 1rem; background-color: #1f67b1; color: white; border-radius: 5px; margin-bottom: 2rem;'>
            <h2 style='margin: 0;'>Analysis Controls</h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Job Description Input
    st.markdown("<h3 style='color: #1f67b1;'>📝 Job Description</h3>", unsafe_allow_html=True)
    job_description = st.text_area("Enter the job requirements:", height=200,
                                 help="Paste the job description here. The more detailed it is, the better the matching will be.")
    
    # Resume File Upload
    st.markdown("<h3 style='color: #1f67b1; margin-top: 2rem;'>📎 Resume Upload</h3>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Drop your resumes here (PDF/DOCX)", 
                                    type=["pdf", "docx"], 
                                    accept_multiple_files=True,
                                    help="You can upload multiple resumes at once")
    
    # Analysis Settings
    st.markdown("<h3 style='color: #1f67b1; margin-top: 2rem;'>⚙️ Settings</h3>", unsafe_allow_html=True)
    min_skill_match = st.slider("Minimum Skill Match %", 0, 100, 50,
                               help="Filter out candidates below this match percentage")
    top_n = st.slider("Show Top N Candidates", 1, 20, 5,
                      help="Number of top candidates to display")
    
    # Process Button
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
    with st.spinner('Processing resumes and job description...'):
        # Create a list to store resume data
        resumes_data = []
        
        # Process job description
        preprocessed_jd = preprocess_text(job_description)
        job_skills = extract_skills(preprocessed_jd)
        job_entities = extract_entities(preprocessed_jd)
        
        st.session_state.job_skills = job_skills
        
        # Process each uploaded resume
        for uploaded_file in uploaded_files:
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
            
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            
            finally:
                # Remove the temporary file
                os.unlink(temp_file_path)
        
        if resumes_data:
            # Rank the resumes
            ranked_resumes = rank_resumes(resumes_data)
            st.session_state.processed_resumes = resumes_data
            st.session_state.ranked_resumes = ranked_resumes
            st.success(f"Successfully processed {len(resumes_data)} resumes!")
        else:
            st.warning("No resumes were successfully processed.")

# Display results if available
if st.session_state.ranked_resumes and st.session_state.job_skills:
    st.header("Resume Ranking Results")
    
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
            st.subheader("Top Candidates")
            
            # Create a DataFrame for display
            display_data = [{
                'Candidate': resume['candidate_name'],
                'Match %': resume['match_percentage'],
                'Matching Skills': ', '.join(resume['matching_skills'][:5]) + 
                                 ('...' if len(resume['matching_skills']) > 5 else '')
            } for resume in top_resumes]
            
            df_display = pd.DataFrame(display_data)
            st.dataframe(df_display, use_container_width=True)
            
            # Detailed candidate view
            st.subheader("Candidate Details")
            for i, resume in enumerate(top_resumes):
                with st.expander(f"{i+1}. {resume['candidate_name']} ({resume['match_percentage']}% match)"):
                    display_resume_details(resume)
        
        with col2:
            st.subheader("Visualizations")
            
            # Bar chart of top candidates
            fig1 = px.bar(
                display_data, 
                x='Match %', 
                y='Candidate', 
                orientation='h',
                title='Resume Match Percentages',
                labels={'x': 'Match Percentage (%)', 'y': 'Candidate'},
                color='Match %',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Keywords frequency analysis
            if job_skills:
                st.subheader("Top Required Skills")
                top_kw = get_top_keywords(ranked_resumes, job_skills)
                
                fig2 = px.bar(
                    top_kw, 
                    x='frequency', 
                    y='keyword',
                    orientation='h',
                    title='Most Common Skills in Top Resumes',
                    labels={'frequency': 'Frequency', 'keyword': 'Skill'},
                    color='frequency',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig2, use_container_width=True)

else:
    if not process_button:
        # Display instructions
        st.info("Please upload resume files and enter a job description, then click 'Analyze Resumes'.")
    elif not uploaded_files:
        st.warning("Please upload at least one resume file.")
    elif not job_description:
        st.warning("Please enter a job description.")
