import os
import sys

import pytest
import requests
from dotenv import load_dotenv

pytestmark = pytest.mark.network

load_dotenv()  # never overrides variables already set, e.g. CI secrets

TARGETS = {
    "INT": ("LINDAS_PASSWORD_INT", "ENDPOINT_INT"),
    "PROD": ("LINDAS_PASSWORD", "ENDPOINT"),
}

STATUS_MESSAGES = {
    200: "OK, endpoint reachable and credentials accepted",
    401: "credentials rejected (401), check user and password",
    403: "logged in, but no read access to the repository (403)",
    404: "repository not found (404), check the endpoint URL",
}


def probe(password_var: str, endpoint_var: str) -> tuple[int | None, str]:
    """Send ASK {} to the repository. Returns (status code or None, message)."""
    values = {
        "LINDAS_USER": os.getenv("LINDAS_USER"),
        password_var: os.getenv(password_var),
        endpoint_var: os.getenv(endpoint_var),
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        return None, f"missing {', '.join(missing)}"

    repo = values[endpoint_var].removesuffix("/rdf-graphs/service")

    try:
        r = requests.get(
            repo,
            params={"query": "ASK {}"},
            headers={"Accept": "application/sparql-results+json"},
            auth=(values["LINDAS_USER"], values[password_var]),
            timeout=15,
        )
    except requests.exceptions.RequestException as e:
        return None, f"cannot reach {repo} ({type(e).__name__})"

    return r.status_code, STATUS_MESSAGES.get(r.status_code, f"unexpected status {r.status_code}")


@pytest.mark.parametrize("password_var, endpoint_var", TARGETS.values(), ids=TARGETS.keys())
def test_lindas_endpoint(password_var, endpoint_var):
    status, message = probe(password_var, endpoint_var)
    assert status == 200, message


if __name__ == "__main__":
    ok = True
    for env, vars_ in TARGETS.items():
        status, message = probe(*vars_)
        print(f"{env}: {message}")
        ok = ok and status == 200
    sys.exit(0 if ok else 1)