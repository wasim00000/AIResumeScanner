# AI Resume Scanner

A Streamlit-based application that analyzes and ranks resumes against a job description using NLP and skill matching. It provides interactive visualizations, an AI shortlisting assistant, and a modern dark-themed UI.

## Features

- Upload multiple PDFs/DOCX resumes, parse text, and extract skills/entities
- Compare resumes to a job description with TF‑IDF similarity and skill matching
- Visualize match percentages and skill counts with Plotly (dark theme)
- AI shortlisting assistant with quick prompts, context toggles, and chat history export
- Save and browse previous analyses (JSON persistence, no external DB)
- Professional, responsive UI with a dark theme and sticky chat panel

## Tech Stack

- Python, Streamlit, Plotly, Pandas, NumPy
- scikit-learn (TF‑IDF + cosine similarity)
- PyPDF2, python-docx for document parsing
- JSON-based storage (in `data/`)

## Quickstart (Windows PowerShell)

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

1. Install dependencies

```powershell
pip install -r requirements.txt
```

1. Run the app

```powershell
.\.venv\Scripts\python -m streamlit run .\app.py --server.port 8502
```

Then open [http://localhost:8502](http://localhost:8502)

Notes

- If another process uses the default port, change it via `--server.port` or in `.streamlit/config.toml`.
- Always run via the venv python to avoid missing packages.

### Docker (alternative)

Build and run with Docker:

```powershell
docker build -t ai-resume-scanner .
docker run --rm -it -p 8502:8502 ai-resume-scanner
```

Or with docker-compose:

```powershell
docker compose up --build
```

Open [http://localhost:8502](http://localhost:8502)

## Usage

1. Paste a job description
2. Upload one or more resumes (PDF/DOCX)
3. Adjust filters (minimum match, top N)
4. Review results and charts
5. Use the AI assistant (right panel) to compare candidates, find skills, or summarize
6. Browse Analysis History to revisit past results

## Configuration

- Streamlit theme and server settings: `.streamlit/config.toml`
- Data files are stored under `data/`
- No external keys required; AI assistant leverages a public HF inference endpoint with fallback rules

## Project Structure

```text
app.py                 # Streamlit UI, orchestration, dark theme
ranking_system.py      # TF‑IDF similarity + ranking
resume_parser.py       # PDF/DOCX text extraction
nlp_processor.py       # Preprocess text, skills/entities extraction
utils.py               # Chat assistant call + helpers
database.py            # JSON persistence
requirements.txt       # Python dependencies
data/                  # JSON datasets (inputs/results)
.streamlit/config.toml # Theme + server config
```

## Documentation

See the docs folder for detailed guides:

- docs/SETUP.md
- docs/USAGE.md
- docs/CONFIGURATION.md
- docs/MODULES.md
- docs/DATA_FORMATS.md
- docs/TROUBLESHOOTING.md
- docs/SECURITY_PRIVACY.md
- docs/CHANGELOG.md
- docs/AIResumeScanner-Documentation.html (print-ready hard copy)

## Troubleshooting (quick)

- ModuleNotFoundError (e.g., plotly): ensure venv is active and install requirements
- Port in use: change `--server.port` or update `.streamlit/config.toml`
- PDF parsing issues: try another PDF extractor or ensure the file isn’t scanned image-only

## License

Add your license of choice here (e.g., MIT).
