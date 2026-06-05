import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF

# local imports
from src.python.utils.helper_functions import load_namespaces, add_lang_labels

def obligation_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/obligations.ttl"
):
    """
    Creates an obligations_ttl graph extracting Obligation entities from the ObligationCode table.
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    XSD = namespaces["xsd"]
    
    # Fallback instantiation if explicitly missing in namespaces.yaml
    CODE = namespaces.get("code", Namespace(str(BASE) + "code/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("code", CODE)
    graph.bind("xsd", XSD)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)
    obligation_df = con.execute("SELECT * FROM ObligationCode").df()
    con.close()

    # Create triples
    for i, row in obligation_df.iterrows():
        try:
            if pd.isna(row.get("code_id")) or not str(row.get("code_id")).strip():
                print(f"Obligation row {i}: missing code_id -> skipped")
                continue

            code_id = str(row["code_id"]).strip()
            obl_uri = CODE[code_id]

            # Add Type
            graph.add((obl_uri, RDF.type, BASE.Obligation))
            
            # Add Identifier (CODE_VALUE)
            if pd.notna(row.get("code_value")) and str(row.get("code_value")).strip():
                code_val = str(row["code_value"]).strip()
                graph.add((obl_uri, SCHEMA.identifier, Literal(code_val, datatype=XSD.string)))

            # Add language-tagged Descriptions
            # Using schema:description as requested
            add_lang_labels(graph, obl_uri, SCHEMA.name, row)

        except Exception as error:
            print(f"Row {i} (Obligation {code_id}): {error}")

    # Print graph info
    print(f"[i] Total obligation triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    obligation_ttl()