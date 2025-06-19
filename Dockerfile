FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION="1.4.0" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="$POETRY_HOME/bin:$PATH" \
    PORT=5000

# Install system dependencies, SQLite, gzip, and Poetry
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl sqlite3 gzip tini \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && mv "$POETRY_HOME/bin/poetry" /usr/local/bin/ \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy Poetry files for dependency installation
COPY poetry.lock pyproject.toml /app/

# Install Python dependencies using Poetry
RUN poetry install --no-root

# Copy the entire project into the container
COPY . /app

# Expose the port Flask will run on
EXPOSE $PORT

# Copy the custom entrypoint script into the container
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Use tini as the entrypoint to manage multiple processes
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]

# Run Flask (API) and Huey worker processes in parallel
CMD ["sh", "-c", "poetry run gunicorn -w 2 -b 0.0.0.0:$PORT app:app & poetry run huey_consumer.py tasks.huey"]

