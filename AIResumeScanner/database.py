import json
import logging
import datetime
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a data directory beside this module so persistence is launch-dir agnostic
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize database files
JOB_DESCRIPTIONS_FILE = DATA_DIR / "job_descriptions.json"
RESUMES_FILE = DATA_DIR / "resumes.json"
ANALYSIS_RESULTS_FILE = DATA_DIR / "analysis_results.json"

def _ensure_json_file(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        path.write_text("[]", encoding="utf-8")


def _load_json_list(path):
    _ensure_json_file(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        logger.warning("Resetting unreadable JSON file: %s", path)
        path.write_text("[]", encoding="utf-8")
        return []


def _write_json_list(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


_ensure_json_file(JOB_DESCRIPTIONS_FILE)
_ensure_json_file(RESUMES_FILE)
_ensure_json_file(ANALYSIS_RESULTS_FILE)


def _next_id(records):
    numeric_ids = [item.get("id", 0) for item in records if isinstance(item, dict)]
    return (max(numeric_ids) if numeric_ids else 0) + 1

def save_job_description(description, skills):
    """
    Save a job description to the JSON file

    Args:
        description (str): The job description text
        skills (list): List of skills extracted from the job description

    Returns:
        int: The ID of the inserted job description
    """
    try:
        job_descriptions = _load_json_list(JOB_DESCRIPTIONS_FILE)
        new_id = _next_id(job_descriptions)

        # Create job description record
        job_description = {
            'id': new_id,
            'description': description,
            'skills': skills,
            'created_at': datetime.datetime.now().isoformat()
        }

        # Add to list and save
        job_descriptions.append(job_description)
        _write_json_list(JOB_DESCRIPTIONS_FILE, job_descriptions)

        logger.info(f"Job description saved with ID: {new_id}")
        return new_id

    except Exception as e:
        logger.error(f"Error saving job description: {str(e)}")
        raise

def save_resume(filename, candidate_name, text, skills):
    """
    Save a resume to the JSON file

    Args:
        filename (str): Original filename of the resume
        candidate_name (str): Name of the candidate
        text (str): Extracted text from the resume
        skills (list): List of skills extracted from the resume

    Returns:
        int: The ID of the inserted resume
    """
    try:
        resumes = _load_json_list(RESUMES_FILE)
        new_id = _next_id(resumes)

        # Create resume record
        resume = {
            'id': new_id,
            'filename': filename,
            'candidate_name': candidate_name,
            'text': text,
            'skills': skills,
            'created_at': datetime.datetime.now().isoformat()
        }

        # Add to list and save
        resumes.append(resume)
        _write_json_list(RESUMES_FILE, resumes)

        logger.info(f"Resume saved with ID: {new_id}")
        return new_id

    except Exception as e:
        logger.error(f"Error saving resume: {str(e)}")
        raise

def save_analysis_result(job_id, resume_id, similarity_score, matching_skills):
    """
    Save an analysis result to the JSON file

    Args:
        job_id (int): ID of the job description
        resume_id (int): ID of the resume
        similarity_score (float): Calculated similarity score
        matching_skills (list): List of matching skills

    Returns:
        int: The ID of the inserted analysis result
    """
    try:
        analysis_results = _load_json_list(ANALYSIS_RESULTS_FILE)
        new_id = _next_id(analysis_results)

        # Create analysis result record
        analysis_result = {
            'id': new_id,
            'job_id': job_id,
            'resume_id': resume_id,
            'similarity_score': similarity_score,
            'matching_skills': matching_skills,
            'created_at': datetime.datetime.now().isoformat()
        }

        # Add to list and save
        analysis_results.append(analysis_result)
        _write_json_list(ANALYSIS_RESULTS_FILE, analysis_results)

        logger.info(f"Analysis result saved with ID: {new_id}")
        return new_id

    except Exception as e:
        logger.error(f"Error saving analysis result: {str(e)}")
        raise

def get_previous_analyses(limit=10):
    """
    Get previous analyses from the JSON files

    Args:
        limit (int): Maximum number of analyses to return

    Returns:
        list: List of dictionaries containing analysis data
    """
    try:
        analysis_results = _load_json_list(ANALYSIS_RESULTS_FILE)
        job_descriptions = _load_json_list(JOB_DESCRIPTIONS_FILE)
        resumes = _load_json_list(RESUMES_FILE)

        job_dict = {
            jd.get("id"): jd
            for jd in job_descriptions
            if isinstance(jd, dict) and jd.get("id") is not None
        }
        resume_dict = {
            resume.get("id"): resume
            for resume in resumes
            if isinstance(resume, dict) and resume.get("id") is not None
        }

        # Build the analysis data with joined information
        analyses = []
        for ar in analysis_results:
            if not isinstance(ar, dict):
                continue

            job = job_dict.get(ar.get("job_id"))
            resume = resume_dict.get(ar.get("resume_id"))

            if job and resume:
                analyses.append({
                    'id': ar.get('id'),
                    'description': job.get('description', ''),
                    'candidate_name': resume.get('candidate_name', ''),
                    'filename': resume.get('filename', ''),
                    'similarity_score': ar.get('similarity_score', 0.0),
                    'matching_skills': ar.get('matching_skills', []),
                    'created_at': ar.get('created_at', '')
                })

        def _sort_key(item):
            timestamp = item.get("created_at", "")
            try:
                return datetime.datetime.fromisoformat(timestamp)
            except (TypeError, ValueError):
                return datetime.datetime.min

        analyses.sort(key=_sort_key, reverse=True)
        return analyses[:limit]

    except Exception as e:
        logger.error(f"Error retrieving previous analyses: {str(e)}")
        return []
