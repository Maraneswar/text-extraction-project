# Use a lean Python 3.10 image as base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies for OCR and NLP
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model during build to improve runtime performance
RUN python -m spacy download en_core_web_sm

# Create uploads directory
RUN mkdir -p /app/uploads

# Copy the rest of the application code
COPY . .

# Expose the API port
EXPOSE 8000

# Start the application using Uvicorn
CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]
