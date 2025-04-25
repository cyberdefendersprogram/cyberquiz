import os
import sqlite3

def migrate(conn):
    """Update class_name for existing quizzes based on directory structure."""
    cursor = conn.cursor()
    
    # Get all quizzes
    quizzes = cursor.execute('SELECT id, name, quiz_id FROM quizzes').fetchall()
    
    # Map of quiz_id to class_name
    quiz_class_map = {}
    
    # Scan through quiz directories to build the map
    quizzes_dir = 'quizzes'
    for class_dir in os.listdir(quizzes_dir):
        class_dir_path = os.path.join(quizzes_dir, class_dir)
        if not os.path.isdir(class_dir_path):
            continue
        
        # Extract class name from directory (e.g., "cis_53" -> "CIS 53")
        class_name = class_dir.replace('_', ' ').upper()
        
        # For each YAML file in this directory
        for filename in os.listdir(class_dir_path):
            if filename.endswith('.yml') or filename.endswith('.yaml'):
                # Extract quiz name from filename
                quiz_base_name = os.path.splitext(filename)[0]
                # Use this to match against quiz_id in the database
                for quiz in quizzes:
                    # Match either by direct name (filenames are often related to the quiz_id)
                    # or by looking for the quiz name in the file path
                    quiz_id = quiz['quiz_id']
                    if quiz_id and (quiz_id.lower() in quiz_base_name.lower() or
                                   quiz_base_name.lower() in quiz_id.lower()):
                        quiz_class_map[quiz['id']] = class_name
    
    # Update class_name for each quiz
    updated_count = 0
    for quiz_id, class_name in quiz_class_map.items():
        cursor.execute(
            'UPDATE quizzes SET class_name = ? WHERE id = ?',
            (class_name, quiz_id)
        )
        updated_count += 1
    
    conn.commit()
    print(f"Updated class_name for {updated_count} quizzes.")