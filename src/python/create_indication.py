import os
import sys
import csv
import yaml
import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
from rdflib.namespace import NamespaceManager

# local imports
from src.python.utils.helper_functions import load_namespaces, load_rdf_mappings

# Set namespaces
namespaces = load_namespaces()

BASE = namespaces["base"]
PRODUCT = namespaces["product"]
SUBSTANCE = namespaces["substance"]
SCHEMA = namespaces["schema"]
UNIT = namespaces["unit"]
ZEFIX = namespaces["zefix"]
COMPANY = namespaces["company"]
COUNTRY = namespaces["country"]
XSD = namespaces["xsd"]
CHEBI = namespaces["chebi"]
PUBCHEM_COMPOUND = namespaces["pubchem_compound"]
PUBCHEM_SUBSTANCE = namespaces["pubchem_substance"]
WIKIDATA = namespaces["wikidata"]

# Load all RDF mappings
# Explicitly specify which namespace each mapping uses
namespace_config = {
    "country_mapping": "country",
    "type_mapping": "base"
}

rdf_mappings = load_rdf_mappings(namespaces, namespace_map=namespace_config)  

COUNTRY_MAPPING = rdf_mappings["country_mapping"]
TYPE_MAPPING = rdf_mappings["type_mapping"]

# Create Products
def indication_ttl(
    db_path = "data/processed/psmv-data.duckdb",
    out_path: str = "rdf/data/substance_ttl"):

    """
    Creates a substance_ttl
    """

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("product", PRODUCT)
    graph.bind("substance", SUBSTANCE)
    graph.bind("company", COMPANY)
    graph.bind("zefix", ZEFIX)
    graph.bind("unit", UNIT)
    graph.bind("country", COUNTRY)
    graph.bind("chebi", CHEBI)
    graph.bind("pubchem_compound", PUBCHEM_COMPOUND)
    graph.bind("pubchem_substance", PUBCHEM_SUBSTANCE)
    graph.bind("wikidata", WIKIDATA)

    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)
    indication_df = con.execute("SELECT * FROM Indication").df()
    con.close()

    # Create substance triples
    for i, row in indication_df.iterrows():
        try:
            if pd.isna(row.get("id")):
                continue
        
            nk_codetable_substance_id = str(row.get("id")).strip()
            substance_uri = SUBSTANCE[nk_codetable_substance_id]

   
        except Exception as error:
            print(f"Row {i} (Substance {substance_uri}): {error}")

    # Print graph info
    print(f"[i] Total triples: {len(graph)}")

    # Save to file
    out_path = Path("rdf/data/indication.ttl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=out_path, format="turtle")
    print(f"\nSaved to `{out_path}`")
    return graph

if __name__ == "__main__":
    indication_ttl()