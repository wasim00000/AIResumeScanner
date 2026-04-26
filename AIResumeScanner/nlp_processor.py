import re
import json
from pathlib import Path

def load_skill_patterns():
    """Load skill patterns from JSON file"""
    try:
        patterns_file = Path(__file__).resolve().parent / "data" / "skill_patterns.json"
        with open(patterns_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
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
    "c#", "c++", "node.js", "scala", "golang", "rust", "swift", "kotlin", "r", "matlab", "sas", "stata",
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

SKILL_CANONICAL_MAP = {
    "cplusplus": "c++",
    "nodejs": "node.js",
    "dotnet": ".net",
    "aspnet": "asp.net",
}


def _canonicalize_skill(value):
    normalized = str(value).lower().strip()
    compact = re.sub(r'[\s._/\-]', '', normalized)
    return SKILL_CANONICAL_MAP.get(compact, normalized)


def _ordered_unique(values):
    seen = set()
    ordered = []
    for value in values:
        normalized = _canonicalize_skill(value)
        if normalized and normalized not in seen:
            ordered.append(normalized)
            seen.add(normalized)
    return ordered


def _compile_skill_pattern(pattern):
    pattern = str(pattern).strip()
    if not pattern:
        return None

    # Treat explicitly escaped or regex-like patterns as regex; otherwise match the literal text.
    regex_like = "\\" in pattern or any(ch in pattern for ch in "[]()|^${}")
    candidate = pattern if regex_like else re.escape(pattern)

    try:
        return re.compile(rf"(?<!\w){candidate}(?!\w)", re.IGNORECASE)
    except re.error:
        return re.compile(re.escape(pattern), re.IGNORECASE)


def _match_pattern(text, pattern):
    regex = _compile_skill_pattern(pattern)
    if regex:
        matches = [match.group(0).strip().lower() for match in regex.finditer(text)]
        if matches:
            return matches

    # Literal fallback for symbol-heavy skills such as C++ or node.js.
    compact_text = re.sub(r'[\s._/\-]', '', text.lower())
    fallback_literal = re.sub(r'\\', '', str(pattern).lower())
    fallback_literal = re.sub(r'[\s._/\-?]', '', fallback_literal)
    if fallback_literal and fallback_literal in compact_text:
        return [fallback_literal]

    return []

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

    text = str(text).replace("\r\n", "\n").replace("\r", "\n")

    # Keep skill-relevant punctuation so tokens like C++, C#, and CI/CD survive preprocessing.
    text = re.sub(r'[^\w\s\+\#\.\-\/]', ' ', text)

    # Collapse extra whitespace without removing punctuation that may be part of a skill token.
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
    text_lower = str(text).lower()

    # Extract skills using regex patterns from JSON
    for category, patterns in SKILL_PATTERNS.items():
        if not isinstance(patterns, list):
            continue
        for pattern in patterns:
            for skill_found in _match_pattern(text_lower, pattern):
                if skill_found and len(skill_found) > 1:
                    matched_skills.append(skill_found)

    # Check additional skills with simple matching
    for skill in ADDITIONAL_SKILLS:
        if _match_pattern(text_lower, skill):
            matched_skills.append(skill.lower())

    # Check soft skills
    for skill in SOFT_SKILLS:
        if _match_pattern(text_lower, skill):
            matched_skills.append(skill.lower())

    return _ordered_unique([skill for skill in matched_skills if len(skill.strip()) > 1])

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
    text = str(text)
    text_lower = text.lower()

    # Extract potential person names from the first visible segment or first few words.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name_candidates = [lines[0]] if lines else [text[:120].strip()]
    for candidate in name_candidates:
        candidate = re.split(
            r'\b(?:email|e-mail|phone|mobile|linkedin|github|address)\b',
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip(" -|,;:")
        words = [word.strip(".,") for word in candidate.split() if word.strip(".,")]
        lowered = {word.lower() for word in words}
        if (
            2 <= len(words) <= 4
            and not any(char.isdigit() for char in candidate)
            and not lowered.intersection({
                'resume', 'cv', 'curriculum', 'profile', 'summary',
                'experience', 'skills', 'objective', 'education', 'projects', 'contact'
            })
        ):
            entities.append((" ".join(words).title(), 'PERSON'))
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

    text_lower = str(text).lower()
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
        (r'bachelor[\'s]*\s*(?:degree)?', "bachelor's degree"),
        (r'master[\'s]*\s*(?:degree)?', "master's degree"),
        (r'phd', 'phd'),
        (r'doctorate', 'doctorate'),
        (r'b\.s\.?', 'b.s.'),
        (r'b\.a\.?', 'b.a.'),
        (r'm\.s\.?', 'm.s.'),
        (r'm\.a\.?', 'm.a.'),
        (r'mba', 'mba'),
    ]
    for pattern, label in education_keywords:
        if re.search(pattern, text_lower):
            requirements['education_requirements'].append(label)

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

    # Remove duplicates from all lists while preserving order
    for key in requirements:
        if isinstance(requirements[key], list):
            requirements[key] = _ordered_unique(requirements[key])

    return requirements
