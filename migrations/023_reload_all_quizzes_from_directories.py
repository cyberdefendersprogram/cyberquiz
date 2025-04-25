import yaml
import os
import re

QUIZZES_DIR = 'quizzes'

def generate_quiz_id(name):
    """Generate a standardized ID from a quiz name."""
    # Convert to lowercase, remove special chars, replace spaces with underscores
    quiz_id = re.sub(r'[^a-zA-Z0-9 ]', '', name).lower().replace(' ', '_')
    return quiz_id

def migrate(conn):
    """
    Load all quiz files from all directories in quizzes folder,
    properly setting class names and quiz IDs.
    This combines functionality from previous migrations to provide a unified update.
    """
    cursor = conn.cursor()
    processed_quizzes = 0
    updated_quizzes = 0
    
    print(f"Starting complete quiz reload from: {QUIZZES_DIR}")
    
    # Loop through each class directory
    for class_dir in os.listdir(QUIZZES_DIR):
        class_dir_path = os.path.join(QUIZZES_DIR, class_dir)
        if not os.path.isdir(class_dir_path):
            continue
            
        # Extract the class name from the directory name (e.g., "cis_60" -> "CIS 60")
        class_name = class_dir.replace('_', ' ').upper()
        print(f"Processing class directory: {class_dir} -> {class_name}")
        
        # Loop through each YAML file in the class directory
        for filename in os.listdir(class_dir_path):
            if not (filename.endswith('.yml') or filename.endswith('.yaml')):
                continue
                
            filepath = os.path.join(class_dir_path, filename)
            try:
                with open(filepath, 'r') as f:
                    quiz_data = yaml.safe_load(f)
                
                # Skip if no quiz data
                if not quiz_data:
                    print(f"Warning: Empty or invalid quiz file: {filepath}")
                    continue
                
                # Get quiz info from the YAML data
                quiz_name = quiz_data.get('name')
                if not quiz_name:
                    print(f"Warning: Quiz in {filepath} has no name, skipping")
                    continue
                
                # Generate or use existing quiz_id
                if 'id' not in quiz_data:
                    quiz_id = generate_quiz_id(quiz_name)
                    # Add the ID to the YAML data and save it back
                    quiz_data['id'] = quiz_id
                    with open(filepath, 'w') as f:
                        yaml.safe_dump(quiz_data, f)
                    print(f"Added ID {quiz_id} to {filepath}")
                else:
                    quiz_id = quiz_data['id']
                
                # Try to find an existing quiz by quiz_id first
                cursor.execute('SELECT id FROM quizzes WHERE quiz_id = ?', (quiz_id,))
                quiz_row = cursor.fetchone()
                
                # If no quiz with this ID, try by name (for backward compatibility)
                if not quiz_row:
                    cursor.execute('SELECT id FROM quizzes WHERE name = ?', (quiz_name,))
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
                    updated_quizzes += 1
                else:
                    # Insert a new quiz
                    cursor.execute('''
                        INSERT INTO quizzes (name, quiz_id, class_name) 
                        VALUES (?, ?, ?)
                    ''', (quiz_name, quiz_id, class_name))
                    db_id = cursor.lastrowid
                
                # Insert each question into the quiz_questions table
                if 'questions' in quiz_data and isinstance(quiz_data['questions'], list):
                    total_questions = 0
                    for question in quiz_data['questions']:
                        if not all(key in question for key in ['question', 'options', 'answer']):
                            print(f"Warning: Question in {filepath} is missing required fields, skipping")
                            continue
                            
                        # Ensure we have exactly 4 options
                        options = question['options']
                        if len(options) != 4:
                            print(f"Warning: Question in {filepath} has {len(options)} options instead of 4, skipping")
                            continue
                            
                        cursor.execute('''
                            INSERT INTO quiz_questions (quiz_id, question, option_a, option_b, option_c, option_d, correct_answer)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            db_id,
                            question['question'],
                            options[0],
                            options[1],
                            options[2],
                            options[3],
                            question['answer']
                        ))
                        total_questions += 1
                
                    # Update the total question count
                    cursor.execute('''
                        UPDATE quizzes SET total_questions = ? WHERE id = ?
                    ''', (total_questions, db_id))
                
                processed_quizzes += 1
                print(f"Loaded quiz: {quiz_name} (ID: {quiz_id}, Class: {class_name}) from {filepath}")
                
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
    
    # Commit all changes to the database
    conn.commit()
    print(f"Migration complete: Processed {processed_quizzes} quizzes ({updated_quizzes} updated, {processed_quizzes - updated_quizzes} newly added)")