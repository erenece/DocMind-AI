FROM python:3.12-slim

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# For DOC -> DOCX conversion (best-effort)
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000 8501

# Default: run API (override in compose for UI)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

