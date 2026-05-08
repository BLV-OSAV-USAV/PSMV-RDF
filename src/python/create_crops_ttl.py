import os
import sys
import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF
from rdflib.namespace import NamespaceManager

# local imports
from src.python.utils.helper_functions import load_namespaces

def crops_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/crops.ttl"
):
    """
    Creates a crops_ttl graph extracting Culture entities from the Code table.
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    
    # Fallback instantiation if they are not explicitly present in namespaces.yaml
    CROP = namespaces.get("crop", Namespace(str(BASE) + "crop/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("crop", CROP)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data using a pivoting approach to group translations into a single row
    con = duckdb.connect(db_path, read_only=True)
    query = """
    SELECT 
        code_id,
        MAX(parent_id) AS parent_id,
        MAX(CASE WHEN language = 'en' THEN value END) AS EN,
        MAX(CASE WHEN language = 'de' THEN value END) AS DE,
        MAX(CASE WHEN language = 'fr' THEN value END) AS FR,
        MAX(CASE WHEN language = 'it' THEN value END) AS IT
    FROM Code
    WHERE text_key = 'Culture'
    GROUP BY code_id
    """
    crops_df = con.execute(query).df()
    con.close()

    # Create crop triples
    for i, row in crops_df.iterrows():
        try:
            if pd.isna(row.get("code_id")):
                continue

            code_id = str(row["code_id"]).strip()
            crop_uri = CROP[code_id]

            # Add Type
            graph.add((crop_uri, RDF.type, BASE.Crop))
            
            # Add Identifier
            graph.add((crop_uri, SCHEMA.identifier, Literal(code_id)))

            # Add Part
            if pd.notna(row.get("parent_id")):
                parent_id = str(row["parent_id"]).strip()
                graph.add((crop_uri, SCHEMA.isPartOf, CROP[parent_id]))

            # Add language-tagged Names
            if pd.notna(row.get("DE")):
                graph.add((crop_uri, SCHEMA.name, Literal(str(row["DE"]).strip(), lang="de")))
            if pd.notna(row.get("EN")):
                graph.add((crop_uri, SCHEMA.name, Literal(str(row["EN"]).strip(), lang="en")))
            if pd.notna(row.get("FR")):
                graph.add((crop_uri, SCHEMA.name, Literal(str(row["FR"]).strip(), lang="fr")))
            if pd.notna(row.get("IT")):
                graph.add((crop_uri, SCHEMA.name, Literal(str(row["IT"]).strip(), lang="it")))

        except Exception as error:
            print(f"Row {i} (Crop {code_id}): {error}")

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