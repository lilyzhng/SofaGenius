FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pdfplumber \
    pandas \
    openpyxl \
    tabulate

WORKDIR /app

# Copy task data files (PDFs, Excel, CSV) into container
COPY data/ /app/data/

RUN mkdir -p /app/output
