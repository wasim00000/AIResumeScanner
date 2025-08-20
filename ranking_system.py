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

        # Convert sparse TF-IDF matrix to dense array for reliable indexing
        # (safe for small corpus of two documents)
        tfidf_array = tfidf_matrix.toarray()  # type: ignore[attr-defined]

        # Calculate cosine similarity between the two vectors using numpy array slices
        # Use [0:1] style to keep 2D shape expected by sklearn's cosine_similarity
        cosine_sim = float(cosine_similarity(tfidf_array[0:1], tfidf_array[1:2])[0][0])
    except Exception:
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
