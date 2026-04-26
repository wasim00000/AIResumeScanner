# Usage Guide

Follow these steps to analyze resumes against a job description and leverage the assistant.

## Steps

1. Paste your job description into the text area.
2. Upload one or more resumes (PDF or DOCX).
3. Adjust filters:
   - Minimum match percentage
   - Top N candidates
4. Click Analyze (if present) or wait for automatic processing.
5. Explore results:
   - Top candidates table
   - Charts: match percentage and matching skill counts
   - Common matching skills
6. Use the Assistant (right panel):
   - Quick prompts (compare, list skills, summarize)
   - Type your own question
   - Toggle context: include summary and job skills
   - Clear or export chat transcript
7. Visit Analysis History to view saved analyses.

## Notes

- Resume parsing uses PyPDF2 and python-docx; scanned PDFs without embedded text may not extract well.
- Data is stored locally under `data/` as JSON.

### Docker users

If running in Docker, see SETUP.md for build/run commands and access the app at [http://localhost:8502](http://localhost:8502)
