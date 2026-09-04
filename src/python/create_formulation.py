import os
import sys
import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF
from rdflib.namespace import NamespaceManager

# local imports
from src.python.utils.helper_functions import load_namespaces, add_lang_labels

def formulation_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/formulation.ttl"
):
    """
    Creates a formulation graph from the FormulationCode vocabulary table.
    """
    namespaces = load_namespaces()

    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    CODE = namespaces.get("code", Namespace(str(BASE) + "code/"))

    graph = Graph()
    graph.bind("", BASE)
    graph.bind("code", CODE)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    con = duckdb.connect(db_path, read_only=True)
    formulation_df = con.execute("SELECT * FROM FormulationCode").df()
    con.close()

    for i, row in formulation_df.iterrows():
        code_id = None
        try:
            if pd.isna(row.get("code_id")):
                continue

            code_id = str(row["code_id"]).strip().lower()
            code_uri = CODE[code_id]

            graph.add((code_uri, RDF.type, BASE.FormulationType))

            if pd.notna(row.get("code_value")):
                code_val = str(row["code_value"]).strip()
                if code_val:
                    graph.add((code_uri, SCHEMA.identifier, Literal(code_val)))

            add_lang_labels(graph, code_uri, SCHEMA.name, row)

        except Exception as error:
            print(f"Row {i} (Formulation {code_id}): {error}")

    print(f"[i] Total formulation triples: {len(graph)}")

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")

    return graph

if __name__ == "__main__":
    formulation_ttl()