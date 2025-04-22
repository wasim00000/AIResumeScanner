import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def calculate_similarity(job_description, resume_text, job_skills, resume_skills):
    """
    Calculate similarity score between job description and resume
    
    Args:
        job_description (str): Preprocessed job description text
        resume_text (str): Preprocessed resume text
        job_skills (list): Skills extracted from job description
        resume_skills (list): Skills extracted from resume
        
    Returns:
        float: Similarity score between 0 and 1
    """
    # Calculate text similarity using TF-IDF and cosine similarity
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    
    # Create a corpus with just the two documents
    corpus = [job_description, resume_text]
    
    # Create the TF-IDF matrix
    try:
        tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)
        
        # Calculate cosine similarity
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except:
        # If TF-IDF fails (e.g., one text is too short), use a fallback
        cosine_sim = 0.0
    
    # Calculate skill match percentage
    if job_skills:
        matching_skills = set(job_skills).intersection(set(resume_skills))
        skill_match_ratio = len(matching_skills) / len(job_skills) if job_skills else 0
    else:
        skill_match_ratio = 0
    
    # Combined score (60% skill match, 40% text similarity)
    combined_score = (0.6 * skill_match_ratio) + (0.4 * cosine_sim)
    
    return combined_score

def rank_resumes(resumes_data):
    """
    Rank resumes based on similarity scores
    
    Args:
        resumes_data (list): List of resume data dictionaries
        
    Returns:
        list: Sorted list of resumes by similarity score
    """
    # Sort resumes by similarity score in descending order
    ranked_resumes = sorted(
        resumes_data,
        key=lambda x: x['similarity_score'],
        reverse=True
    )
    
    return ranked_resumes
