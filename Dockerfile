# Use the official Python image as the base.
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.6.1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

RUN pip install poetry

WORKDIR /app
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

COPY . /app

CMD ["hypercorn", "main:app"]
