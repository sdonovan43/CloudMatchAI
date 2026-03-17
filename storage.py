import os
import hashlib
import sqlite3
from datetime import datetime

try:
    from azure.cosmos import CosmosClient, PartitionKey
    COSMOS_AVAILABLE = True
except ImportError:
    COSMOS_AVAILABLE = False

BACKEND = os.getenv("STORAGE_BACKEND", "sqlite").lower()

DB_FILE = "jobs.db"

COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB = "CloudMatchAI"
COSMOS_CONTAINER = "Jobs"


def hash_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


# ---------------------------------------------------------
# SQLITE
# ---------------------------------------------------------

def sqlite_init():
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


def sqlite_save(job):
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


def sqlite_get_top(limit=20):
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


# ---------------------------------------------------------
# COSMOS
# ---------------------------------------------------------

def cosmos_init():
    if not COSMOS_AVAILABLE:
        raise RuntimeError("Cosmos DB SDK not installed")

    client = CosmosClient(COSMOS_URL, credential=COSMOS_KEY)
    db = client.create_database_if_not_exists(id=COSMOS_DB)

    db.create_container_if_not_exists(
        id=COSMOS_CONTAINER,
        partition_key=PartitionKey(path="/company"),
        offer_throughput=400
    )


def cosmos_save(job):
    client = CosmosClient(COSMOS_URL, credential=COSMOS_KEY)
    db = client.get_database_client(COSMOS_DB)
    container = db.get_container_client(COSMOS_CONTAINER)

    item = {
        "id": hash_id(job["url"]),
        "title": job["title"],
        "company": job["company"],
        "location": job["location"],
        "url": job["url"],
        "score": job["score"],
        "description": job["description"],
        "scraped_at": datetime.utcnow().isoformat()
    }

    container.upsert_item(item)


def cosmos_get_top(limit=20):
    client = CosmosClient(COSMOS_URL, credential=COSMOS_KEY)
    db = client.get_database_client(COSMOS_DB)
    container = db.get_container_client(COSMOS_CONTAINER)

    query = f"""
        SELECT * FROM c
        ORDER BY c.score DESC
        OFFSET 0 LIMIT {limit}
    """

    return list(container.query_items(query=query, enable_cross_partition_query=True))


# ---------------------------------------------------------
# UNIFIED INTERFACE
# ---------------------------------------------------------

def init_storage():
    if BACKEND == "cosmos":
        cosmos_init()
    else:
        sqlite_init()


def save_job(job):
    if BACKEND == "cosmos":
        cosmos_save(job)
    else:
        sqlite_save(job)


def get_top_jobs(limit=20):
    if BACKEND == "cosmos":
        return cosmos_get_top(limit)
    return sqlite_get_top(limit)
