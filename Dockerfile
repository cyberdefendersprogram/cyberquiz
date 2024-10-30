# Use an official Python 3.11 image as the base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION="1.4.0" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies and Poetry
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && mv "$POETRY_HOME/bin/poetry" /usr/local/bin/ \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy Poetry files to install dependencies
COPY poetry.lock pyproject.toml /app/

# Install Python dependencies with Poetry
RUN poetry install --no-root --no-dev

# Copy the entire project into the container
COPY . /app

# Expose the port Flask will run on
EXPOSE ${PORT}

# Run Gunicorn with Poetry for production
CMD ["poetry", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:${PORT}", "app:app"]

