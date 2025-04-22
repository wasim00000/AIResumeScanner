import spacy
import re
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load spaCy models
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # If model isn't downloaded, download it
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Common technical skills and programming languages
COMMON_TECH_SKILLS = {
    "python", "java", "javascript", "c++", "c#", "ruby", "php", "swift", "kotlin", "scala",
    "golang", "rust", "typescript", "html", "css", "sql", "mongodb", "postgresql", "mysql",
    "oracle", "sqlite", "redis", "cassandra", "dynamodb", "firebase", "aws", "azure", "gcp",
    "docker", "kubernetes", "jenkins", "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "slack", "terraform", "ansible", "puppet", "chef", "react", "angular", "vue", "svelte",
    "jquery", "bootstrap", "tailwind", "material-ui", "sass", "less", "webpack", "babel", "nodejs",
    "express", "django", "flask", "fastapi", "spring", "hibernate", "linq", "entity framework",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn",
    "tableau", "power bi", "excel", "powerpoint", "word", "outlook", "linux", "windows", "macos",
    "agile", "scrum", "kanban", "waterfall", "api", "rest", "graphql", "soap", "json", "xml",
    "oauth", "jwt", "saml", "devops", "machine learning", "deep learning", "data science",
    "big data", "data mining", "data analysis", "data visualization", "nlp", "computer vision"
}

# Soft skills
COMMON_SOFT_SKILLS = {
    "communication", "teamwork", "leadership", "problem solving", "critical thinking",
    "time management", "adaptability", "creativity", "emotional intelligence", "negotiation",
    "conflict resolution", "decision making", "stress management", "flexibility", "patience",
    "empathy", "self-motivation", "reliability", "work ethic", "attention to detail",
    "organization", "interpersonal", "presentation", "mentoring", "coaching"
}

# Combined skills set for faster lookups
ALL_SKILLS = COMMON_TECH_SKILLS.union(COMMON_SOFT_SKILLS)

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
    Extract potential skills from text using NLP and a predefined list
    
    Args:
        text (str): Input text (should be preprocessed)
        
    Returns:
        list: Extracted skills
    """
    if not text:
        return []
        
    # Process with spaCy
    doc = nlp(text)
    
    # Extract noun phrases as potential skills
    potential_skills = set()
    
    # Extract noun chunks (potential multi-word skills)
    for chunk in doc.noun_chunks:
        potential_skills.add(chunk.text.lower())
    
    # Extract individual tokens that might be skills
    for token in doc:
        if not token.is_stop and not token.is_punct and len(token.text) > 1:
            potential_skills.add(token.text.lower())
    
    # Match with known skills list
    matched_skills = []
    for skill in potential_skills:
        # Check for exact matches
        if skill in ALL_SKILLS:
            matched_skills.append(skill)
        else:
            # Check for partial matches within known skills
            for known_skill in ALL_SKILLS:
                if (len(known_skill.split()) > 1 and skill in known_skill) or \
                   (len(skill.split()) > 1 and known_skill in skill):
                    matched_skills.append(known_skill)
                    break
    
    # Also check for n-grams in the text that might match skills
    text_words = text.split()
    for i in range(len(text_words)):
        for j in range(1, 4):  # Check 1, 2, and 3-grams
            if i+j <= len(text_words):
                ngram = " ".join(text_words[i:i+j])
                if ngram in ALL_SKILLS and ngram not in matched_skills:
                    matched_skills.append(ngram)
    
    # Remove duplicates and return
    return list(set(matched_skills))

def extract_entities(text):
    """
    Extract named entities from text using spaCy
    
    Args:
        text (str): Input text
        
    Returns:
        list: List of (entity_text, entity_label) tuples
    """
    if not text:
        return []
        
    # Process with spaCy
    doc = nlp(text)
    
    # Extract entities
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    return entities
