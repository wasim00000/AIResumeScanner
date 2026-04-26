# Data Formats

This project persists data in JSON files under `data/`.

## job_descriptions.json

Array of objects:

```json
{
  "id": "uuid",
  "description": "string",
  "skills": ["python", "nlp", "sql"],
  "created_at": "ISO-8601 timestamp"
}
```

## resumes.json

Array of objects:

```json
{
  "id": "uuid",
  "filename": "candidate.pdf",
  "candidate_name": "Jane Doe",
  "text": "extracted resume text",
  "skills": ["python", "pandas"],
  "created_at": "ISO-8601 timestamp"
}
```

## analysis_results.json

Array of objects (one per candidate per job description):

```json
{
  "id": "uuid",
  "job_id": "uuid",
  "resume_id": "uuid",
  "filename": "candidate.pdf",
  "candidate_name": "Jane Doe",
  "description": "job description text",
  "similarity_score": 0.82,
  "matching_skills": ["python", "nlp"],
  "missing_skills": ["aws"],
  "details": {
    "tfidf_similarity": 0.78,
    "skill_overlap": 0.86
  },
  "created_at": "ISO-8601 timestamp"
}
```

Note: Exact fields may vary slightly based on implementation; the above captures the core shape used throughout the app.
