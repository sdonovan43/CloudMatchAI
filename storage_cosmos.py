import hashlib
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey

COSMOS_URL = "<your-cosmos-url>"
COSMOS_KEY = "<your-cosmos-key>"
DATABASE_NAME = "CloudMatchAI"
CONTAINER_NAME = "Jobs"

client = CosmosClient(COSMOS_URL, credential=COSMOS_KEY)

def init_db():
    db = client.create_database_if_not_exists(id=DATABASE_NAME)
    db.create_container_if_not_exists(
        id=CONTAINER_NAME,
        partition_key=PartitionKey(path="/company"),
        offer_throughput=400
    )


def hash_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def save_job(job):
    db = client.get_database_client(DATABASE_NAME)
    container = db.get_container_client(CONTAINER_NAME)

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


def get_top_jobs(limit=20):
    db = client.get_database_client(DATABASE_NAME)
    container = db.get_container_client(CONTAINER_NAME)

    query = f"""
        SELECT * FROM c
        ORDER BY c.score DESC
        OFFSET 0 LIMIT {limit}
    """

    return list(container.query_items(query=query, enable_cross_partition_query=True))
