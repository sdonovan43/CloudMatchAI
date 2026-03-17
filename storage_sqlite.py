import sqlite3
from datetime import datetime

DB_FILE = "jobs.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT UNIQUE,
            score INTEGER,
            description TEXT,
            scraped_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_job(job):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO jobs (title, company, location, url, score, description, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        job["title"],
        job["company"],
        job["location"],
        job["url"],
        job["score"],
        job["description"],
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def get_top_jobs(limit=20):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        SELECT title, company, location, url, score, scraped_at
        FROM jobs
        ORDER BY score DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows
