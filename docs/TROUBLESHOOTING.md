# Troubleshooting

## Plotly not found

- Symptom: `ModuleNotFoundError: No module named 'plotly'`
- Fix: Activate the venv and reinstall requirements:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Port already in use

- Symptom: Streamlit fails to start due to occupied port.
- Fix: Run on a free port:

```powershell
.\.venv\Scripts\python -m streamlit run .\app.py --server.port 8503
```

## No text extracted from PDF

- Symptom: Empty or poor extraction for scanned PDFs.
- Fix: Use a text-based PDF or run OCR externally before upload.

## Slow or failed AI responses

- Symptom: Timeout or unhelpful results.
- Fix: The app falls back to a local rule-based assistant. Check internet connectivity or try again.

## General tips

- Always run via the project virtual environment
- Keep `requirements.txt` in sync with your environment
