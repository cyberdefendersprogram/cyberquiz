# CyberQuiz - Interactive Cybersecurity Quiz Platform

A Flask-based web application for administering cybersecurity quizzes and assessments. Built for educational institutions offering cybersecurity courses (CIS 53, CIS 55, CIS 60, etc.).

## Features

- **Magic Link Authentication** - Passwordless login via email
- **Multi-Course Support** - Organized quizzes by class (CIS 53, 55, 60)
- **Interactive Quizzes** - Multiple choice questions with instant scoring
- **Progress Tracking** - User dashboard with quiz history and scores
- **Admin Panel** - Database management and user administration
- **Automated Backups** - Google Drive integration for data protection
- **Responsive Design** - Mobile-friendly interface with Tailwind CSS

## Tech Stack

- **Backend**: Flask (Python 3.11+)
- **Database**: SQLite with custom migration system
- **Task Queue**: Huey for background jobs
- **Email**: Flask-Mail with SMTP support
- **Containerization**: Docker & Docker Compose
- **Frontend**: Jinja2 templates with Tailwind CSS
- **Cloud Storage**: Google Drive API for backups

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cyberquiz
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run database migrations**
   ```bash
   poetry run python migrations.py
   ```

5. **Start the development server**
   ```bash
   poetry run flask run
   ```

The application will be available at `http://localhost:5000`

### Docker Setup

1. **Development environment**
   ```bash
   docker-compose up --build
   ```

2. **Production environment**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database
DATABASE_NAME=data/app.db

# Flask
SECRET_KEY=your-secret-key-here
PORT=5000

# Email Configuration
MAIL_SERVER=smtp.forwardemail.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=your-email@domain.com

# Google Drive Backup (Optional)
GOOGLE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...}
GOOGLE_DRIVE_FOLDER_ID=your-drive-folder-id

# Huey Task Queue
HUEY_SQLITE=data/huey.sqlite
```

### Admin Access

Admin access is granted to the email address specified in `app.py:48`. To change the admin user:

1. Update the hardcoded email in the admin check functions
2. Or set it via environment variable (recommended improvement)

## Project Structure

```
cyberquiz/
\ app.py                 # Main Flask application
\ settings.py           # Configuration management
\ tasks.py              # Background tasks (Huey)
\ migrations.py         # Database migration runner
\ migrations/           # SQL and Python migrations
\ templates/            # Jinja2 HTML templates
\ quizzes/             # Quiz content (YAML files)
    \  cis_53/          # Network Security quizzes
    \ cis_55/          # Cybersecurity Fundamentals
    \ cis_60/          # Digital Forensics
\ data/                # SQLite databases
  \ docker-compose.yml   # Development container setup
  \ docker-compose.prod.yml # Production with Nginx/SSL
  \ Dockerfile           # Container definition
entrypoint.sh        # Container startup script
pyproject.toml       # Poetry dependencies
```

## Development Workflow

### Adding New Quizzes

1. Create a YAML file in the appropriate `quizzes/` subdirectory:
   ```yaml
   name: "Quiz Title"
   questions:
     - question: "What is cybersecurity?"
       options:
         - "A) Computer games"
         - "B) Protecting digital assets"
         - "C) Social media"
         - "D) Web design"
       answer: "B"
   ```

2. Run the quiz loader migration:
   ```bash
   poetry run python migrations/023_reload_all_quizzes_from_directories.py
   ```

### Database Migrations

1. **Create a new migration**
   ```bash
   # For SQL migrations
   touch migrations/024_your_migration_name.sql
   
   # For Python migrations
   touch migrations/024_your_migration_name.py
   ```

2. **Run migrations**
   ```bash
   poetry run python migrations.py
   ```

### Testing

Run the test suite to ensure everything is working correctly:

```bash
# Using Poetry (local)
poetry run pytest

