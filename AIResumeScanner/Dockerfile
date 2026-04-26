# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (leverage Docker layer caching)
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy app source
COPY . .

EXPOSE 8502

# Run Streamlit on 0.0.0.0 for Docker networking
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port", "8502", "--server.address", "0.0.0.0"]
