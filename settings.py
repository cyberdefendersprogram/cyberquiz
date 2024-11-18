# settings.py
import os

# Database configuration
DATABASE_NAME = os.getenv('DATABASE_NAME', 'app.db')

# Email configuration
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.forwardemail.net')  # Default is optional
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'vaibhavb@cyberdefendersprogram.com')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # No default for security
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'vaibhavb@cyberdefendersprogram.com')

# Secret key (you might want to generate a unique key for production)
SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')

# Huey instance with SQLite backend
HUEY_SQLITE = os.getenv('HUEY_SQLITE', 'data/huey.sqlite')

# Google Drive API Configuration
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')  # Folder ID where backups are stored
LOCAL_DB_PATH = os.getenv('LOCAL_DB_PATH', '/app/data/app.db')  # SQLite database path
LOCAL_RESTORE_PATH = os.getenv('LOCAL_RESTORE_PATH', '/app/data/restored.db')  # Restored database path

