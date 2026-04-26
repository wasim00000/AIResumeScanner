import re

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover - optional dependency fallback
    TfidfVectorizer = None
    cosine_similarity = None


def _normalize_text(value):
    return str(value or "").strip()


def _normalize_skills(skills):
    if not skills:
        return []
    return [
        str(skill).strip().lower()
        for skill in skills
        if str(skill).strip()
    ]


def _safe_score(value):
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _fallback_text_similarity(job_description, resume_text):
    job_tokens = set(re.findall(r"[a-z0-9+#./-]+", job_description.lower()))
    resume_tokens = set(re.findall(r"[a-z0-9+#./-]+", resume_text.lower()))
    if not job_tokens or not resume_tokens:
        return 0.0

    union = job_tokens | resume_tokens
    if not union:
        return 0.0
    return len(job_tokens & resume_tokens) / len(union)

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
    job_description = _normalize_text(job_description)
    resume_text = _normalize_text(resume_text)
    job_skills = _normalize_skills(job_skills)
    resume_skills = _normalize_skills(resume_skills)

    if not job_description and not resume_text and not job_skills and not resume_skills:
        return 0.0

    # Calculate text similarity using TF-IDF and cosine similarity when available.
    if TfidfVectorizer is not None and cosine_similarity is not None:
        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        corpus = [job_description, resume_text]
        try:
            tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)
            tfidf_array = tfidf_matrix.toarray()  # type: ignore[attr-defined]
            cosine_sim = float(cosine_similarity(tfidf_array[0:1], tfidf_array[1:2])[0][0])
        except Exception:
            cosine_sim = _fallback_text_similarity(job_description, resume_text)
    else:
        cosine_sim = _fallback_text_similarity(job_description, resume_text)

    # Calculate skill match percentage
    if job_skills:
        matching_skills = set(job_skills).intersection(set(resume_skills))
        skill_match_ratio = len(matching_skills) / len(job_skills) if job_skills else 0
    else:
        skill_match_ratio = 0

    # Combined score (60% skill match, 40% text similarity)
    combined_score = (0.6 * skill_match_ratio) + (0.4 * cosine_sim)
    combined_score = max(0.0, min(1.0, combined_score))

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
        key=lambda x: _safe_score(x.get('similarity_score', 0.0)),
        reverse=True
    )

    return ranked_resumes
