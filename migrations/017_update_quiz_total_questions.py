def migrate(conn):
    # Update each quiz with the count of its questions
    conn.execute('''
    UPDATE quizzes
    SET total_questions = (
        SELECT COUNT(*)
        FROM quiz_questions
        WHERE quiz_questions.quiz_id = quizzes.id
    )
    ''')
    conn.commit()
    print("Updated total_questions for all quizzes")