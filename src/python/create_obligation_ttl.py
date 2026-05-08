import os
import sys
import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF

# local imports
from src.python.utils.helper_functions import load_namespaces

def obligation_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/obligations.ttl"
):
    """
    Creates an obligations_ttl graph extracting Obligation entities from the Code table.
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    
    # Fallback instantiation if explicitly missing in namespaces.yaml
    CODE = namespaces.get("code", Namespace(str(BASE) + "code/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("code", CODE)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data using a pivoting approach
    con = duckdb.connect(db_path, read_only=True)
    query = """
    SELECT 
        code_id,
        MAX(code_value) AS code_value,
        MAX(CASE WHEN language = 'en' THEN value END) AS EN,
        MAX(CASE WHEN language = 'de' THEN value END) AS DE,
        MAX(CASE WHEN language = 'fr' THEN value END) AS FR,
        MAX(CASE WHEN language = 'it' THEN value END) AS IT
    FROM Code
    WHERE text_key = 'Obligation'
    GROUP BY code_id
    """
    obligation_df = con.execute(query).df()
    con.close()

    # Create triples
    for i, row in obligation_df.iterrows():
        try:
            if pd.isna(row.get("code_id")):
                continue

            code_id = str(row["code_id"]).strip()
            obl_uri = CODE[code_id]

            # Add Type
            graph.add((obl_uri, RDF.type, BASE.Obligation))
            
            # Add Identifier (CODE_VALUE)
            if pd.notna(row.get("code_value")):
                code_val = str(row["code_value"]).strip()
                graph.add((obl_uri, SCHEMA.identifier, Literal(code_val)))

            # Add language-tagged Descriptions
            # Using schema:description as requested
            if pd.notna(row.get("DE")):
                graph.add((obl_uri, SCHEMA.description, Literal(str(row["DE"]).strip(), lang="de")))
            if pd.notna(row.get("EN")):
                graph.add((obl_uri, SCHEMA.description, Literal(str(row["EN"]).strip(), lang="en")))
            if pd.notna(row.get("FR")):
                graph.add((obl_uri, SCHEMA.description, Literal(str(row["FR"]).strip(), lang="fr")))
            if pd.notna(row.get("IT")):
                graph.add((obl_uri, SCHEMA.description, Literal(str(row["IT"]).strip(), lang="it")))

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