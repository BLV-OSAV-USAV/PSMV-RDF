import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()  # never overrides variables already set, e.g. CI secrets

TARGETS = {
    "INT": ("LINDAS_PASSWORD_INT", "ENDPOINT_INT"),
    "PROD": ("LINDAS_PASSWORD", "ENDPOINT"),
}


def check(env: str, password_var: str, endpoint_var: str) -> bool:
    values = {
        "LINDAS_USER": os.getenv("LINDAS_USER"),
        password_var: os.getenv(password_var),
        endpoint_var: os.getenv(endpoint_var),
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        print(f"{env}: missing {', '.join(missing)}")
        return False

    user = values["LINDAS_USER"]
    password = values[password_var]
    repo = values[endpoint_var].removesuffix("/rdf-graphs/service")

    try:
        r = requests.get(
            repo,
            params={"query": "ASK {}"},
            headers={"Accept": "application/sparql-results+json"},
            auth=(user, password),
            timeout=15,
        )
    except requests.exceptions.RequestException as e:
        print(f"{env}: cannot reach {repo} ({type(e).__name__})")
        return False

    messages = {
        200: "OK, endpoint reachable and credentials accepted",
        401: "credentials rejected (401), check user and password",
        403: "logged in, but no read access to the repository (403)",
        404: "repository not found (404), check the endpoint URL",
    }
    print(f"{env}: {messages.get(r.status_code, f'unexpected status {r.status_code}')}")
    return r.status_code == 200


if __name__ == "__main__":
    results = [check(env, *vars_) for env, vars_ in TARGETS.items()]
    sys.exit(0 if all(results) else 1)