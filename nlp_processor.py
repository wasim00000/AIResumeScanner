import re
import string
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def load_skill_patterns():
    """Load skill patterns from JSON file"""
    try:
        patterns_file = os.path.join(os.path.dirname(__file__), 'data', 'skill_patterns.json')
        with open(patterns_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback patterns if file not found
        return {
            "programming": ["python", "java", "javascript", "c\\+\\+", "typescript", "php", "ruby"],
            "web": ["html", "css", "react", "angular", "vue", "node\\.?js", "express", "django", "flask"],
            "data_science": ["machine learning", "deep learning", "pandas", "numpy", "sklearn", "tensorflow", "pytorch"],
            "database": ["sql", "mysql", "postgresql", "mongodb", "redis", "oracle"],
            "devops": ["docker", "kubernetes", "aws", "azure", "gcp", "jenkins", "ci/cd", "terraform"]
        }

# Load skill patterns
SKILL_PATTERNS = load_skill_patterns()

# Additional comprehensive skills for fallback
ADDITIONAL_SKILLS = {
    "c#", "scala", "golang", "rust", "swift", "kotlin", "r", "matlab", "sas", "stata",
    "git", "github", "gitlab", "bitbucket", "jira", "confluence", "slack", "trello",
    "ansible", "puppet", "chef", "vagrant", "nginx", "apache", "elasticsearch", "cassandra",
    "firebase", "dynamodb", "sqlite", "redshift", "snowflake", "tableau", "power bi", 
    "excel", "powerpoint", "word", "outlook", "linux", "windows", "macos", "ubuntu",
    "agile", "scrum", "kanban", "waterfall", "lean", "api", "rest", "graphql", "soap", 
    "json", "xml", "yaml", "oauth", "jwt", "saml", "microservices", "serverless",
    "big data", "data mining", "data analysis", "data visualization", "nlp", "computer vision",
    "neural networks", "reinforcement learning", "statistics", "analytics", "reporting",
    "hadoop", "spark", "kafka", "airflow", "etl", "data warehouse", "business intelligence"
}

# Soft skills and general terms
SOFT_SKILLS = {
    "communication", "teamwork", "leadership", "problem solving", "critical thinking",
    "time management", "adaptability", "creativity", "emotional intelligence", "negotiation",
    "conflict resolution", "decision making", "stress management", "flexibility", "patience",
    "empathy", "self-motivation", "reliability", "work ethic", "attention to detail",
    "organization", "interpersonal", "presentation", "mentoring", "coaching", "collaboration",
    "project management", "client management", "stakeholder management", "customer service"
}

def preprocess_text(text):
    """
    Preprocess text by converting to lowercase, removing non-alphanumeric characters,
    and extra whitespace.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Preprocessed text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace newlines with spaces
    text = re.sub(r'\n+', ' ', text)
    
    # Remove special characters but keep spaces between words
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_skills(text):
    """
    Extract potential skills from text using pattern matching and regex
    
    Args:
        text (str): Input text (should be preprocessed)
        
    Returns:
        list: Extracted skills
    """
    if not text:
        return []
    
    matched_skills = []
    text_lower = text.lower()
    
    # Extract skills using regex patterns from JSON
    for category, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            # Convert pattern to case-insensitive regex
            try:
                regex_pattern = r'\b' + pattern.replace('\\', '\\') + r'\b'
                matches = re.finditer(regex_pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    skill_found = match.group(0)
                    # Clean up the matched skill
                    skill_found = re.sub(r'[^\w\s\+\-\.]', '', skill_found).strip()
                    if skill_found and len(skill_found) > 1:
                        matched_skills.append(skill_found)
            except re.error:
                # If regex fails, fall back to simple string matching
                if pattern.lower() in text_lower:
                    matched_skills.append(pattern.replace('\\', ''))
    
    # Check additional skills with simple matching
    tokens = text_lower.split()
    for skill in ADDITIONAL_SKILLS:
        if skill.lower() in text_lower:
            matched_skills.append(skill)
    
    # Check soft skills
    for skill in SOFT_SKILLS:
        if skill.lower() in text_lower:
            matched_skills.append(skill)
    
    # Remove duplicates and normalize
    unique_skills = []
    seen = set()
    for skill in matched_skills:
        skill_normalized = skill.lower().strip()
        if skill_normalized not in seen and len(skill_normalized) > 1:
            unique_skills.append(skill)
            seen.add(skill_normalized)
    
    return unique_skills

def extract_entities(text):
    """
    Extract potential named entities from text with enhanced detection
    
    Args:
        text (str): Input text
        
    Returns:
        list: List of (entity_text, entity_label) tuples
    """
    if not text:
        return []
    
    entities = []
    
    # Extract potential person names (assumes first lines might contain names)
    lines = text.split('\n')
    if lines and len(lines) > 0:
        # First few lines often contain the name
        for i, line in enumerate(lines[:3]):
            line = line.strip()
            if line and len(line.split()) <= 4 and not any(char.isdigit() for char in line):
                # Skip if it looks like a header or title
                if not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum', 'profile', 'summary']):
                    entities.append((line, 'PERSON'))
                    break
    
    # Enhanced email detection
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text, re.IGNORECASE)
    for email in emails:
        entities.append((email, 'EMAIL'))
    
    # Enhanced phone number detection
    phone_patterns = [
        r'\b(?:\+\d{1,3}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',  # US format
        r'\b(?:\+\d{1,3}\s?)?\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b',         # Simple format
        r'\b(?:\+\d{1,3}\s?)?\d{10}\b'                                  # No separators
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        for phone in phones:
            entities.append((phone.strip(), 'PHONE'))
    
    # Extract URLs/websites
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    for url in urls:
        entities.append((url, 'URL'))
    
    # Extract LinkedIn profiles
    linkedin_pattern = r'linkedin\.com/in/[^\s]+'
    linkedin_profiles = re.findall(linkedin_pattern, text, re.IGNORECASE)
    for profile in linkedin_profiles:
        entities.append((profile, 'LINKEDIN'))
    
    # Extract GitHub profiles
    github_pattern = r'github\.com/[^\s/]+'
    github_profiles = re.findall(github_pattern, text, re.IGNORECASE)
    for profile in github_profiles:
        entities.append((profile, 'GITHUB'))
    
    # Extract education degrees and certifications
    education_patterns = [
        r'\b(?:Bachelor|Master|PhD|MBA|B\.S\.|M\.S\.|B\.A\.|M\.A\.|B\.Sc\.|M\.Sc\.)[^\n]*',
        r'\b(?:Certified|Certification)\s+[A-Za-z\s]+',
        r'\b(?:AWS|Azure|Google|Microsoft|Oracle|Cisco)\s+Certified[^\n]*'
    ]
    for pattern in education_patterns:
        degrees = re.findall(pattern, text, re.IGNORECASE)
        for degree in degrees:
            entities.append((degree.strip(), 'EDUCATION'))
    
    # Extract company names (simple heuristic)
    company_keywords = ['inc', 'corp', 'ltd', 'llc', 'company', 'corporation', 'limited', 'technologies', 'systems', 'solutions']
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if any(keyword in line.lower() for keyword in company_keywords):
            if len(line.split()) <= 6:  # Reasonable company name length
                entities.append((line, 'ORGANIZATION'))
    
    # Extract years of experience
    experience_pattern = r'\b(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)\b'
    experiences = re.findall(experience_pattern, text, re.IGNORECASE)
    for exp in experiences:
        entities.append((f"{exp} years experience", 'EXPERIENCE'))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_entities = []
    for entity_text, entity_label in entities:
        entity_key = (entity_text.lower(), entity_label)
        if entity_key not in seen:
            unique_entities.append((entity_text, entity_label))
            seen.add(entity_key)
    
    return unique_entities

def extract_job_requirements(text):
    """
    Extract specific job requirements and qualifications from job description text
    
    Args:
        text (str): Job description text
        
    Returns:
        dict: Dictionary with categorized requirements
    """
    if not text:
        return {}
    
    text_lower = text.lower()
    requirements = {
        'required_skills': [],
        'preferred_skills': [],
        'experience_years': [],
        'education_requirements': [],
        'certifications': [],
        'job_type': [],
        'location': []
    }
    
    # Extract experience requirements
    exp_patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
        r'minimum\s*(?:of\s*)?(\d+)\s*(?:years?|yrs?)',
        r'at\s*least\s*(\d+)\s*(?:years?|yrs?)'
    ]
    for pattern in exp_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            requirements['experience_years'].append(f"{match} years")
    
    # Extract education requirements
    education_keywords = [
        r'bachelor[\'s]*\s*(?:degree)?', r'master[\'s]*\s*(?:degree)?', r'phd', r'doctorate',
        r'b\.s\.?', r'b\.a\.?', r'm\.s\.?', r'm\.a\.?', r'mba'
    ]
    for keyword in education_keywords:
        if re.search(keyword, text_lower):
            requirements['education_requirements'].append(keyword.replace('\\', ''))
    
    # Extract certification requirements
    cert_patterns = [
        r'(?:aws|azure|google|microsoft|oracle|cisco)\s+certified[^\n.]*',
        r'certified\s+[a-z\s]+(?:professional|associate|expert)',
        r'certification\s+in\s+[a-z\s]+'
    ]
    for pattern in cert_patterns:
        matches = re.findall(pattern, text_lower)
        requirements['certifications'].extend(matches)
    
    # Extract job type
    job_type_keywords = ['full-time', 'part-time', 'contract', 'remote', 'on-site', 'hybrid', 'freelance', 'temporary', 'permanent']
    for keyword in job_type_keywords:
        if keyword in text_lower:
            requirements['job_type'].append(keyword)
    
    # Enhanced skill extraction using required/preferred context
    required_indicators = ['required', 'must have', 'essential', 'mandatory', 'minimum', 'should have']
    preferred_indicators = ['preferred', 'nice to have', 'bonus', 'plus', 'desired', 'would be great']
    
    # Split text into sentences for better context
    sentences = re.split(r'[.!?]', text)
    
    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        if not sentence_lower:
            continue
            
        # Check if sentence contains requirement indicators
        is_required = any(indicator in sentence_lower for indicator in required_indicators)
        is_preferred = any(indicator in sentence_lower for indicator in preferred_indicators)
        
        # Extract skills from this sentence
        sentence_skills = extract_skills(sentence)
        
        if is_required:
            requirements['required_skills'].extend(sentence_skills)
        elif is_preferred:
            requirements['preferred_skills'].extend(sentence_skills)
        else:
            # Default to required if no clear indicator
            requirements['required_skills'].extend(sentence_skills)
    
    # Remove duplicates from all lists
    for key in requirements:
        if isinstance(requirements[key], list):
            requirements[key] = list(set(requirements[key]))
    
    return requirements
