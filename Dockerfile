FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/
COPY manage_tokens.py .
COPY export_interviews.py .

# Create data directory
RUN mkdir -p /app/data/audio_cache /app/data/exports

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.main:create_app

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
