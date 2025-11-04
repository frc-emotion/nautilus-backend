# Use official Python image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.4 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install poetry
RUN pip install poetry==${POETRY_VERSION}

# Set working directory
WORKDIR /app

# Copy dependency files
COPY poetry.lock pyproject.toml /app/

# Install dependencies (no dev dependencies in production)
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root --only main

# Copy application code
COPY . /app

# Expose port (Railway will set PORT env var dynamically)
EXPOSE 7001

# Note: Railway uses its own health check mechanism (healthcheckPath in railway.toml)
# Docker HEALTHCHECK is disabled in favor of Railway's health checks

# Run the application with hypercorn
# Uses shell to expand PORT variable (Railway sets PORT dynamically)
CMD ["sh", "-c", "hypercorn main:app --bind 0.0.0.0:${PORT:-7001} --workers 2"]
