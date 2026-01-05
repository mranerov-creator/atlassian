FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 bluevektor && chown -R bluevektor:bluevektor /app
USER bluevektor

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
