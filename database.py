import os
import sqlite3
import json
from datetime import datetime

DB_FILE = "defiant_roots.db"

def get_db_connection():
    """Establishes and returns a sqlite3 database connection with Row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database tables and populates seed data if empty."""
    # Establish connection with SQLite.
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table: Holds permanent user credentials, contact preferences, and phone numbers.
    # Enables selecting between Email and SMS nudges.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        contact_preference TEXT DEFAULT 'Email',
        phone TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Migration: Dynamically add 'contact_preference' column if not present in older databases
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN contact_preference TEXT DEFAULT 'Email'")
        conn.commit()
    except sqlite3.OperationalError:
        # Avoid error if column already exists (SQLite lacks ALTER TABLE ADD COLUMN IF NOT EXISTS)
        pass

    # Migration: Dynamically add 'phone' column if not present in older databases
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # 2. Experiments Table: Tracks user's active crop engineering journeys.
    # Records target crop, location, the climate conflict, adaptation blueprint hacks, and startup tips.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        plant_name TEXT NOT NULL,
        location TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active',
        current_week INTEGER DEFAULT 1,
        conflict TEXT NOT NULL,
        blueprint TEXT NOT NULL,
        youbuddy_insights TEXT,
        startup_phase TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """)

    # Migration: Add crowd-sourced insights and start-up phase details to experiments
    try:
        cursor.execute("ALTER TABLE experiments ADD COLUMN youbuddy_insights TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE experiments ADD COLUMN startup_phase TEXT")
    except sqlite3.OperationalError:
        pass

    # 3. Adaptation Searches Table: Caches historical query outcomes to avoid redundant LLM calls.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adaptation_searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        plant_name TEXT NOT NULL,
        location TEXT NOT NULL,
        conflict TEXT NOT NULL,
        blueprint TEXT NOT NULL,
        youbuddy_insights TEXT,
        startup_phase TEXT
    )
    """)

    # Migration: Add crowd-sourced insights and start-up phase details to searches
    try:
        cursor.execute("ALTER TABLE adaptation_searches ADD COLUMN youbuddy_insights TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE adaptation_searches ADD COLUMN startup_phase TEXT")
    except sqlite3.OperationalError:
        pass
    
    # 4. Community Logs Table: Feeds the "Plant Gossip" grapevine section.
    # Displays grower status (Adapting, Experimenting, Thriving) and latest environmental hacks.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        grower_name TEXT NOT NULL,
        plant_name TEXT NOT NULL,
        location TEXT NOT NULL,
        status TEXT NOT NULL,
        latest_hack TEXT NOT NULL
    )
    """)
    
    # Migration: Add optional question field to logs to let community troubleshoot issues together
    try:
        cursor.execute("ALTER TABLE community_logs ADD COLUMN question TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    # 5. Comments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_id INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        commenter_name TEXT NOT NULL,
        comment_text TEXT NOT NULL,
        FOREIGN KEY (log_id) REFERENCES community_logs(id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    
    # Seed Mock Community Logs if empty
    cursor.execute("SELECT COUNT(*) FROM community_logs")
    if cursor.fetchone()[0] == 0:
        logs = [
            ("Rosalyn V.", "Mango", "Washington, UT", "Adapting", "South-facing thermal wall protection"),
            ("Alex D.", "Avocado", "Chicago, IL", "Experimenting", "Clustered humidity microclimate"),
            ("Jordan P.", "Fig Tree", "Boston, MA", "Thriving", "Frost-cloth wrapping during winter")
        ]
        cursor.executemany("""
        INSERT INTO community_logs (grower_name, plant_name, location, status, latest_hack)
        VALUES (?, ?, ?, ?, ?)
        """, logs)
        conn.commit()
        
        # Seed comments for the first log
        cursor.execute("SELECT id FROM community_logs WHERE grower_name = 'Rosalyn V.'")
        rosalyn_log_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM community_logs WHERE grower_name = 'Alex D.'")
        alex_log_id = cursor.fetchone()[0]
        
        comments = [
            (rosalyn_log_id, "Alex D.", "How is it holding up in winter? Are you using mulch as well?"),
            (rosalyn_log_id, "Jordan P.", "South-facing walls are absolute lifesavers! Burlap wrapping helps too if winds pick up."),
            (alex_log_id, "Rosalyn V.", "Avocados love that clustered setup, it really helps with the dry indoor heating!")
        ]
        
        cursor.executemany("""
        INSERT INTO comments (log_id, commenter_name, comment_text)
        VALUES (?, ?, ?)
        """, comments)
        conn.commit()
        
    # 6. Weekly Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weekly_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_id INTEGER NOT NULL,
        week_number INTEGER NOT NULL,
        weather_context TEXT,
        nudge_message TEXT,
        user_feedback TEXT,
        action_plan TEXT,
        image_path TEXT,
        image_blob BLOB,
        delivery_log TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
    )
    """)

    # Ensure image_path column exists in weekly_logs (migration)
    try:
        cursor.execute("ALTER TABLE weekly_logs ADD COLUMN image_path TEXT")
    except sqlite3.OperationalError:
        pass

    # Ensure image_blob column exists in weekly_logs (migration)
    try:
        cursor.execute("ALTER TABLE weekly_logs ADD COLUMN image_blob BLOB")
    except sqlite3.OperationalError:
        pass

    # Ensure delivery_log column exists in weekly_logs (migration)
    try:
        cursor.execute("ALTER TABLE weekly_logs ADD COLUMN delivery_log TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def save_adaptation_search(plant_name: str, location: str, conflict: str, blueprint: list, youbuddy_insights: str = "", startup_phase: str = ""):
    """Saves a search query and adaptation blueprint results into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO adaptation_searches (plant_name, location, conflict, blueprint, youbuddy_insights, startup_phase)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (plant_name, location, conflict, json.dumps(blueprint), youbuddy_insights, startup_phase))
    conn.commit()
    conn.close()

def get_adaptation_searches():
    """Retrieves all past searches from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM adaptation_searches ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_community_log(grower_name: str, plant_name: str, location: str, status: str, latest_hack: str, question: str = None):
    """Inserts a new growing log into the community board."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO community_logs (grower_name, plant_name, location, status, latest_hack, question)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (grower_name, plant_name, location, status, latest_hack, question))
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id

def get_community_logs():
    """Retrieves all community growing logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM community_logs ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_comment(log_id: int, commenter_name: str, comment_text: str):
    """Adds a new comment under a specific community log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO comments (log_id, commenter_name, comment_text)
    VALUES (?, ?, ?)
    """, (log_id, commenter_name, comment_text))
    conn.commit()
    conn.close()

