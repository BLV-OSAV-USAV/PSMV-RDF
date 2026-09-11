import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF

# local imports
from src.python.utils.helper_functions import load_namespaces


def _read_fetch_date(metadata_path):
    """
    Reads `fetch_date` from the YAML written by the fetch script.
    Falls back to today's date if the file or the key is missing.
    """
    path = Path(metadata_path)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            fetch_date = (yaml.safe_load(f) or {}).get("fetch_date")
        if fetch_date:
            return date.fromisoformat(str(fetch_date))

    print(f"[i] No fetch date found in `{metadata_path}`, using today's date")
    return date.today()


def _model_version_iri(shapes_path, shape_doc_iri):
    """
    Reads `owl:versionIRI` of the data model from the SHACL shapes file,
    so the data always points to the model version it was built against.
    """
    shapes = Graph().parse(shapes_path, format="turtle")
    version_iri = shapes.value(shape_doc_iri, OWL.versionIRI)

    if not isinstance(version_iri, URIRef):
        raise ValueError(
            f"owl:versionIRI of <{shape_doc_iri}> in `{shapes_path}` is missing "
            f"or not an IRI (found: {version_iri!r})"
        )
    return version_iri


def dataset_ttl(
    data_as_of=None,
    metadata_path="data/raw/fetch_metadata.yaml",
    shapes_path="rdf/shapes/data_shape.ttl",
    out_path="rdf/data/dataset.ttl"
):
    """
    Creates the dataset metadata graph: a single `:dataset` node stating which
    registry export the data reflects, when the RDF was generated and which
    version of the data model it conforms to.

    The date is taken from `data_as_of` if given, otherwise from the fetch date
    in `metadata_path`, otherwise today's date.
    """
    # Set namespaces
    namespaces = load_namespaces()

    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    XSD = namespaces["xsd"]

    # Fallback instantiation if they are not explicitly present in namespaces.yaml
    DCTERMS = namespaces.get("dcterms", Namespace("http://purl.org/dc/terms/"))
    DCAT = namespaces.get("dcat", Namespace("http://www.w3.org/ns/dcat#"))
    PROV = namespaces.get("prov", Namespace("http://www.w3.org/ns/prov#"))
    SHAPE = namespaces.get("shape", Namespace(str(BASE) + "shape/"))

    # Resolve inputs before building anything, so problems fail early
    if data_as_of:
        as_of = date.fromisoformat(str(data_as_of))
    else:
        as_of = _read_fetch_date(metadata_path)
    version_iri = _model_version_iri(shapes_path, URIRef(str(SHAPE)))
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)

    # Create empty graph
    graph = Graph()

    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("dcterms", DCTERMS)
    graph.bind("dcat", DCAT)
    graph.bind("prov", PROV)
    graph.bind("xsd", XSD)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    dataset_uri = BASE["dataset"]

    # Add Types
    graph.add((dataset_uri, RDF.type, SCHEMA.Dataset))
    graph.add((dataset_uri, RDF.type, DCAT.Dataset))

    # Add fetch date ("data as of")
    graph.add((dataset_uri, DCTERMS.modified, Literal(as_of, datatype=XSD.date)))
    graph.add((dataset_uri, SCHEMA.dateModified, Literal(as_of, datatype=XSD.date)))

    # Add generation time of this RDF
    graph.add((dataset_uri, PROV.generatedAtTime, Literal(generated_at, datatype=XSD.dateTime)))

    # Add data model version
    graph.add((dataset_uri, DCTERMS.conformsTo, version_iri))

    # Print graph info
    print(f"[i] Data as of: {as_of.isoformat()}")
    print(f"[i] Data model: {version_iri}")
    print(f"[i] Total dataset triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")

    return graph


if __name__ == "__main__":
    # Optional: date as first argument, otherwise the fetch date is used
    dataset_ttl(sys.argv[1] if len(sys.argv) > 1 else None)