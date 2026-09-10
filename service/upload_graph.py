import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env (only if running locally - not in CI)
if not os.getenv("CI"):
    load_dotenv()

# Serve both endpoints
TARGETS = {
    "int": {
        "file": "rdf/processed/graph.ttl",
        "password": "LINDAS_PASSWORD_INT",
        "graph": "GRAPH_INT",
        "endpoint": "ENDPOINT_INT",
    },
    "prod": {
        "file": "rdf/processed/graph.ttl",
        "password": "LINDAS_PASSWORD",
        "graph": "GRAPH",
        "endpoint": "ENDPOINT",
    },
}


def require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.exit(f"Error: missing environment variable {name}")
    return value


def upload(env: str) -> None:
    cfg = TARGETS[env]
    user = require("LINDAS_USER")
    password = require(cfg["password"])
    graph = require(cfg["graph"])
    endpoint = require(cfg["endpoint"])
    path = Path(cfg["file"])

    if not path.is_file():
        sys.exit(f"Error: file not found: {path}")

    size_mb = path.stat().st_size / 1e6
    print(f"Uploading {path} ({size_mb:.1f} MB) to {env.upper()} graph <{graph}>")

    try:
        with path.open("rb") as f:
            response = requests.put(
                endpoint,
                auth=(user, password),
                params={"graph": graph},
                headers={"Content-Type": "text/turtle"},
                data=f,
                timeout=(10, 900), 
            )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        sys.exit(f"HTTP error {e.response.status_code}: {e.response.text[:1000]}")
    except requests.exceptions.RequestException as e:
        sys.exit(f"Request failed: {e}")

    print(f"Uploaded, status {response.status_code}")


if __name__ == "__main__":
    choices = [*TARGETS, "all"]
    env = sys.argv[1] if len(sys.argv) > 1 else "int"
    if env not in choices:
        sys.exit(f"Usage: {sys.argv[0]} [{'|'.join(choices)}]")

    for target in (TARGETS if env == "all" else [env]):
        upload(target)