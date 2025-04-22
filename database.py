import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters from environment variables
db_params = {
    'dbname': os.environ.get('PGDATABASE', 'postgres'),
    'user': os.environ.get('PGUSER', 'postgres'),
    'password': os.environ.get('PGPASSWORD', ''),
    'host': os.environ.get('PGHOST', 'localhost'),
    'port': os.environ.get('PGPORT', '5432')
}

def get_db_connection():
    """
    Create a connection to the PostgreSQL database
    
    Returns:
        connection: A PostgreSQL database connection
    """
    try:
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to the database: {str(e)}")
        raise

def create_tables():
    """
    Create the necessary tables if they don't exist
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create job_descriptions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id SERIAL PRIMARY KEY,
            description TEXT NOT NULL,
            skills TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create resumes table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            candidate_name TEXT,
            text TEXT NOT NULL,
            skills TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create analysis_results table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id SERIAL PRIMARY KEY,
            job_id INTEGER REFERENCES job_descriptions(id),
            resume_id INTEGER REFERENCES resumes(id),
            similarity_score FLOAT NOT NULL,
            matching_skills TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.close()
        conn.close()
        
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

def save_job_description(description, skills):
    """
    Save a job description to the database
    
    Args:
        description (str): The job description text
        skills (list): List of skills extracted from the job description
        
    Returns:
        int: The ID of the inserted job description
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO job_descriptions (description, skills) VALUES (%s, %s) RETURNING id",
            (description, skills)
        )
        
        job_id = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return job_id
    except Exception as e:
        logger.error(f"Error saving job description: {str(e)}")
        raise

def save_resume(filename, candidate_name, text, skills):
    """
    Save a resume to the database
    
    Args:
        filename (str): Original filename of the resume
        candidate_name (str): Name of the candidate
        text (str): Extracted text from the resume
        skills (list): List of skills extracted from the resume
        
    Returns:
        int: The ID of the inserted resume
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO resumes (filename, candidate_name, text, skills) VALUES (%s, %s, %s, %s) RETURNING id",
            (filename, candidate_name, text, skills)
        )
        
        resume_id = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return resume_id
    except Exception as e:
        logger.error(f"Error saving resume: {str(e)}")
        raise

def save_analysis_result(job_id, resume_id, similarity_score, matching_skills):
    """
    Save an analysis result to the database
    
    Args:
        job_id (int): ID of the job description
        resume_id (int): ID of the resume
        similarity_score (float): Calculated similarity score
        matching_skills (list): List of matching skills
        
    Returns:
        int: The ID of the inserted analysis result
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO analysis_results (job_id, resume_id, similarity_score, matching_skills) VALUES (%s, %s, %s, %s) RETURNING id",
            (job_id, resume_id, similarity_score, matching_skills)
        )
        
        result_id = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return result_id
    except Exception as e:
        logger.error(f"Error saving analysis result: {str(e)}")
        raise

def get_previous_analyses(limit=10):
    """
    Get previous analyses from the database
    
    Args:
        limit (int): Maximum number of analyses to return
        
    Returns:
        list: List of dictionaries containing analysis data
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            ar.id, 
            jd.description, 
            r.candidate_name, 
            r.filename,
            ar.similarity_score,
            ar.matching_skills,
            ar.created_at
        FROM 
            analysis_results ar
        JOIN 
            job_descriptions jd ON ar.job_id = jd.id
        JOIN 
            resumes r ON ar.resume_id = r.id
        ORDER BY 
            ar.created_at DESC
        LIMIT %s
        """, (limit,))
        
        analyses = []
        for row in cursor.fetchall():
            analyses.append({
                'id': row[0],
                'description': row[1],
                'candidate_name': row[2],
                'filename': row[3],
                'similarity_score': row[4],
                'matching_skills': row[5],
                'created_at': row[6]
            })
        
        cursor.close()
        conn.close()
        
        return analyses
    except Exception as e:
        logger.error(f"Error retrieving previous analyses: {str(e)}")
        return []

# Create tables when the module is imported
try:
    create_tables()
except Exception as e:
    logger.error(f"Failed to create database tables: {str(e)}")