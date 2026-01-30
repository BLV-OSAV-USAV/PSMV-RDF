import sys
import csv
import logging

from pathlib import Path
import pandas as pd

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD

# local imports
from utils.helper_functions import load_namespaces

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sert namespaces
namespaces = load_namespaces()

BASE = namespaces["base"]
PRODUCT = namespaces["product"]
SUBSTANCE = namespaces["substance"]
SCHEMA = namespaces["schema"]
UNIT = namespaces["unit"]
ZEFIX = namespaces["zefix"]
COMPANY = namespaces["company"]

# Create Products
def products_ttl():
    """
    Creates products_ttl
    """
    # Create empty graph
    graph = Graph()
    
    # Bind namespaces (do this once, outside the loop)
    graph.bind("", BASE)
    graph.bind("product", PRODUCT)
    graph.bind("substance", SUBSTANCE)
    graph.bind("company", COMPANY)
    graph.bind("zefix", ZEFIX)
    graph.bind("schema", SCHEMA)
    graph.bind("unit", UNIT)
    graph.bind("xsd", XSD)

    # Read data
    df = pd.read_csv("data/processed/AllProducts_Renamed.csv")

    # Iterate through dataframe
    for i, row in df.iterrows():
        try: 
            # Skip missing required fields
            if pd.isna(row["product_id"]) or pd.isna(row["product_name"]):
                continue

            product_uri = PRODUCT[str(row["product_id"]).strip()]

            # Add product type
            product_type = row.get("product_type", "PlantProtectionProduct")
            graph.add((product_uri, RDF.type, BASE[product_type]))
            
            # Add product name
            graph.add((product_uri, SCHEMA.name, Literal(str(row["product_name"]).strip(), lang="de")))
            
        except Exception as error:
            print(f"Row {i}: {error}")

    # Print graph info
    print(f"\nGraph created successfully!")
    print(f"Total triples: {len(graph)}")

    # Print first triple
    print(f"\nFirst three triples:")
    for i, (s, p, o) in enumerate(graph):
        if i >= 3:
            break
        print(f"{s} {p} {o}")

    # Save to file
    graph.serialize(destination="rdf/data/products_test.ttl", format="turtle")
    print(f"\nSaved to products_test.ttl")

    return graph

if __name__ == "__main__":
    products_ttl()