def get_comments(log_id: int):
    """Retrieves all comments associated with a specific community log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM comments WHERE log_id = ? ORDER BY timestamp ASC", (log_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
def get_or_create_user(user_id: str, email: str, name: str):
    """Checks if a user exists by user_id; if not, creates a user record and returns the user object."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("""
        INSERT INTO users (user_id, email, name)
        VALUES (?, ?, ?)
        """, (user_id, email, name))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    conn.close()
    return user

def create_experiment(user_id: str, plant_name: str, location: str, conflict: str, blueprint: list, youbuddy_insights: str = "", startup_phase: str = ""):
    """Creates a new growing experiment linked to a user_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO experiments (user_id, plant_name, location, status, current_week, conflict, blueprint, youbuddy_insights, startup_phase)
    VALUES (?, ?, ?, 'Active', 1, ?, ?, ?, ?)
    """, (user_id, plant_name, location, conflict, json.dumps(blueprint), youbuddy_insights, startup_phase))
    conn.commit()
    exp_id = cursor.lastrowid
    conn.close()
    return exp_id

def get_user_experiments(user_id: str):
    """Retrieves all experiments associated with a specific user_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_experiment_week(experiment_id: int, new_week: int):
    """Updates the current week/state of an experiment."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE experiments 
    SET current_week = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (new_week, experiment_id))
    conn.commit()
    conn.close()

def update_user_preference(user_id: str, preference: str, phone: str = None):
    """Updates contact preference (Email/SMS) and phone number for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users 
    SET contact_preference = ?, phone = ?
    WHERE user_id = ?
    """, (preference, phone, user_id))
    conn.commit()
    conn.close()

def get_all_active_experiments():
    """Retrieves all active experiments across all users for loop worker."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT e.*, u.contact_preference, u.email as user_email, u.name as user_name, u.phone as user_phone 
    FROM experiments e
    JOIN users u ON e.user_id = u.user_id
    WHERE e.status = 'Active'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_active_experiment_by_id(exp_id: int):
    """Retrieves a single active experiment by its ID for targeted loop worker run."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT e.*, u.contact_preference, u.email as user_email, u.name as user_name, u.phone as user_phone 
    FROM experiments e
    JOIN users u ON e.user_id = u.user_id
    WHERE e.id = ? AND e.status = 'Active'
    """, (exp_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_weekly_logs(experiment_id: int):
    """Retrieves all weekly logs for an experiment."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM weekly_logs 
    WHERE experiment_id = ? 
    ORDER BY week_number ASC
    """, (experiment_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_latest_weekly_log(experiment_id: int):
    """Retrieves the latest weekly log for an experiment."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM weekly_logs 
    WHERE experiment_id = ? 
    ORDER BY week_number DESC LIMIT 1
    """, (experiment_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_weekly_nudge(experiment_id: int, week_number: int, weather_context: str, nudge_message: str, delivery_log: str = None):
    """Creates or updates a weekly nudge log entry, including simulated delivery status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if entry already exists
    cursor.execute("""
    SELECT id FROM weekly_logs 
    WHERE experiment_id = ? AND week_number = ?
    """, (experiment_id, week_number))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("""
        UPDATE weekly_logs 
        SET weather_context = ?, nudge_message = ?, delivery_log = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (weather_context, nudge_message, delivery_log, row["id"]))
    else:
        cursor.execute("""
        INSERT INTO weekly_logs (experiment_id, week_number, weather_context, nudge_message, delivery_log)
        VALUES (?, ?, ?, ?, ?)
        """, (experiment_id, week_number, weather_context, nudge_message, delivery_log))
        
    conn.commit()
    conn.close()

def add_weekly_feedback(experiment_id: int, week_number: int, user_feedback: str, action_plan: str, image_path: str = None, image_blob: bytes = None):
    """Saves user feedback, image path, image BLOB, and dynamical action plan for a week, and increments current_week."""
    # Size validation on the image BLOB field before any insert (enforce 5MB limit for safety and storage sanity)
    if image_blob is not None and len(image_blob) > 5 * 1024 * 1024:
        raise ValueError("Image BLOB exceeds 5MB size limit.")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if entry already exists (allows updating the same week before moving to next week)
    cursor.execute("""
    SELECT id FROM weekly_logs 
    WHERE experiment_id = ? AND week_number = ?
    """, (experiment_id, week_number))
    row = cursor.fetchone()
    
    # All statements use parameterized SQL parameters (?) to prevent SQL injection vulnerabilities
    if row:
        cursor.execute("""
        UPDATE weekly_logs 
        SET user_feedback = ?, action_plan = ?, image_path = ?, image_blob = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (user_feedback, action_plan, image_path, sqlite3.Binary(image_blob) if image_blob else None, row["id"]))
    else:
        cursor.execute("""
        INSERT INTO weekly_logs (experiment_id, week_number, user_feedback, action_plan, image_path, image_blob)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (experiment_id, week_number, user_feedback, action_plan, image_path, sqlite3.Binary(image_blob) if image_blob else None))
        
    # Increment the experiment week counter to unlock the next weekly check-in cycle
    cursor.execute("""
    UPDATE experiments 
    SET current_week = ? + 1, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (week_number, experiment_id))
    
    conn.commit()
    conn.close()

def get_user_posts_today(grower_name: str) -> int:
    """Returns the count of community logs posted by grower_name today (local time)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT COUNT(*) FROM community_logs 
    WHERE grower_name = ? AND date(timestamp, 'localtime') = date('now', 'localtime')
    """, (grower_name,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

if __name__ == "__main__":
    init_db()
    print("Database successfully initialized.")
