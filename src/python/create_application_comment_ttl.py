import os
import sys
import html
import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF
from rdflib.namespace import NamespaceManager

# local imports
from src.python.utils.helper_functions import load_namespaces

def application_comment_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/application_comments.ttl"
):
    """
    Creates an application_comments_ttl graph extracting ApplicationComment entities from the Code table.
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    UNIT = namespaces["unit"]
    
    # Fallback instantiation if explicitly missing in namespaces.yaml
    CODE = namespaces.get("code", Namespace(str(BASE) + "code/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("code", CODE)
    graph.bind("unit", UNIT)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)
    app_comment_df = con.execute("SELECT * FROM ApplicationCommentCode").df()
    con.close()

    # Create application comment triples
    for i, row in app_comment_df.iterrows():
        try:
            if pd.isna(row.get("code_id")):
                continue

            code_id = str(row["code_id"]).strip()
            comment_uri = CODE[code_id]

            # Add Type
            graph.add((comment_uri, RDF.type, BASE.ApplicationComment))

            # Add language-tagged Descriptions (unescaping HTML entities like &gt;)
            if pd.notna(row.get("DE")):
                graph.add((comment_uri, SCHEMA.description, Literal(html.unescape(str(row["DE"]).strip()), lang="de")))
            if pd.notna(row.get("EN")):
                graph.add((comment_uri, SCHEMA.description, Literal(html.unescape(str(row["EN"]).strip()), lang="en")))
            if pd.notna(row.get("FR")):
                graph.add((comment_uri, SCHEMA.description, Literal(html.unescape(str(row["FR"]).strip()), lang="fr")))
            if pd.notna(row.get("IT")):
                graph.add((comment_uri, SCHEMA.description, Literal(html.unescape(str(row["IT"]).strip()), lang="it")))

            # Add waiting period blank node if applicable
            if pd.notna(row.get("min_interval_between_uses")):
                interval_val = str(row["min_interval_between_uses"]).strip()
                if interval_val:
                    wp_node = BNode()
                    graph.add((comment_uri, BASE.waitingPeriod, wp_node))
                    graph.add((wp_node, RDF.type, SCHEMA.QuantitativeValue))
                    graph.add((wp_node, SCHEMA.unitCode, UNIT.DAY))
                    
                    try:
                        # Parse string to an integer
                        num_val = int(float(interval_val))
                        graph.add((wp_node, SCHEMA.minValue, Literal(num_val)))
                    except ValueError:
                        # Fallback for unexpected non-numeric formats
                        graph.add((wp_node, SCHEMA.minValue, Literal(interval_val)))

        except Exception as error:
            print(f"Row {i} (Application Comment {code_id}): {error}")

    # Print graph info
    print(f"[i] Total application comment triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    application_comment_ttl()