# Using Docker (recommended)
docker compose -f docker-compose.test.yml run --rm test
```

The test suite includes:
- Homepage and login page functionality
- Authentication and authorization tests  
- Error handling (404 pages)
- Database integration tests

### Background Tasks

The application uses Huey for background tasks:

- **Nightly backups** - Automated Google Drive backups at midnight
- **Manual backup/restore** - Admin-triggered operations

Start the Huey worker:
```bash
poetry run huey_consumer.py tasks.huey
```

## Use Cases

### Educational Institution
- **Course Management**: Organize quizzes by course code (CIS 53, 55, 60)
- **Student Assessment**: Track individual student progress and scores
- **Content Delivery**: Serve interactive cybersecurity curriculum

### Training Organizations
- **Certification Prep**: Deliver practice exams for cybersecurity certifications
- **Progress Tracking**: Monitor learner advancement through course materials
- **Flexible Content**: Easy addition of new quiz content via YAML files

### Corporate Training
- **Security Awareness**: Deploy security awareness quizzes to employees
- **Compliance Training**: Track completion of mandatory security training
- **Custom Content**: Adapt quiz content to organization-specific policies

## API Endpoints

### Public Routes
- `GET /` - Landing page
- `GET /login` - Magic link login form
- `GET /login/<token>` - Magic link authentication
- `GET /select_quiz` - Quiz selection page
- `GET /quiz/<id>` - Quiz taking interface
- `POST /submit_quiz/<id>` - Quiz submission

### Authenticated Routes
- `GET /dashboard` - User dashboard with quiz history
- `GET /update_account` - Account settings
- `GET /logout` - User logout

### Admin Routes
- `GET /admin` - Database administration panel
- `POST /backup` - Trigger manual backup
- `POST /restore` - Restore from backup
- `POST /execute_query` - Execute custom SQL queries

## Production Deployment

### Using Docker Compose (Recommended)

1. **Set up production environment**
   ```bash
   cp docker-compose.prod.yml docker-compose.yml
   ```

2. **Configure SSL certificates**
   ```bash
   # Update nginx.conf with your domain
   # Set up Let's Encrypt certificates
   ```

3. **Deploy**
   ```bash
   docker-compose up -d
   ```

### Manual Deployment

1. **Install dependencies**
   ```bash
   poetry install --no-dev
   ```

2. **Set production environment variables**

3. **Run with Gunicorn**
   ```bash
   poetry run gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

4. **Set up reverse proxy** (Nginx recommended)

## Security Considerations

� **Important**: This application has several security considerations for production use:

✅ **Security Improvements Applied**:

- **SQL Injection Protection**: All database queries now use parameterized queries or proper validation
- **Admin Panel Security**: Table access is restricted to whitelisted tables with proper quoting
- **Query Validation**: Custom queries are validated for dangerous keywords and length limits
- **Shell Command Security**: Background tasks now use `subprocess` instead of `os.system()`

⚠️ **Remaining Considerations for Production**:
- **Hard-coded Admin**: Admin access is hard-coded to a specific email (consider environment variables)
- **Default Secret Key**: Change the default secret key in production
- **Rate Limiting**: Consider adding rate limiting for API endpoints
- **Input Validation**: Add comprehensive input validation and CSRF protection

## Feature Backlog
- Immediate: Add CIS 52 (Cloud Security) content and improve existing quiz quality
- AI Features (content generation)
- Enhanced question types and better admin tools
- LMS integration and advanced analytics

## Recent Security Updates
**v1.1.0 Security Fixes**:
- Fixed SQL injection vulnerability in admin panel (`app.py:58`)
- Enhanced custom query validation with keyword filtering
- Replaced shell commands with secure `subprocess` calls in backup tasks
- Added table name whitelisting for admin database access

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues:
- Create an issue on GitHub
- Contact: vaibhavb@gmail.com

## Acknowledgments
- Built for cybersecurity education
- Supports multiple course curricula (CIS 53, 55, 60)
- Designed for ease of content management and student engagement
