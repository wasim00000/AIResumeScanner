# Security & Privacy

## Data handling

- Files are processed locally and not uploaded to external services by default
- Results and inputs are stored in local JSON files under `data/`
- Avoid uploading sensitive PII where possible; prefer sanitized resumes for demos

## Logging

- Errors/warnings may include filenames or brief context, but not full document contents

## Network calls

- The AI assistant may call a public inference endpoint; if that’s undesirable, disable it or limit to the rule-based fallback in `utils.py`

## Recommendations

- Clear `data/` regularly for sensitive projects
- Consider full encryption at rest if storing real candidate data
- Add user consent and data retention notices if used in production
