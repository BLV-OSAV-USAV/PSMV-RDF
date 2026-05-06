import os
import sys
import requests
from dotenv import load_dotenv

# Load .env only if running locally (not in CI)
if not os.getenv("CI"):
    load_dotenv()

USER = os.getenv("LINDAS_USER")
PASSWORD = os.getenv("LINDAS_PASSWORD")
ENDPOINT = os.getenv("ENDPOINT")
GRAPH = os.getenv("GRAPH")

if not all([USER, PASSWORD, ENDPOINT, GRAPH]):
    print("❌ Missing required environment variables.")
    sys.exit(1)

print(f"Testing connection to: {ENDPOINT}")
print(f"Graph: {GRAPH}")
print(f"USER: {USER}")
print(f"PASSWORD: {PASSWORD[:2]}***" if PASSWORD else "PASSWORD: None")

response = requests.get(
    ENDPOINT,
    auth=(USER, PASSWORD),
    params={"graph": GRAPH},
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✅ Graph exists and is accessible")
elif response.status_code == 404:
    print("⚠️  Graph not found (404) — it may not exist yet or the URL is wrong")
elif response.status_code == 401:
    print("❌ Unauthorized (401) — check your USER and PASSWORD")
elif response.status_code == 403:
    print("❌ Forbidden (403) — your user lacks permission on this graph")
else:
    print(f"❌ Unexpected status: {response.status_code}")
    print(response.text)