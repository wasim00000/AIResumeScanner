# Configuration

## Streamlit configuration

File: `.streamlit/config.toml`

- Server
  - `server.port` (e.g., 8502)
  - `server.address` (e.g., localhost)
- Theme (dark)
  - `base = "dark"`
  - Custom colors for primary/background/text

## Application settings

- Data location: `data/`
- No API keys required (assistant uses a public endpoint with fallback)

## Environment

Recommended to run in a Python virtual environment and install from `requirements.txt`.
