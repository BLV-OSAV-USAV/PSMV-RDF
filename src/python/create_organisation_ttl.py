import sys
import csv
import yaml

from pathlib import Path
import pandas as pd

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD

# local imports
from src.python.utils.helper_functions import load_namespaces

# Create Products
def organisation_ttl(
    organsiation_data_path: str = "data/processed/Organisation.csv",
    out_path: str = "rdf/data/organisation_test.ttl",
    mapping_rdf_path: str = "data/mapping/mapping_rdf.yaml",
    ):

    """
    Creates a Turtle file with organisation triples from Organisation.csv
    """

    # Load namespaces
    namespaces = load_namespaces()

    BASE = namespaces["base"]
    PRODUCT = namespaces["product"]
    SUBSTANCE = namespaces["substance"]
    SCHEMA = namespaces["schema"]
    UNIT = namespaces["unit"]
    ZEFIX = namespaces["zefix"]
    COMPANY = namespaces["company"]

    # Create a country namespace under BASE (e.g. .../country/CHE)
    COUNTRY = Namespace(str(BASE).rstrip("/") + "/country/")

    # Load mapping yaml
    with open(mapping_rdf_path, "r", encoding="utf-8") as f:
        mapping = yaml.safe_load(f) or {}
    country_mapping = mapping.get("country_mapping", {}) or {}

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

            #if pd.notna(row.get("country_id")):
            #    graph.add((org_uri, SCHEMA.addressCountry, Literal(str(row["country_id"]).strip(), datatype=XSD.string)))

            # country as iso3
            country_id = (row.get("country_id") or "").strip().lower()
            if country_id:
                iso3 = (country_mapping.get(country_id) or "").strip()
                if iso3:
                    graph.add((org_uri, SCHEMA.addressCountry, Literal(iso3)))
                else:
                    # If you strictly never want literals, best is to skip and log
                    print(f"Organisation row {i}: country_id '{country_id}' not found in mapping_rdf.yaml -> skipped")

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
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to {out_file}")
    return graph

if __name__ == "__main__":
    organisation_ttl()


