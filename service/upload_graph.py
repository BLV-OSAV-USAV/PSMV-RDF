import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env (only if running locally - not in CI)
if not os.getenv("CI"):
    load_dotenv()

USER = os.getenv("LINDAS_USER")
PASSWORD = os.getenv("LINDAS_PASSWORD")
ENDPOINT = os.getenv("ENDPOINT")
GRAPH = os.getenv("GRAPH")

if not all([USER, PASSWORD, ENDPOINT, GRAPH]):
    print("Error: Missing required environment variables.")
    sys.exit(1)

auth = (USER, PASSWORD)
params = {"graph": GRAPH}

print("Uploading graph.ttl to LINDAS...")
try:
    with open("rdf/processed/graph.ttl", "rb") as f:
        response = requests.put(
            ENDPOINT,
            auth=auth,
            params=params,
            headers={"Content-Type": "text/turtle"},
            data=f,
        )
    response.raise_for_status()
    print(f"✅ Uploaded — {response.status_code}")
except FileNotFoundError:
    print("❌ File not found: rdf/processed/graph.ttl")
    sys.exit(1)
except requests.exceptions.HTTPError as e:
    print(f"❌ HTTP error: {e.response.status_code} — {e.response.text}")
    sys.exit(1)