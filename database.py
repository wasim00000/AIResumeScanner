import os
import json
import logging
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a data directory if it doesn't exist
DATA_DIR = Path("./data")
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)

# Initialize database files
JOB_DESCRIPTIONS_FILE = DATA_DIR / "job_descriptions.json"
RESUMES_FILE = DATA_DIR / "resumes.json"
ANALYSIS_RESULTS_FILE = DATA_DIR / "analysis_results.json"

# Initialize empty data structures if files don't exist
if not JOB_DESCRIPTIONS_FILE.exists():
    with open(JOB_DESCRIPTIONS_FILE, 'w') as f:
        json.dump([], f)

if not RESUMES_FILE.exists():
    with open(RESUMES_FILE, 'w') as f:
        json.dump([], f)

if not ANALYSIS_RESULTS_FILE.exists():
    with open(ANALYSIS_RESULTS_FILE, 'w') as f:
        json.dump([], f)

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
        # Read existing data
        with open(JOB_DESCRIPTIONS_FILE, 'r') as f:
            job_descriptions = json.load(f)
        
        # Generate new ID
        new_id = 1
        if job_descriptions:
            new_id = max([jd.get('id', 0) for jd in job_descriptions]) + 1
        
        # Create job description record
        job_description = {
            'id': new_id,
            'description': description,
            'skills': skills,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        # Add to list and save
        job_descriptions.append(job_description)
        with open(JOB_DESCRIPTIONS_FILE, 'w') as f:
            json.dump(job_descriptions, f, indent=2)
        
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
        # Read existing data
        with open(RESUMES_FILE, 'r') as f:
            resumes = json.load(f)
        
        # Generate new ID
        new_id = 1
        if resumes:
            new_id = max([r.get('id', 0) for r in resumes]) + 1
        
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
        with open(RESUMES_FILE, 'w') as f:
            json.dump(resumes, f, indent=2)
        
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
        # Read existing data
        with open(ANALYSIS_RESULTS_FILE, 'r') as f:
            analysis_results = json.load(f)
        
        # Generate new ID
        new_id = 1
        if analysis_results:
            new_id = max([ar.get('id', 0) for ar in analysis_results]) + 1
        
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
        with open(ANALYSIS_RESULTS_FILE, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
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
        # Read data from files
        with open(ANALYSIS_RESULTS_FILE, 'r') as f:
            analysis_results = json.load(f)
        
        with open(JOB_DESCRIPTIONS_FILE, 'r') as f:
            job_descriptions = json.load(f)
            # Create dictionary for faster lookup
            job_dict = {jd['id']: jd for jd in job_descriptions}
        
        with open(RESUMES_FILE, 'r') as f:
            resumes = json.load(f)
            # Create dictionary for faster lookup
            resume_dict = {r['id']: r for r in resumes}
        
        # Build the analysis data with joined information
        analyses = []
        for ar in analysis_results:
            job = job_dict.get(ar['job_id'])
            resume = resume_dict.get(ar['resume_id'])
            
            if job and resume:
                analyses.append({
                    'id': ar['id'],
                    'description': job['description'],
                    'candidate_name': resume['candidate_name'],
                    'filename': resume['filename'],
                    'similarity_score': ar['similarity_score'],
                    'matching_skills': ar['matching_skills'],
                    'created_at': ar['created_at']
                })
        
        # Sort by created_at (newest first) and limit
        analyses.sort(key=lambda x: x['created_at'], reverse=True)
        return analyses[:limit]
        
    except Exception as e:
        logger.error(f"Error retrieving previous analyses: {str(e)}")
        return []