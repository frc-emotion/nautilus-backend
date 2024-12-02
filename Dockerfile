# Use the official Python image as the base.
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        && curl -sSL https://install.python-poetry.org | python3 - \
        && apt-get purge -y --auto-remove curl \
        && rm -rf /var/lib/apt/lists/*

# Copy only the pyproject.toml and poetry.lock to leverage Docker cache
COPY pyproject.toml poetry.lock* /app/

# Install Python dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Expose the port your application runs on
EXPOSE 3000

CMD ["python", "main.py"]
