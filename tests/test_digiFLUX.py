"""Smoke test for the digiFLUX export queries against LINDAS.

The queries in src/sparql/queries/digiFLUX/queries/ feed the digiFLUX product
catalogue. Each .rq file is picked up automatically, so a new query is tested
without touching this file. To keep the test fast, the final ORDER BY is
dropped and LIMIT 100 is appended. Checked per query:

- LINDAS accepts and runs it,
- it returns at least one row,
- the key is filled and unique within the sample: `id` for entity tables,
  the first two columns for relationship tables (see the digiFLUX README).
"""

import re
from collections import Counter
from pathlib import Path

import pytest
import requests

pytestmark = pytest.mark.network

ENDPOINT = "https://lindas.admin.ch/query"
LIMIT = 100
TIMEOUT = 60

QUERY_DIR = Path(__file__).resolve().parents[1] / "src" / "sparql" / "queries" / "digiFLUX" / "queries"
QUERIES = sorted(QUERY_DIR.glob("*.rq"))


def limited(query: str) -> str:
    """Drop a trailing ORDER BY / LIMIT and append LIMIT 100."""
    query = re.sub(r"\s*(ORDER\s+BY[^}]*?)?\s*(LIMIT\s+\d+)?\s*$", "", query, flags=re.IGNORECASE)
    return f"{query}\nLIMIT {LIMIT}\n"


def run(query: str) -> tuple[list[str], list[dict]]:
    r = requests.post(
        ENDPOINT,
        data=query.encode("utf-8"),
        headers={
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    result = r.json()
    return result["head"]["vars"], result["results"]["bindings"]


def key_columns(variables: list[str]) -> list[str]:
    """`id` for entity tables, otherwise the first two columns."""
    return ["id"] if "id" in variables else variables[:2]


def test_queries_found():
    assert QUERIES, f"no .rq files in {QUERY_DIR}"


@pytest.mark.parametrize("path", QUERIES, ids=[p.stem for p in QUERIES])
def test_digiflux_query(path):
    variables, rows = run(limited(path.read_text(encoding="utf-8")))

    assert rows, "query returned no rows"

    keys = key_columns(variables)
    missing = [r for r in rows if any(k not in r for k in keys)]
    assert not missing, f"{len(missing)} row(s) without {keys}, first: {missing[:3]}"

    counts = Counter(tuple(r[k]["value"] for k in keys) for r in rows)
    duplicates = [k for k, n in counts.items() if n > 1]
    assert not duplicates, f"{len(duplicates)} duplicate {keys} in sample, first: {duplicates[:5]}"