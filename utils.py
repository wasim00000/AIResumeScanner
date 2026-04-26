import streamlit as st
import pandas as pd
from collections import Counter
import re # Add re import
import requests
import os

def ai_chatbot_response(prompt: str) -> str:
    """
    Try to use a free HuggingFace inference API model for chatbot queries.
    Falls back to an advanced rule-based response when the API is unavailable.
    """
    # First try external API
    try:
        api_url = "https://api-inference.huggingface.co/models/google/flan-t5-base"
        headers = {"Accept": "application/json"}
        payload = {"inputs": prompt}
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
                return result[0]['generated_text'].strip()
            elif isinstance(result, dict) and 'generated_text' in result:
                return result['generated_text'].strip()
    except Exception:
        pass  # Silently fail and use fallback
    
    # Advanced fallback responses when API is unavailable
    prompt_lower = prompt.lower()
    
    # Job role specific templates
    job_roles = {
        "web developer": """
## Web Developer Requirements Template

**Essential Skills:**
- HTML5, CSS3, JavaScript (ES6+)
- Responsive design principles
- Experience with modern frameworks (React, Angular, Vue)
- Version control (Git)
- Browser compatibility and debugging
- API integration

**Nice-to-Have Skills:**
- Backend experience (Node.js, Python, PHP)
- Database experience (SQL, MongoDB)
- Performance optimization
- Automated testing
- UI/UX principles

**Qualities:**
- Strong problem-solving skills
- Attention to detail
- Ability to work in an agile environment

Would you like me to help you analyze resumes for this position? Upload your resumes to get started.
""",
        "data scientist": """
## Data Scientist Requirements Template

**Essential Skills:**
- Python or R programming
- Statistical analysis and modeling
- Machine learning algorithms
- Data visualization
- SQL and database knowledge
- Data cleaning and preparation

**Nice-to-Have Skills:**
- Big data technologies (Hadoop, Spark)
- Cloud platforms (AWS, Azure, GCP)
- Deep learning frameworks
- A/B testing experience
- Industry-specific knowledge

**Qualities:**
- Analytical thinking
- Problem-solving ability
- Communication skills to explain complex findings

Would you like me to help you analyze resumes for this position? Upload your resumes to get started.
""",
        "software engineer": """
## Software Engineer Requirements Template

**Essential Skills:**
- Strong programming skills in at least one language
- Data structures and algorithms
- System design knowledge
- Testing methodologies
- Version control
- Problem-solving ability

**Nice-to-Have Skills:**
- CI/CD experience
- Cloud services knowledge
- Microservices architecture
- Security best practices
- Agile development experience

**Qualities:**
- Team collaboration
- Adaptability to new technologies
- Attention to detail
- Time management

Would you like me to help you analyze resumes for this position? Upload your resumes to get started.
""",
        "project manager": """
## Project Manager Requirements Template

**Essential Skills:**
- Project planning and scheduling
- Budget management
- Risk assessment and mitigation
- Team leadership and coordination
- Stakeholder communication
- Progress tracking and reporting

**Nice-to-Have Skills:**
- Certification (PMP, PRINCE2, Agile)
- Industry-specific knowledge
- Resource allocation expertise
- Technical background related to the project domain
- Experience with project management tools

**Qualities:**
- Strong leadership
- Problem-solving ability
- Excellent communication
- Decision-making skills
- Conflict resolution

Would you like me to help you analyze resumes for this position? Upload your resumes to get started.
"""
    }
    
    # Check for job role requests
    for role, template in job_roles.items():
        if role in prompt_lower or f"need {role}" in prompt_lower or f"looking for {role}" in prompt_lower:
            return template
    
    # Resume related questions
    if any(word in prompt_lower for word in ['resume', 'cv', 'skill', 'candidate', 'job description']):
        return """I can help you scan and analyze resumes based on job requirements. Here's what I can do:

1. **Extract key skills** from resumes and job descriptions
2. **Match candidates** to job requirements with percentage scores
3. **Highlight matching skills** for each candidate
4. **Rank candidates** by suitability for the position

To get started:
1. Upload your job description
2. Upload candidate resumes
3. View the ranked results and detailed analysis

Is there a specific job role you're hiring for? I can provide a requirements template!"""
    
    # Help related questions
    elif any(word in prompt_lower for word in ['help', 'how to', 'tutorial', 'guide', 'instructions']):
        return """## How to Use the Resume Scanner

**Step 1: Job Description**
- Upload a job description file OR
- Enter job requirements as text
- Key skills will be automatically extracted

**Step 2: Resumes**
- Upload multiple candidate resumes (PDF or Word format)
- Our AI will parse them automatically

**Step 3: Results**
- View ranked candidates by match percentage
- See which skills match for each candidate
- Get detailed analysis of each resume

**Step 4: Shortlist**
- Use the chat assistant to compare candidates
- Filter by minimum match percentage
- Export your shortlist

Need a job description template? Ask me for requirements for specific roles like "web developer" or "data scientist"!"""
    
    # Greeting
    elif any(word in prompt_lower for word in ['hi', 'hello', 'hey', 'greetings']):
        return """Hello! I'm your AI assistant for resume scanning. I can help you with:

- Creating job descriptions with key requirements
- Analyzing resumes against job requirements
- Finding the best candidates for your positions
- Comparing candidate qualifications

What would you like help with today?"""
    
    # Questions about the tool
    elif 'what can you do' in prompt_lower or 'what do you do' in prompt_lower or 'capabilities' in prompt_lower:
        return """## Resume Scanner Capabilities

**Resume Analysis:**
- Extract skills, experience, education and certifications
- Match candidates to job requirements
- Calculate match percentages based on key skills
- Rank candidates by suitability

**Job Requirements:**
- Extract key requirements from job descriptions
- Create custom skill patterns for specialized roles
- Provide templates for common job positions

**Advanced Features:**
- Natural language Q&A about candidates
- Skill gap analysis
- Candidate comparison
- Export shortlisted candidates

Ask me for a job description template or upload resumes to get started!"""
    
    # Advanced features or improvements
    elif 'advanced' in prompt_lower or 'improve' in prompt_lower or 'better' in prompt_lower or 'enhance' in prompt_lower:
        return """## Advanced Resume Scanner Features

Our AI-powered resume scanner uses natural language processing to go beyond simple keyword matching:

**Skills Context Analysis:**
- Understands skills in context (not just keywords)
- Recognizes skill variations and related terms
- Evaluates skill proficiency indicators

**Smart Candidate Ranking:**
- Weighs critical vs. preferred skills
- Considers experience level and recency
- Analyzes skill combinations and patterns

**Actionable Insights:**
- Identifies skill gaps across your candidate pool
- Suggests skills to prioritize in interviews
- Highlights unique candidate strengths

**Efficiency Tools:**
- Batch process multiple resumes
- Save and compare multiple job descriptions
- Export detailed analysis reports

Would you like to start analyzing resumes or need help with a specific advanced feature?"""
    
    # If looking for templates or examples
    elif any(word in prompt_lower for word in ['template', 'example', 'sample']):
        return """I can provide templates for:

**Job Descriptions:**
- Web Developer
- Data Scientist
- Software Engineer
- Project Manager
- Marketing Specialist
- Financial Analyst
- UX/UI Designer

**Resume Analysis:**
- Technical roles
- Management positions
- Creative positions
- Entry-level candidates

Which template would you like to see? Ask for a specific role like "web developer template" or "marketing specialist requirements"."""
    
    # Fallback response
    return """I'm here to help you scan and analyze resumes for your hiring needs. You can:

1. Ask for job requirement templates (e.g., "web developer requirements")
2. Get help with using the tool (e.g., "how to use this tool")
3. Learn about advanced features (e.g., "show advanced features")
4. Upload resumes to start the analysis process

How can I assist you with your recruitment needs today?"""

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

