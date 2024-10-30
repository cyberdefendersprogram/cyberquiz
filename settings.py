# settings.py
import os

# Database configuration
DATABASE_NAME = os.getenv('DATABASE_NAME', '/app/data/app.db')

# Email configuration
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.forwardemail.net')  # Default is optional
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'vaibhavb@cyberdefendersprogram.com')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # No default for security
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'vaibhavb@cyberdefendersprogram.com')

# Secret key (you might want to generate a unique key for production)
SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')

