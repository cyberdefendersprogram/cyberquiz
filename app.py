from flask import Flask, request, redirect, url_for, render_template, session, flash, jsonify
from tasks import backup_to_drive, restore_from_drive
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import sqlite3
import settings
import logging

app = Flask(__name__)
app.secret_key = settings.SECRET_KEY

# Database configuration
DATABASE = settings.DATABASE_NAME

# Email configuration
app.config.update(
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_USE_TLS=settings.MAIL_USE_TLS,
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_DEFAULT_SENDER=settings.MAIL_DEFAULT_SENDER
)

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

def get_db():
    app.logger.info(f"Opening file {DATABASE}")
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def send_email(to_email, subject, body):
    """
    Sends an email using Flask-Mail.
    """
    msg = Message(subject, recipients=[to_email], sender=settings.MAIL_DEFAULT_SENDER)
    msg.body = body
    mail.send(msg)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET'])
def admin_page():
    if 'email' not in session or session['email'] != 'vaibhavb@gmail.com':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('index'))

    conn = get_db()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tables = [table['name'] for table in tables]

    db_data = {}
    for table in tables:
        data = conn.execute(f"SELECT * FROM {table}").fetchall()
        db_data[table] = [dict(row) for row in data]

    return render_template('admin.html', db_data=db_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if not user:
            conn.execute('INSERT INTO users (email) VALUES (?)', (email,))
            conn.commit()
        token = serializer.dumps(email, salt='email-login')
        login_link = url_for('login_with_token', token=token, _external=True)
        # Send the login link via email using SMTP
        subject = "Your Magic Login Link"
        body = f"Click the link to log in: {login_link}"
        send_email(email, subject, body)

        print(f"Magic login link for {email}: {login_link}")
        flash("A login link has been sent to your email.", "info")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/login/<token>')
def login_with_token(token):
    try:
        email = serializer.loads(token, salt='email-login', max_age=300)
    except Exception:
        flash("The login link is invalid or has expired.", "danger")
        return redirect(url_for('login'))
    session['email'] = email
    flash("You have been logged in successfully!", "success")
    return redirect(url_for('select_quiz'))

@app.route('/select_quiz', methods=['GET'])
def select_quiz():
    conn = get_db()
    quizzes = conn.execute('SELECT * FROM quizzes').fetchall()
    return render_template('quiz_selection.html', quizzes=quizzes)

@app.route('/quiz/<int:quiz_id>', methods=['GET'])
def quiz(quiz_id):
    conn = get_db()
    questions = conn.execute('SELECT * FROM quiz_questions WHERE quiz_id = ?', (quiz_id,)).fetchall()
    return render_template('quiz.html', questions=questions, quiz_id=quiz_id)

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    if 'email' not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (session['email'],)).fetchone()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('select_quiz'))

    score = 0
    questions = conn.execute('SELECT * FROM quiz_questions WHERE quiz_id = ?', (quiz_id,)).fetchall()
    for question in questions:
        user_answer = request.form.get(f'question_{question["id"]}')
        if user_answer == question["correct_answer"]:
            score += 10

    conn.execute('INSERT INTO quiz_results (user_id, quiz_id, score) VALUES (?, ?, ?)', (user["id"], quiz_id, score))
    conn.commit()
    flash(f"Quiz completed! Your score: {score}/50", "success")
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (session['email'],)).fetchone()
    quiz_results = conn.execute('''
        SELECT quizzes.name, quiz_results.score, quiz_results.timestamp
        FROM quiz_results
        JOIN quizzes ON quiz_results.quiz_id = quizzes.id
        WHERE quiz_results.user_id = ?
    ''', (user['id'],)).fetchall()
    return render_template('dashboard.html', quiz_results=quiz_results)

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

@app.route('/backup', methods=['POST'])
def trigger_backup():
    """API endpoint to trigger a backup task."""
    backup_to_drive()
    return jsonify({'status': 'Backup task triggered successfully!'})

@app.route('/restore', methods=['POST'])
def trigger_restore():
    """API endpoint to trigger a restore task."""
    restore_from_drive()
    return jsonify({'status': 'Restore task triggered successfully!'})

# Configure logging for production
if not app.debug:  # Only configure logging if in production mode
    if "gunicorn" in logging.root.manager.loggerDict:
        gunicorn_error_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_error_logger.handlers
        app.logger.setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)
    app.logger.info("Application startup")

if __name__ == '__main__':
    app.run()

