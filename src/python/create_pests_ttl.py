import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF

# local imports
from src.python.utils.helper_functions import load_namespaces, add_lang_labels

def pests_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/pests.ttl"
):
    """
    Creates a pests_ttl graph extracting Pest entities from the Code table.
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    XSD = namespaces["xsd"]
    
    # Fallback instantiation if they are not explicitly present in namespaces.yaml
    PEST = namespaces.get("pest", Namespace(str(BASE) + "pest/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("pest", PEST)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data using a pivoting approach to group translations into a single row
    con = duckdb.connect(db_path, read_only=True)
    pests_df = con.execute("SELECT * FROM PestCode").df()
    con.close()

    # Create pest triples
    for i, row in pests_df.iterrows():
        try:
            if pd.isna(row.get("code_id")) or not str(row.get("code_id")).strip():
                print(f"Pest row {i}: missing code_id -> skipped")
                continue

            code_id = str(row["code_id"]).strip()
            pest_uri = PEST[code_id]

            # Add Type
            graph.add((pest_uri, RDF.type, BASE.Pest))

            # Add Identifier
            graph.add((pest_uri, SCHEMA.identifier, Literal(code_id, datatype=XSD.string)))

            # Add Part
            if pd.notna(row.get("parent_id")) and str(row.get("parent_id")).strip():
                parent_id = str(row["parent_id"]).strip()
                graph.add((pest_uri, SCHEMA.isPartOf, PEST[parent_id]))

            # Add language-tagged Names
            add_lang_labels(graph, pest_uri, SCHEMA.name, row)

        except Exception as error:
            print(f"Row {i} (Pest {code_id}): {error}")

    # Print graph info
    print(f"[i] Total pest triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    pests_ttl()