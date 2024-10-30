import yaml
import os

QUIZZES_DIR = 'quizzes'

def load_quizzes(conn):
    cursor = conn.cursor()

    # Loop through each YAML file in the quizzes directory
    for filename in os.listdir(QUIZZES_DIR):
        if filename.endswith('.yml') or filename.endswith('.yaml'):
            filepath = os.path.join(QUIZZES_DIR, filename)
            with open(filepath, 'r') as f:
                quiz_data = yaml.safe_load(f)

            # Insert the quiz into the quizzes table if it doesn't already exist
            quiz_name = quiz_data['name']
            cursor.execute('SELECT id FROM quizzes WHERE name = ?', (quiz_name,))
            quiz_row = cursor.fetchone()

            if quiz_row:
                quiz_id = quiz_row['id']
            else:
                cursor.execute('INSERT INTO quizzes (name) VALUES (?)', (quiz_name,))
                quiz_id = cursor.lastrowid

            # Insert each question into the quiz_questions table
            for question in quiz_data['questions']:
                cursor.execute('''
                    INSERT INTO quiz_questions (quiz_id, question, option_a, option_b, option_c, option_d, correct_answer)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    quiz_id,
                    question['question'],
                    question['options'][0],
                    question['options'][1],
                    question['options'][2],
                    question['options'][3],
                    question['answer']
                ))

            print(f"Loaded quiz: {quiz_name} from {filename}")

    # Commit all changes to the database
    conn.commit()

# Define a migrate function that the main migration script will call
def migrate(conn):
    load_quizzes(conn)

