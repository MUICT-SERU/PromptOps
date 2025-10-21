FROM python:3.9.13-slim


# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-venv build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./api /app/api

# Create virtual environment
RUN python3 -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# Install packages in smaller, logical groups
RUN pip install --no-cache-dir -U pip setuptools wheel

# Install base packages
RUN pip install --no-cache-dir -U \
    "pandas>=1.3.0,<2.0.0" \
    numpy==1.23.0 \
    scipy==1.8.1 \
    scikit-learn==1.6.1

# Install NLP-related packages
RUN pip install --no-cache-dir -U \
    nltk==3.9.1 \
    PyDictionary==2.0.1 \
    textblob==0.19.0 \
    spacy==3.5.0 \
    coreferee==1.4.1 \
    inflect==7.5.0

# Install AI-related packages
RUN pip install --no-cache-dir -U \
    openai==1.75.0 \
    anthropic==0.49.0 \
    huggingface-hub==0.30.2 \
    sentence-transformers==4.1.0 \
    transformers==4.48.1 \
    torch==2.6.0 \
    accelerate \
    litellm==1.24.5 \
    llama-stack

# Install Google packages - try to avoid futures dependency
RUN pip install --no-cache-dir -U \
    google-generativeai==0.8.5 && \
    pip uninstall -y futures || true

# Install remaining packages
RUN pip install --no-cache-dir -U \
    tqdm \
    ipywidgets \
    openpyxl==3.1.5 \
    environs==14.1.1 \
    python-multipart==0.0.20 \
    uvicorn==0.34.2 \
    fastapi==0.115.7 \
    redis>=5.0.0 \
    celery \
    pycryptodome


ENV PYTHONPATH=/app

# directly pip-install the spaCy model wheels:
RUN python -m spacy download en_core_web_sm \
 && python -m spacy download en_core_web_lg

# then install coreferee & its en model:
RUN python -m coreferee install en

EXPOSE 5328
HEALTHCHECK --interval=10s --timeout=2s --retries=5 \
    CMD curl -f http://localhost:5328/health || exit 1

CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "5328"]
