import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF

# local imports
from src.python.utils.helper_functions import load_namespaces, add_lang_labels

def application_area_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/application_areas.ttl"
):
    """
    Creates an application_areas_ttl graph extracting ApplicationArea entities from the ApplicationAreaCode table.
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
    
    try:
        app_area_df = con.execute("SELECT * FROM ApplicationAreaCode").df()
    except Exception as e:
        print(f"[!] Could not read ApplicationAreaCode ({e}).")
        app_area_df = pd.DataFrame()
        
    con.close()

    # Create application area triples
    for i, row in app_area_df.iterrows():
        code_id = None
        try:
            if pd.isna(row.get("code_id")) or not str(row.get("code_id")).strip():
                print(f"Application area row {i}: missing code_id -> skipped")
                continue

            code_id = str(row["code_id"]).strip().lower()
            area_uri = CODE[code_id]

            # Add Type
            graph.add((area_uri, RDF.type, BASE.ApplicationArea))
            
            # Add Identifier (CODE_VALUE) - The letter identifier
            if 'code_value' in row and pd.notna(row.get("code_value")):
                code_val = str(row["code_value"]).strip()
                if code_val:
                    graph.add((area_uri, SCHEMA.identifier, Literal(code_val)))

            # Add language-tagged Names
            add_lang_labels(graph, area_uri, SCHEMA.name, row)

        except Exception as error:
            print(f"Application area row {i} ({code_id or 'unknown'}): {error}")

    # Print graph info
    print(f"[i] Total application area triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    application_area_ttl()