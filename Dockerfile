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

# Expose port 7001 (Railway will proxy external traffic to this port)
EXPOSE 7001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7001/health').read()"

# Run the application with hypercorn
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:7001", "--workers", "2"]
