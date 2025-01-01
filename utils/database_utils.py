import sqlite3

def create_database():
    """Create SQLite database to store user progress."""
    conn = sqlite3.connect("user_progress.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            feedback TEXT,
            score INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_progress(question, answer, feedback, score):
    """Save progress to the database."""
    conn = sqlite3.connect("user_progress.db")
    cursor = conn.cursor()
    cursor.execute("""
    
        INSERT INTO progress (question, answer, feedback, score) VALUES (?, ?, ?, ?)
    """, (question, answer, feedback, score))
    conn.commit()
    conn.close()

def get_progress():
    """Retrieve all progress records."""
    conn = sqlite3.connect("user_progress.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM progress")
    rows = cursor.fetchall()
    conn.close()
    return rows
