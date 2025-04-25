import re

def generate_quiz_id(name):
    """Generate a standardized ID from a quiz name."""
    # Convert to lowercase, remove special chars, replace spaces with underscores
    quiz_id = re.sub(r'[^a-zA-Z0-9 ]', '', name).lower().replace(' ', '_')
    return quiz_id

def migrate(conn):
    cursor = conn.cursor()
    
    # Get all quizzes without an ID
    cursor.execute('SELECT id, name FROM quizzes WHERE quiz_id IS NULL')
    quizzes = cursor.fetchall()
    
    # Update each quiz with a generated ID
    for quiz in quizzes:
        db_id = quiz['id']
        name = quiz['name']
        quiz_id = generate_quiz_id(name)
        
        cursor.execute('UPDATE quizzes SET quiz_id = ? WHERE id = ?', (quiz_id, db_id))
        print(f"Updated quiz '{name}' with ID: {quiz_id}")
    
    conn.commit()
    print(f"Updated {len(quizzes)} quizzes with generated IDs")