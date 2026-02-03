import sys
import csv

from pathlib import Path
import pandas as pd

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD

# local imports
from utils.helper_functions import load_namespaces

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
def organisation_ttl(
    organsiation_data_path = "data/processed/Organisation.csv"
    ):

    """
    Creates organisations_ttl
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
    organsiation_df = pd.read_csv(organsiation_data_path)

    # Create organisation triples
    for i, row in organsiation_df.iterrows():
        try:
            if pd.isna(row["organisation_id"]):
                continue

            org_uri = COMPANY[str(row["organisation_id"]).strip()]

            # Add organisation type
            graph.add((org_uri, RDF.type, BASE.Organisation))

            # Add name
            if pd.notna(row.get("organisation_name")):
                graph.add((org_uri, SCHEMA.name, Literal(str(row["organisation_name"]).strip(), lang="de")))

            # Add contact info
            if pd.notna(row.get("phone_number")):
                graph.add((org_uri, SCHEMA.telephone, Literal(str(row["phone_number"]).strip(), datatype=XSD.string)))

            if pd.notna(row.get("fax_number")):
                graph.add((org_uri, SCHEMA.faxNumber, Literal(str(row["fax_number"]).strip(), datatype=XSD.string)))

            # Add address
            if pd.notna(row.get("street_address")):
                graph.add((org_uri, SCHEMA.streetAddress, Literal(str(row["street_address"]).strip(), datatype=XSD.string)))

            if pd.notna(row.get("post_office_box")):
                graph.add((org_uri, SCHEMA.postOfficeBoxNumber, Literal(str(row["post_office_box"]).strip(), datatype=XSD.string)))

            if pd.notna(row.get("city_id")):
                graph.add((org_uri, SCHEMA.addressLocality, Literal(str(row["city_id"]).strip(), datatype=XSD.string)))

            if pd.notna(row.get("country_id")):
                graph.add((org_uri, SCHEMA.addressCountry, Literal(str(row["country_id"]).strip(), datatype=XSD.string)))

            if pd.notna(row.get("additional_information")):
                graph.add((org_uri, SCHEMA.description, Literal(str(row["additional_information"]).strip(), lang="de")))

        except Exception as error:
            print(f"Organisation row {i}: {error}")

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
    graph.serialize(destination="rdf/data/organisation_test.ttl", format="turtle")
    print(f"\nSaved to organisation_test.ttl")
    return graph

if __name__ == "__main__":
    organisation_ttl()


