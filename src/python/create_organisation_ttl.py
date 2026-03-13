import os
import sys
import csv
import yaml
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF
from rdflib import BNode

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
def organisation_ttl(
    organsiation_data_path: str = "data/processed/Organisation.csv",
    out_path: str = "rdf/data/organisation_ttl"):

    """
    Creates a organisation_ttl
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
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    organsiation_df = pd.read_csv(organsiation_data_path)

    # Create organisation triples
    for i, row in organsiation_df.iterrows():
        try:
            if pd.isna(row.get("organisation_id")) or pd.isna(row.get("organisation_name")):
                continue

            org_uri = COMPANY[str(row["organisation_id"]).strip()]

            # Add organisation type
            graph.add((org_uri, RDF.type, SCHEMA.Organization))

            # Add organisation name
            if pd.notna(row.get("organisation_name")):
                graph.add((org_uri, SCHEMA.name, Literal(str(row["organisation_name"]).strip())))

            # Add contact info
            if pd.notna(row.get("phone_number")):
                graph.add((org_uri, SCHEMA.telephone, Literal(str(row["phone_number"]).strip(), datatype=XSD.string)))

            # Add address node
            address_node = BNode()
            graph.add((org_uri, SCHEMA.address, address_node))
            graph.add((address_node, RDF.type, SCHEMA.PostalAddress))

            if pd.notna(row.get("street_address")):
                graph.add((address_node, SCHEMA.streetAddress, Literal(str(row["street_address"]).strip(), datatype=XSD.string)))

            if pd.notna(row.get("post_office_box")):
                graph.add((address_node, SCHEMA.postOfficeBoxNumber, Literal(str(row["post_office_box"]).strip(), datatype=XSD.string)))

            if pd.notna(row.get("city_id")):
                graph.add((address_node, SCHEMA.addressLocality, Literal(str(row["city_id"]).strip(), datatype=XSD.string)))

            # country as iso3
            country_id = (row.get("country_id") or "").strip().lower()
            if country_id:
                iso3 = (COUNTRY_MAPPING.get(country_id) or "").strip()
                if iso3:
                    graph.add((address_node, SCHEMA.addressCountry, URIRef(iso3)))
                else:
                    # If you strictly never want literals, best is to skip and log
                    print(f"Organisation row {i}: country_id '{country_id}' not found in mapping_rdf.yaml -> skipped")

        except Exception as error:
            print(f"Organisation row {i}: {error}")

    # Print graph info
    print(f"[i] Total triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to {out_file}")
    return graph

if __name__ == "__main__":
    organisation_ttl()
