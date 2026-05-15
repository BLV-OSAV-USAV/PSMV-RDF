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

def ghs_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/ghs.ttl"
):
    """
    Creates a ghs_ttl graph extracting GHS-related entities from the Code table.
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    
    # Fallback instantiation if explicitly missing in namespaces.yaml
    CODE = namespaces.get("code", Namespace(str(BASE) + "code/"))
    GHS = namespaces.get("ghs", Namespace("https://agriculture.ld.admin.ch/plant-protection/ghs/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("code", CODE)
    graph.bind("ghs", GHS)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data using a pivoting approach
    con = duckdb.connect(db_path, read_only=True)
    query = """
    SELECT 
        code_id,
        MAX(text_key) AS text_key,
        MAX(code_value) AS code_value,
        MAX(CASE WHEN language = 'en' THEN value END) AS EN,
        MAX(CASE WHEN language = 'de' THEN value END) AS DE,
        MAX(CASE WHEN language = 'fr' THEN value END) AS FR,
        MAX(CASE WHEN language = 'it' THEN value END) AS IT
    FROM Code
    WHERE text_key IN ('SignalWords', 'DangerSymbol', 'CodeR', 'CodeS')
    GROUP BY code_id
    """
    ghs_df = con.execute(query).df()
    con.close()

    type_mapping = {
        "SignalWords": GHS.SignalWord,
        "DangerSymbol": GHS.HazardPictogram,
        "CodeR": GHS.HazardStatement,
        "CodeS": GHS.PrecautionaryStatement
    }

    # Create GHS triples
    for i, row in ghs_df.iterrows():
        try:
            if pd.isna(row.get("code_id")):
                continue

            code_id = str(row["code_id"]).strip()
            ghs_uri = CODE[code_id]
            
            text_key = str(row.get("text_key")).strip()
            rdf_type = type_mapping.get(text_key)

            if not rdf_type:
                continue

            # Add Type
            graph.add((ghs_uri, RDF.type, rdf_type))
            
            # Add Identifier (CODE_VALUE)
            if pd.notna(row.get("code_value")):
                code_val = str(row["code_value"]).strip()
                if code_val:
                    graph.add((ghs_uri, SCHEMA.identifier, Literal(code_val)))

            # Add language-tagged Names
            if pd.notna(row.get("DE")):
                graph.add((ghs_uri, SCHEMA.name, Literal(str(row["DE"]).strip(), lang="de")))
            if pd.notna(row.get("EN")):
                graph.add((ghs_uri, SCHEMA.name, Literal(str(row["EN"]).strip(), lang="en")))
            if pd.notna(row.get("FR")):
                graph.add((ghs_uri, SCHEMA.name, Literal(str(row["FR"]).strip(), lang="fr")))
            if pd.notna(row.get("IT")):
                graph.add((ghs_uri, SCHEMA.name, Literal(str(row["IT"]).strip(), lang="it")))

        except Exception as error:
            print(f"Row {i} (GHS Entity {code_id}): {error}")

    # Print graph info
    print(f"[i] Total GHS triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    ghs_ttl()