import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF

# local imports
from src.python.utils.helper_functions import load_namespaces, add_lang_labels

def crops_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/crops.ttl"
):
    """
    Creates a crops_ttl graph extracting Crop entities from the CultureCode table.
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    XSD = namespaces["xsd"]
    
    # Fallback instantiation if they are not explicitly present in namespaces.yaml
    CROP = namespaces.get("crop", Namespace(str(BASE) + "crop/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("crop", CROP)
    graph.bind("xsd", XSD)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)
    crops_df = con.execute("SELECT * FROM CultureCode").df()
    con.close()

    # Create crop triples
    for i, row in crops_df.iterrows():
        code_id = None
        try:
            if pd.isna(row.get("code_id")) or not str(row.get("code_id")).strip():
                print(f"Crop row {i}: missing code_id -> skipped")
                continue

            code_id = str(row["code_id"]).strip()
            crop_uri = CROP[code_id]

            # Add Type
            graph.add((crop_uri, RDF.type, BASE.Crop))
            
            # Add Identifier
            graph.add((crop_uri, SCHEMA.identifier, Literal(code_id, datatype=XSD.string)))

            # Add Part
            if pd.notna(row.get("parent_id")) and str(row.get("parent_id")).strip():
                parent_id = str(row["parent_id"]).strip()
                graph.add((crop_uri, SCHEMA.isPartOf, CROP[parent_id]))

            # Add language-tagged Names
            add_lang_labels(graph, crop_uri, SCHEMA.name, row)

        except Exception as error:
            print(f"Crop row {i} ({code_id or 'unknown'}): {error}")

    # Print graph info
    print(f"[i] Total crop triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    crops_ttl()