def generate_chatbot_response(query, ranked_resumes, job_skills):
    """  Generates a response to a user query based on ranked resume data.
    This is a rule-based assistant, not a true LLM chatbot.

    Args:
        query (str): The user's query.
        ranked_resumes (list): List of ranked resume data dictionaries (filtered and top N).
        job_skills (list): List of skills from the job description.

    Returns:
        str: The assistant's response.
    """
    query_lower = query.lower()
    response = "I'm sorry, I couldn't understand that request. Try asking about specific candidates, skills, or comparisons (e.g., 'Compare candidate 1 and 2', 'Who has Python?', 'Details for resume.pdf')." # Default response

    if not ranked_resumes:
        # This case might not be reached if called after filtering in app.py, but good practice.
        return "There are no candidates to analyze based on the current filters."

    # --- Simple Keyword Matching ---

    # Requesting details for a specific candidate (by number or filename)
    # Adjusted regex to be more flexible with phrasing and optional elements
    detail_match = re.search(r"(?:details for|show|tell me about) (?:candidate (\d+)|(?:resume|file) name? ['\"]?(.+\.(?:pdf|docx))['\"]?)", query_lower)
    if detail_match:
        candidate_index_str = detail_match.group(1)
        filename = detail_match.group(2)
        found = False
        target_query = f"candidate {candidate_index_str}" if candidate_index_str else filename

        if candidate_index_str:
            try:
                idx = int(candidate_index_str) - 1
                if 0 <= idx < len(ranked_resumes):
                    resume = ranked_resumes[idx]
                    response = f"**Candidate {idx + 1}: {resume['filename']}**\\n" # Use \\n for markdown line breaks
                    response += f"- **Match:** {resume['match_percentage']}%\\n"
                    matching_skills_str = ', '.join(resume['matching_skills']) if resume['matching_skills'] else 'None'
                    response += f"- **Matching Skills:** {matching_skills_str}\\n"
                    other_skills = list(set(resume['skills']) - set(resume['matching_skills']))
                    other_skills_str = ', '.join(other_skills[:5]) + ('...' if len(other_skills) > 5 else '') if other_skills else 'None'
                    response += f"- **Other Skills:** {other_skills_str} (Top 5 shown)"
                    found = True
            except ValueError:
                pass # Invalid number format
        elif filename:
             filename_lower = filename.lower()
             for i, resume in enumerate(ranked_resumes):
                 if filename_lower == resume['filename'].lower(): # Exact match preferred
                    response = f"**Candidate {i + 1}: {resume['filename']}**\\n"
                    response += f"- **Match:** {resume['match_percentage']}%\\n"
                    matching_skills_str = ', '.join(resume['matching_skills']) if resume['matching_skills'] else 'None'
                    response += f"- **Matching Skills:** {matching_skills_str}\\n"
                    other_skills = list(set(resume['skills']) - set(resume['matching_skills']))
                    other_skills_str = ', '.join(other_skills[:5]) + ('...' if len(other_skills) > 5 else '') if other_skills else 'None'
                    response += f"- **Other Skills:** {other_skills_str} (Top 5 shown)"
                    found = True
                    break
             # Fallback to partial match if exact match fails
             if not found:
                 for i, resume in enumerate(ranked_resumes):
                     if filename_lower in resume['filename'].lower():
                        response = f"Found partial match: **Candidate {i + 1}: {resume['filename']}**\\n"
                        response += f"- **Match:** {resume['match_percentage']}%\\n"
                        matching_skills_str = ', '.join(resume['matching_skills']) if resume['matching_skills'] else 'None'
                        response += f"- **Matching Skills:** {matching_skills_str}\\n"
                        other_skills = list(set(resume['skills']) - set(resume['matching_skills']))
                        other_skills_str = ', '.join(other_skills[:5]) + ('...' if len(other_skills) > 5 else '') if other_skills else 'None'
                        response += f"- **Other Skills:** {other_skills_str} (Top 5 shown)"
                        found = True
                        break

        if not found:
             response = f"Sorry, I couldn't find a candidate matching '{target_query}' in the current list. Please use the candidate number (e.g., 'details for candidate 1') or the exact filename (e.g., 'details for resume_xyz.pdf')."
        return response

    # Comparing candidates (by number)
    compare_match = re.search(r"compare (?:candidate )?(\d+) and (?:candidate )?(\d+)", query_lower)
    if compare_match:
        try:
            idx1 = int(compare_match.group(1)) - 1
            idx2 = int(compare_match.group(2)) - 1
            if 0 <= idx1 < len(ranked_resumes) and 0 <= idx2 < len(ranked_resumes):
                res1 = ranked_resumes[idx1]
                res2 = ranked_resumes[idx2]
                response = f"**Comparison: {res1['filename']} (Candidate {idx1+1}) vs {res2['filename']} (Candidate {idx2+1})**\\n"
                response += f"- **Match %:** {res1['match_percentage']}% vs {res2['match_percentage']}%\\n"
                response += f"- **Matching Skills:** {len(res1['matching_skills'])} vs {len(res2['matching_skills'])} skills\\n"
                common_skills = set(res1['matching_skills']).intersection(set(res2['matching_skills']))
                response += f"- **Common Matching Skills:** {', '.join(common_skills) if common_skills else 'None'}\\n"
                res1_unique = set(res1['matching_skills']) - common_skills
                res2_unique = set(res2['matching_skills']) - common_skills
                response += f"- **Unique Matching Skills ({res1['filename']}):** {', '.join(res1_unique) if res1_unique else 'None'}\\n"
                response += f"- **Unique Matching Skills ({res2['filename']}):** {', '.join(res2_unique) if res2_unique else 'None'}"
            else:
                response = f"Invalid candidate number(s) provided for comparison. Please use numbers between 1 and {len(ranked_resumes)}."
        except ValueError:
            response = "Please provide valid numbers for comparison (e.g., 'compare 1 and 2')."
        return response

    # Asking about specific skills (more flexible regex)
    skill_match = re.search(r"(?:who has|show candidates? with|list .* with|which candidates? know) ['\"]?([\w\s+#.-]+?)['\"]?(?: skill)?s?", query_lower)
    if skill_match:
        skill_query = skill_match.group(1).strip().lower() # Normalize skill query
        candidates_with_skill = []
        for i, resume in enumerate(ranked_resumes):
            # Check both matching and other skills (case-insensitive)
            if skill_query in [s.lower() for s in resume['skills']]:
                 # Check if it's a matching skill for extra info
                 is_matching = skill_query in [s.lower() for s in resume['matching_skills']]
                 match_info = "(Matching Skill)" if is_matching else "(Other Skill)"
                 candidates_with_skill.append(f"Candidate {i+1}: {resume['filename']} (Match: {resume['match_percentage']}%) {match_info}")

        if candidates_with_skill:
            response = f"Candidates with **{skill_query}** skills:\\n- " + "\\n- ".join(candidates_with_skill)
        else:
            response = f"No candidates in the current list have the skill: **{skill_query}**."
        return response

    # Showing top N candidates
    top_match = re.search(r"(?:show|list|get) top (\d+)", query_lower)
    if top_match:
        try:
            n = int(top_match.group(1))
            if n > 0:
                response = f"**Top {min(n, len(ranked_resumes))} Candidates:**\\n"
                for i, resume in enumerate(ranked_resumes[:n]):
                     response += f"{i+1}. {resume['filename']} (Match: {resume['match_percentage']}%)\\n"
                # Remove trailing newline
                response = response.strip()
            else:
                response = "Please specify a positive number for 'top'."
        except ValueError:
            response = "Invalid number specified for 'top'."
        return response

    # Simple greetings or help
    if query_lower in ["hi", "hello", "help", "what can you do?"]:
        response = "Hello! I can help you analyze the ranked candidates currently displayed. Try asking me to:\\n"
        response += "- 'Show top 3 candidates'\\n"
        response += "- 'Details for candidate 1' or 'Details for resume_name.pdf'\\n"
        response += "- 'Compare candidate 1 and 2'\\n"
        response += "- 'Who has Python skills?'"
        return response


    return response # Return default if no rules matched
