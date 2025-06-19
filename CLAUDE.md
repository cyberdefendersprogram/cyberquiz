# CLAUDE.md - CyberQuiz Development Guide

## Project Overview
Flask-based cybersecurity quiz platform for educational institutions (CIS 53, 55, 60 courses).

## Tech Stack
- Backend: Flask (Python 3.11+)
- Database: SQLite with custom migrations
- Task Queue: Huey
- Dependencies: Poetry
- Containerization: Docker/Docker Compose

## Development Commands
```bash
# Setup
poetry install
cp .env.example .env

# Database
poetry run python migrations.py

# Development server
poetry run flask run

# Background tasks
poetry run huey_consumer.py tasks.huey

# Docker
docker-compose up --build

# Testing
# Add your test commands here when available
```

## Project Structure
- `app.py` - Main Flask application
- `migrations/` - Database migrations (SQL & Python)
- `quizzes/` - Quiz content (YAML files by course)
- `templates/` - Jinja2 HTML templates
- `tasks.py` - Huey background tasks

## Common Tasks
- Adding quizzes: Create YAML in `quizzes/{course}/` then run migration 023
- Database changes: Create migration in `migrations/` then run `migrations.py`
- Admin access: Currently hardcoded email in `app.py:48`

## Security Notes
- Uses parameterized queries for SQL injection protection
- Admin panel has table whitelisting
- Backup tasks use subprocess (not shell commands)