
import streamlit as st
import pandas as pd
from collections import Counter

def display_resume_details(resume_data):
    """
    Display detailed information about a resume
    """
    st.write(f"**Filename:** {resume_data['filename']}")
    st.write(f"**Match Percentage:** {resume_data['match_percentage']}%")
    
    # Display skills section
    st.write("### Skills")
    all_skills = resume_data['skills']
    matching_skills = resume_data['matching_skills']
    
    # Create two columns for skills display
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Matching Skills:**")
        if matching_skills:
            for skill in matching_skills:
                st.write(f"- {skill}")
        else:
            st.write("No matching skills found")
    
    with col2:
        st.write("**Other Skills:**")
        other_skills = list(set(all_skills) - set(matching_skills))
        if other_skills:
            for skill in other_skills[:10]:  # Show only top 10 other skills
                st.write(f"- {skill}")
            if len(other_skills) > 10:
                st.write(f"- ... and {len(other_skills) - 10} more")
        else:
            st.write("No other skills found")
    
    # Display resume preview without nested expander
    st.write("### Resume Text Preview")
    preview_text = resume_data['text'][:1000] + ("..." if len(resume_data['text']) > 1000 else "")
    st.text_area("", preview_text, height=200)

def get_top_keywords(resumes_data, job_skills, top_n=10):
    """
    Extract top keywords from resumes based on frequency
    """
    # Count skill frequencies across all resumes
    skill_counter = Counter()
    
    for resume in resumes_data:
        for skill in resume['skills']:
            if skill in job_skills:
                skill_counter[skill] += 1
    
    # Get the most common skills
    most_common = skill_counter.most_common(top_n)
    
    # Convert to DataFrame
    if most_common:
        df = pd.DataFrame(most_common, columns=['keyword', 'frequency'])
        return df
    else:
        return pd.DataFrame(columns=['keyword', 'frequency'])
