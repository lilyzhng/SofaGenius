FROM python:3.11-slim

# Standard tools for professional analysis tasks
RUN apt-get update && apt-get install -y --no-install-recommends \
    jq curl wget poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Python packages for data analysis
RUN pip install --no-cache-dir \
    pandas openpyxl pdfplumber tabulate xlrd

WORKDIR /app

# Create data and output directories
RUN mkdir -p /app/data /app/output /logs/verifier
