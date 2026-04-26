# Modules Reference

High-level overview of key modules and their responsibilities.

## app.py

- Streamlit UI and orchestration
- Custom dark theme styles
- Tabs: Resume Analysis, Analysis History
- Assistant panel (sticky right column) with quick prompts and export

## ranking_system.py

- `calculate_similarity(job_description, resume_text, job_skills, resume_skills)`
  - Uses TF‑IDF vectors and cosine similarity; includes simple skill overlap
  - Returns: similarity score (0..1) plus details
- `rank_resumes(resumes_data)`
  - Ranks multiple resumes by the similarity score and aggregates metadata

## resume_parser.py

- `extract_text_from_pdf(file_bytes)`
- `extract_text_from_docx(file_bytes)`
- Handles empty text gracefully and logs issues

## nlp_processor.py

- `preprocess_text(text)`
- `extract_skills(text)`
- `extract_entities(text)` (simple regex/heuristics)

## utils.py

- `ai_chatbot_response(prompt)`
  - Calls a public Hugging Face inference endpoint; falls back to rule-based responses
- `display_resume_details(...)`, `get_top_keywords(...)`, `generate_chatbot_response(...)`

## database.py

- JSON-based storage utilities:
  - `save_job_description`, `save_resume`, `save_analysis_result`, `get_previous_analyses`

## data/

- `job_descriptions.json`, `resumes.json`, `analysis_results.json`, `skill_patterns.json`
