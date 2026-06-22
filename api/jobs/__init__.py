import json
import os
import azure.functions as func
from azure.cosmos import CosmosClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        client    = CosmosClient(os.environ["COSMOS_ENDPOINT"], os.environ["COSMOS_KEY"])
        container = (client
                     .get_database_client(os.environ.get("COSMOS_DB", "cloudmatchai"))
                     .get_container_client(os.environ.get("COSMOS_CONTAINER", "jobs")))

        q = ("SELECT c.title, c.company, c.location, c.url, "
             "c.score, c.description, c.scraped_at FROM c")
        jobs = list(container.query_items(query=q, enable_cross_partition_query=True))
        jobs.sort(key=lambda j: j.get("score", 0), reverse=True)

        return func.HttpResponse(
            json.dumps(jobs),
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
