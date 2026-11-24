import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, SKOS

# local imports
from src.python.utils.helper_functions import load_namespaces, add_lang_labels, load_unit_map

def measure_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/measures.ttl"
):
    """
    Creates a measures_ttl graph extracting Measure entities from the MeasureCode table
    (code lists 'Measure' and 'TimeMeasure', see process_measure_code).
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    XSD = namespaces["xsd"]
    UNIT = namespaces["unit"]
    
    # Fallback instantiation if explicitly missing in namespaces.yaml
    MEASURE = namespaces.get("measure", Namespace(str(BASE) + "measure/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("measure", MEASURE)
    graph.bind("unit", UNIT)
    graph.bind("skos", SKOS)
    graph.bind("xsd", XSD)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)
    measure_df = con.execute("SELECT * FROM MeasureCode").df()
    con.close()

    # Load Unit map
    UNIT_MAP = load_unit_map(UNIT)

    # Create triples
    for i, row in measure_df.iterrows():
        try:
            if pd.isna(row.get("code_id")) or not str(row.get("code_id")).strip():
                print(f"Measure row {i}: missing code_id -> skipped")
                continue

            code_id = str(row["code_id"]).strip().lower()
            measure_uri = MEASURE[code_id]

            # Add Type
            graph.add((measure_uri, RDF.type, BASE.Measure))

            # Add Identifier
            graph.add((measure_uri, SCHEMA.identifier, Literal(code_id, datatype=XSD.string)))

            # Add language-tagged Names
            add_lang_labels(graph, measure_uri, SCHEMA.name, row)

            # Add QUDT unit (only where an equivalent exists in unit_map.yaml)
            if pd.notna(row.get("DE")) and str(row.get("DE")).strip() in UNIT_MAP:
                unit_uri = UNIT_MAP[str(row["DE"]).strip()]
                graph.add((measure_uri, SKOS.exactMatch, unit_uri))

        except Exception as error:
            print(f"Row {i} (Measure {code_id}): {error}")

    # Print graph info
    print(f"[i] Total measure triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    measure_ttl()