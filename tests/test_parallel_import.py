"""Checks the parallel import rules on the generated graph.

Parallel imports take over only the active substances and the SP-coded
plant protection statements of their reference product. Co-formulants and
GHS hazard labelling (hazard statements, pictograms, signal words) are not
inherited, as the labelling of the foreign original label applies.
"""

import sys
from pathlib import Path

import pytest
from rdflib import Graph

pytestmark = pytest.mark.graph

GRAPH_PATH = Path(__file__).resolve().parents[1] / "rdf" / "processed" / "graph.ttl"

PREFIXES = """
PREFIX : <https://agriculture.ld.admin.ch/plant-protection/>
PREFIX schema: <http://schema.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
"""

# id: (count query, expectation); expectation is an exact int or ">0"
CHECKS = {
    # Parallel imports: must be gone
    "pi_no_coformulants": ("""
        SELECT (COUNT(*) AS ?n) WHERE {
          ?p a :ParallelImport ; :ingredient/:substance ?s .
          ?s a :CoFormulant .
        }""", 0),
    "pi_no_ghs_hazard_labelling": ("""
        SELECT (COUNT(*) AS ?n) WHERE {
          ?p a :ParallelImport ; :ghsLabel ?c .
          ?c a :GHSLabelElement .
        }""", 0),
    "pi_only_sp_coded_statements": ("""
        SELECT (COUNT(*) AS ?n) WHERE {
          ?p a :ParallelImport ; :ghsLabel ?c .
          ?c a :PlantProtectionStatement .
          OPTIONAL { ?c schema:identifier ?id }
          FILTER(!BOUND(?id) || !REGEX(STR(?id), "^SP", "i"))
        }""", 0),
    "pi_I-4822_sp1_spe2": ("""
        SELECT (COUNT(DISTINCT ?c) AS ?n) WHERE {
          ?p a :ParallelImport ; :federalAdmissionNumber ?nr ; :ghsLabel ?c .
          FILTER(STR(?nr) = "I-4822")
        }""", 2),
        
    # Parallel imports: must still be there
    "pi_has_active_substances": ("""
        SELECT (COUNT(*) AS ?n) WHERE {
          ?p a :ParallelImport ; :ingredient/:substance ?s .
          ?s a :ActiveSubstance .
        }""", ">0"),
    "pi_has_sp_statements": ("""
        SELECT (COUNT(*) AS ?n) WHERE {
          ?p a :ParallelImport ; :ghsLabel ?c .
          ?c a :PlantProtectionStatement .
        }""", ">0"),

    # Regular products: unaffected
    "regular_has_ghs_hazard_labelling": ("""
        SELECT (COUNT(*) AS ?n) WHERE {
          ?p a :RegularProduct ; :ghsLabel ?c .
          ?c a :GHSLabelElement .
        }""", ">0"),
    "regular_has_coformulants": ("""
        SELECT (COUNT(*) AS ?n) WHERE {
          ?p a :RegularProduct ; :ingredient/:substance ?s .
          ?s a :CoFormulant .
        }""", ">0"),

    # Model cleanup
    "no_hasPlantProtectionStatement": ("""
        SELECT (COUNT(*) AS ?n) WHERE {
          { ?s :hasPlantProtectionStatement ?o }
          UNION { :hasPlantProtectionStatement ?p ?o }
        }""", 0),
    "ghsLabel_range_includes_statements": ("""
        SELECT (COUNT(*) AS ?n) WHERE {
          :ghsLabel rdfs:range/owl:unionOf/rdf:rest*/rdf:first :PlantProtectionStatement .
        }""", 1),
}


def count(graph: Graph, query: str) -> int:
    """Run a COUNT query and return the single number."""
    return int(next(iter(graph.query(PREFIXES + query)))[0])


def matches(n: int, expect: int | str) -> bool:
    return n > 0 if expect == ">0" else n == expect


@pytest.fixture(scope="module")
def graph() -> Graph:
    if not GRAPH_PATH.exists():
        pytest.skip(f"{GRAPH_PATH} not found, run the pipeline first")
    g = Graph()
    g.parse(GRAPH_PATH, format="turtle")
    return g


@pytest.mark.parametrize("query, expect", CHECKS.values(), ids=CHECKS.keys())
def test_parallel_import_rules(graph, query, expect):
    n = count(graph, query)
    assert matches(n, expect), f"got {n}, expected {expect}"


if __name__ == "__main__":
    g = Graph()
    g.parse(GRAPH_PATH, format="turtle")
    ok = True
    for name, (query, expect) in CHECKS.items():
        n = count(g, query)
        passed = matches(n, expect)
        print(f"[{'OK' if passed else 'FAIL'}] {name}: {n} (expected {expect})")
        ok = ok and passed
    sys.exit(0 if ok else 1)