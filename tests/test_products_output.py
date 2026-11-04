import contextlib
import io
import re
from pathlib import Path

import pytest
from rdflib import Literal, URIRef

from src.python.utils.helper_functions import load_namespaces
from src.python.create_products_ttl import products_ttl

DB_PATH = Path("data/processed/psmv-data.duckdb")

pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(), reason="needs pipeline data, run the pipeline first"
)

NS = load_namespaces()
BASE, PRODUCT, XSD = NS["base"], NS["product"], NS["xsd"]


@pytest.fixture(scope="module")
def run():
    """Run products_ttl once, capture what it prints, return (graph, output)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        graph = products_ttl(db_path=str(DB_PATH))
    return graph, buf.getvalue()


# --- Idea 2: errors must not disappear silently -----------------------------

def test_no_row_errors(run):
    _, output = run
    errors = re.findall(r"^Row \d+ \(Product .*$", output, re.MULTILINE)
    assert not errors, f"{len(errors)} row error(s), first: {errors[:5]}"


# --- Idea 3: inline conversions, checked on the output ----------------------

def test_w_numbers_have_no_float_suffix(run):
    graph, _ = run
    bad = [str(o) for o in graph.objects(None, BASE.federalAdmissionNumber)
           if str(o).endswith(".0")]
    assert not bad, bad[:10]


def test_package_insert_numbers_are_clean(run):
    graph, _ = run
    bad = [str(o) for o in graph.objects(None, BASE.packageInsertNumber)
           if "." in str(o) or str(o).lower() == "nan"]
    assert not bad, bad[:10]


@pytest.mark.parametrize("prop", ["exhaustionDeadline", "soldOutDeadline"])
def test_dates_are_xsd_dates(run, prop):
    graph, _ = run
    bad = [o for o in graph.objects(None, BASE[prop])
           if o.datatype != XSD.date or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(o))]
    assert not bad, bad[:10]


def test_product_uris_are_lowercase(run):
    # guards against the UUID case bug that caused duplicate triples
    graph, _ = run
    bad = {str(s) for s in graph.subjects()
           if isinstance(s, URIRef) and str(s).startswith(str(PRODUCT))
           and str(s) != str(s).lower()}
    assert not bad, sorted(bad)[:10]


def test_no_nan_leaked_into_graph(run):
    # str(NaN) == "nan" is the classic pandas leak, into URIs or literals
    graph, _ = run
    bad = [t for t in graph
           if any((isinstance(x, URIRef) and str(x).lower().endswith("/nan"))
                  or (isinstance(x, Literal) and str(x).lower() == "nan")
                  for x in t)]
    assert not bad, bad[:5]