import os
import yaml

QUIZZES_DIR = 'quizzes'

def migrate(conn):
    """Update class_name for quizzes based on the current directory structure."""
    cursor = conn.cursor()
    
    # Get all quizzes from the database
    quizzes = cursor.execute('SELECT id, name, quiz_id FROM quizzes').fetchall()
    
    # Create a mapping of quiz ID/name to their files and classes
    quiz_class_map = {}
    
    # Scan through the quiz directories
    print(f"Scanning directory: {QUIZZES_DIR}")
    for class_dir in os.listdir(QUIZZES_DIR):
        class_dir_path = os.path.join(QUIZZES_DIR, class_dir)
        if not os.path.isdir(class_dir_path):
            continue
            
        # Extract class name from directory (e.g., "cis_53" -> "CIS 53")
        class_name = class_dir.replace('_', ' ').upper()
        print(f"Processing class directory: {class_dir} -> {class_name}")
        
        # Process each YAML file in this class directory
        for filename in os.listdir(class_dir_path):
            if filename.endswith('.yml') or filename.endswith('.yaml'):
                filepath = os.path.join(class_dir_path, filename)
                try:
                    with open(filepath, 'r') as f:
                        quiz_data = yaml.safe_load(f)
                        
                    # Get quiz info from the YAML data
                    quiz_name = quiz_data.get('name')
                    quiz_id = quiz_data.get('id')
                    
                    if quiz_name:
                        print(f"Found quiz: '{quiz_name}' in {filepath}")
                        # Attempt to find matching quiz in database by name and id
                        for quiz in quizzes:
                            db_name = quiz['name']
                            db_id = quiz['id']
                            db_quiz_id = quiz['quiz_id']
                            
                            # Match by name or quiz_id
                            if (quiz_name == db_name) or (quiz_id and quiz_id == db_quiz_id):
                                quiz_class_map[db_id] = class_name
                                print(f"Matched quiz ID {db_id}: '{db_name}' to class {class_name}")
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    # Update class_name for each matched quiz
    updated_count = 0
    for db_id, class_name in quiz_class_map.items():
        cursor.execute(
            'UPDATE quizzes SET class_name = ? WHERE id = ?',
            (class_name, db_id)
        )
        updated_count += 1
    
    conn.commit()
    print(f"Updated class_name for {updated_count} quizzes.")