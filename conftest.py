import pytest
import tempfile
import os
from app import app, get_db
import sqlite3


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    import settings
    
    db_fd, test_db_path = tempfile.mkstemp()
    original_db = settings.DATABASE_NAME
    settings.DATABASE_NAME = test_db_path
    
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            init_test_db(test_db_path)
        yield client
    
    settings.DATABASE_NAME = original_db
    os.close(db_fd)
    os.unlink(test_db_path)


def init_test_db(db_path):
    """Initialize the test database with basic schema."""
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            student_id TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class_name TEXT,
            total_questions INTEGER DEFAULT 0
        )
    ''')
    conn.execute('''
        CREATE TABLE quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quiz_id INTEGER,
            score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
        )
    ''')
    
    # Insert test data
    conn.execute("INSERT INTO users (email, student_id) VALUES ('test@example.com', 'S123')")
    conn.execute("INSERT INTO quizzes (name, class_name, total_questions) VALUES ('Test Quiz', 'CIS 53', 2)")
    conn.execute("INSERT INTO quiz_questions (quiz_id, question, correct_answer) VALUES (1, 'What is 2+2?', '4')")
    conn.execute("INSERT INTO quiz_questions (quiz_id, question, correct_answer) VALUES (1, 'What is 3+3?', '6')")
    
    conn.commit()
    conn.close()