import yaml
import os
import re

QUIZZES_DIR = 'quizzes'

def generate_quiz_id(name):
    """Generate a standardized ID from a quiz name."""
    # Convert to lowercase, remove special chars, replace spaces with underscores
    quiz_id = re.sub(r'[^a-zA-Z0-9 ]', '', name).lower().replace(' ', '_')
    return quiz_id

def load_quizzes(conn):
    cursor = conn.cursor()

    # Loop through each class directory
    for class_dir in os.listdir(QUIZZES_DIR):
        class_dir_path = os.path.join(QUIZZES_DIR, class_dir)
        if not os.path.isdir(class_dir_path):
            continue
            
        # Extract the class number from the directory name (e.g., "cis_53" -> "CIS 53")
        class_number = class_dir.replace('_', ' ').upper()
        
        # Loop through each YAML file in the class directory
        for filename in os.listdir(class_dir_path):
            if filename.endswith('.yml') or filename.endswith('.yaml'):
                filepath = os.path.join(class_dir_path, filename)
                with open(filepath, 'r') as f:
                    quiz_data = yaml.safe_load(f)

                # Get quiz info from the YAML data
                quiz_name = quiz_data['name']
                
                # Generate quiz_id if not present in the YAML
                if 'id' not in quiz_data:
                    quiz_id = generate_quiz_id(quiz_name)
                    # Add the ID to the YAML data and save it back
                    quiz_data['id'] = quiz_id
                    with open(filepath, 'w') as f:
                        yaml.safe_dump(quiz_data, f)
                else:
                    quiz_id = quiz_data['id']
                
                # Use the class number derived from directory structure
                class_name = class_number
                
                # Try to find an existing quiz by quiz_id first
                cursor.execute('SELECT id FROM quizzes WHERE quiz_id = ?', (quiz_id,))
                quiz_row = cursor.fetchone()
                
                # If no quiz with this ID, try by name (for backward compatibility)
                if not quiz_row:
                    cursor.execute('SELECT id FROM quizzes WHERE name = ? AND quiz_id IS NULL', (quiz_name,))
                    quiz_row = cursor.fetchone()

                if quiz_row:
                    db_id = quiz_row['id']
                    # Update existing quiz with the latest details
                    cursor.execute('''
                        UPDATE quizzes 
                        SET name = ?, quiz_id = ?, class_name = ? 
                        WHERE id = ?
                    ''', (quiz_name, quiz_id, class_name, db_id))
                    
                    # Delete existing questions for this quiz to be replaced with the latest ones
                    cursor.execute('DELETE FROM quiz_questions WHERE quiz_id = ?', (db_id,))
                else:
                    # Insert a new quiz
                    cursor.execute('''
                        INSERT INTO quizzes (name, quiz_id, class_name) 
                        VALUES (?, ?, ?)
                    ''', (quiz_name, quiz_id, class_name))
                    db_id = cursor.lastrowid

                # Insert each question into the quiz_questions table
                for question in quiz_data['questions']:
                    cursor.execute('''
                        INSERT INTO quiz_questions (quiz_id, question, option_a, option_b, option_c, option_d, correct_answer)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        db_id,
                        question['question'],
                        question['options'][0],
                        question['options'][1],
                        question['options'][2],
                        question['options'][3],
                        question['answer']
                    ))

                # Update the total question count
                cursor.execute('''
                    UPDATE quizzes
                    SET total_questions = (
                        SELECT COUNT(*)
                        FROM quiz_questions
                        WHERE quiz_questions.quiz_id = ?
                    )
                    WHERE id = ?
                ''', (db_id, db_id))

                print(f"Loaded quiz: {quiz_name} (ID: {quiz_id}, Class: {class_name}) from {filepath}")

    # Commit all changes to the database
    conn.commit()

# Define a migrate function that the main migration script will call
def migrate(conn):
    load_quizzes(conn)