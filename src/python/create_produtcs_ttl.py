import sys
import csv

from pathlib import Path
import pandas as pd

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD

# local imports
from utils.helper_functions import load_namespaces

# Set namespaces
namespaces = load_namespaces()

BASE = namespaces["base"]
PRODUCT = namespaces["product"]
SUBSTANCE = namespaces["substance"]
SCHEMA = namespaces["schema"]
UNIT = namespaces["unit"]
ZEFIX = namespaces["zefix"]
COMPANY = namespaces["company"]

# Create Products
def products_ttl(
    products_data_path = "data/processed/Product.csv",
    product_organisation_link_path = "data/processed/ProductOrganisation.csv"):

    """
    Creates products_ttl
    """
    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("product", PRODUCT)
    graph.bind("substance", SUBSTANCE)
    graph.bind("company", COMPANY)
    graph.bind("zefix", ZEFIX)
    graph.bind("schema", SCHEMA)
    graph.bind("unit", UNIT)

    # Read data
    products_df = pd.read_csv(products_data_path)
    pro_org_link_df = pd.read_csv(product_organisation_link_path)

    # Iterate through dataframe
    for i, row in products_df.iterrows():
        try: 
            # Skip missing required fields
            if pd.isna(row["product_id"]) or pd.isna(row["schema:name"]):
                continue

            product_uri = PRODUCT[str(row["product_id"]).strip()]
            
            # Add product name
            graph.add((product_uri, SCHEMA.name, Literal(str(row["schema:name"]).strip(), lang="de")))

            # Add w_number
            if pd.notna(row.get("w_number")):
                graph.add((product_uri, BASE.wNumber, Literal(str(row["w_number"]).strip(), datatype=XSD.string)))

            # Add product type
            product_type = row.get("rdf:type")
            if pd.isna(product_type):
                product_type = "PlantProtectionProduct"
            graph.add((product_uri, RDF.type, BASE[str(product_type).strip().replace(" ", "")]))

            
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


