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
def admin():
    if 'email' not in session or session['email'] != 'vaibhavb@gmail.com':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('index'))

    conn = get_db()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tables = [table['name'] for table in tables]

    db_data = {}
    # Whitelist allowed table names to prevent SQL injection
    allowed_tables = {'users', 'quizzes', 'quiz_questions', 'quiz_results', 'schema_version'}
    for table in tables:
        table_name = table['name']
        if table_name in allowed_tables:
            # Use parameterized query with identifier quoting for table names
            query = f"SELECT * FROM '{table_name}'"
            data = conn.execute(query).fetchall()
            db_data[table_name] = [dict(row) for row in data]

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
    # Fetch all quizzes and organize them by class
    quizzes = conn.execute('SELECT * FROM quizzes ORDER BY class_name, name').fetchall()
    
    # Group quizzes by class name
    classes = {}
    for quiz in quizzes:
        class_name = quiz['class_name'] or 'Other'
        if class_name not in classes:
            classes[class_name] = []
        classes[class_name].append(quiz)
    
    return render_template('quiz_selection.html', classes=classes)

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
    num_questions = len(questions)
    for question in questions:
        user_answer = request.form.get(f'question_{question["id"]}')
        if user_answer == question["correct_answer"]:
            score += 10

    conn.execute('INSERT INTO quiz_results (user_id, quiz_id, score) VALUES (?, ?, ?)', (user["id"], quiz_id, score))
    conn.commit()
    flash(f"Quiz completed! Your score: {score}/{num_questions * 10}", "success")
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (session['email'],)).fetchone()
    quiz_results = conn.execute('''
        SELECT quizzes.name, quiz_results.score, quiz_results.timestamp, 
               quizzes.total_questions, quizzes.class_name
        FROM quiz_results
        JOIN quizzes ON quiz_results.quiz_id = quizzes.id
        WHERE quiz_results.user_id = ?
        ORDER BY quiz_results.timestamp DESC
    ''', (user['id'],)).fetchall()
    
    # Group results by class
    classes = {}
    for result in quiz_results:
        class_name = result['class_name'] or 'Other'
        if class_name not in classes:
            classes[class_name] = []
        classes[class_name].append(result)
    
    return render_template('dashboard.html', quiz_results=quiz_results, classes=classes)

@app.route('/update_account', methods=['GET', 'POST'])
def update_account():
    if 'email' not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for('login'))

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (session['email'],)).fetchone()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('select_quiz'))

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        if student_id:
            try:
                conn.execute('UPDATE users SET student_id = ? WHERE id = ?', (student_id, user['id']))
                conn.commit()
                flash("Account updated successfully!", "success")
            except Exception as e:
                flash(f"Error updating account: {e}", "danger")
        else:
            flash("Student ID is required.", "warning")

    return render_template('update_account.html', user=user)

@app.context_processor
def inject_user():
    is_admin = session.get('email') == 'vaibhavb@gmail.com' if 'email' in session else False
    # Fetch the current user from the database if logged in
    current_user = None
    if 'email' in session:
        conn = get_db()
        current_user = conn.execute('SELECT * FROM users WHERE email = ?', (session['email'],)).fetchone()
    return dict(is_admin=is_admin, current_user=current_user)

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
    try:
        if 'email' not in session or session['email'] != 'vaibhavb@gmail.com':
            return jsonify({'error': 'Unauthorized access'}), 403
            
        backup_to_drive()
        return jsonify({'status': 'Backup completed successfully!'})
    except Exception as e:
        app.logger.error(f"Backup failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/restore', methods=['POST'])
def trigger_restore():
    """API endpoint to trigger a restore task."""
    try:
        if 'email' not in session or session['email'] != 'vaibhavb@gmail.com':
            return jsonify({'error': 'Unauthorized access'}), 403
            
        file_id = request.json.get('fileId')
        if not file_id:
            return jsonify({'error': 'File ID is required'}), 400
            
        restore_from_drive(file_id)
        return jsonify({'status': 'Restore completed successfully!'})
    except Exception as e:
        app.logger.error(f"Restore failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_custom_query(query):
    """Execute a custom SQL query safely."""
    try:
        conn = get_db()
        # Only allow SELECT queries for safety
        query_stripped = query.lower().strip()
        if not query_stripped.startswith('select'):
            raise ValueError("Only SELECT queries are allowed")
            
        # Additional validation to prevent dangerous operations
        dangerous_keywords = ['drop', 'delete', 'update', 'insert', 'alter', 'create', 'pragma']
        if any(keyword in query_stripped for keyword in dangerous_keywords):
            raise ValueError("Query contains potentially dangerous keywords")
            
        # Limit query length to prevent abuse
        if len(query) > 1000:
            raise ValueError("Query too long")
            
        results = conn.execute(query).fetchall()
        # Convert results to list of dicts
        columns = list(results[0].keys()) if results else []
        data = [dict(row) for row in results]
        return {"columns": columns, "data": data}
        
    except Exception as e:
        app.logger.error(f"Query execution failed: {str(e)}")
        raise
    
@app.route('/execute_query', methods=['POST'])
def execute_query():
    """API endpoint to execute custom SQL queries."""
    try:
        if 'email' not in session or session['email'] != 'vaibhavb@gmail.com':
            return jsonify({'error': 'Unauthorized access'}), 403
            
        query = request.json.get('query')
        if not query:
            return jsonify({'error': 'Query is required'}), 400
            
        results = run_custom_query(query)
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Query execution failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


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

