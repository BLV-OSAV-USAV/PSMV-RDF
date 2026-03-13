import os
import sys
import csv
import yaml
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
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
    graph.bind("unit", UNIT)
    graph.bind("country", COUNTRY)
    graph.bind("rdfs", RDFS)
    graph.bind("xsd", XSD)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    products_df = pd.read_csv(products_data_path)
    pro_org_link_df = pd.read_csv(product_organisation_link_path)

    # Create product triples
    for i, row in products_df.iterrows():
        try: 
            if pd.isna(row.get("product_id")) or pd.isna(row.get("schema:name")):
                continue

            product_id_str = str(row.get("product_id")).strip()
            product_uri = PRODUCT[product_id_str]
            
            graph.add((product_uri, SCHEMA.name, Literal(str(row.get("schema:name")).strip())))

            raw_type = row.get("rdf:type")
            
            # Case 1: Regular Product
            if raw_type == "REGULAR":
                graph.add((product_uri, RDF.type, BASE.RegularProduct))  # ← added
                if pd.notna(row.get("w_number")):
                    w_number_str = str(row.get("w_number")).strip()
                    fed_adm_num = f"W-{w_number_str}"
                    graph.add((product_uri, BASE.federalAdmissionNumber, Literal(fed_adm_num, datatype=XSD.string)))

            # Case 2: Sale Permission
            elif raw_type == "SALE_PERMISSION":
                graph.add((product_uri, RDF.type, BASE.SalePermission))  # ← added
                if pd.notna(row.get("w_number")):
                    w_number_str = str(row.get("w_number")).strip()
                    fed_adm_num = f"W-{w_number_str}"
                    graph.add((product_uri, BASE.federalAdmissionNumber, Literal(fed_adm_num, datatype=XSD.string)))

            # Case 3: Parallel Import
            elif raw_type == "PARALLEL_IMPORT":
                graph.add((product_uri, RDF.type, BASE.ParallelImport))  # ← added
                if pd.notna(row.get("record_id")):
                    id_val = str(row.get("record_id")).strip()
                    graph.add((product_uri, BASE.federalAdmissionNumber, Literal(id_val, datatype=XSD.string)))
                if pd.notna(row.get("admission_number")):
                    adm_num = str(row.get("admission_number")).strip()
                    graph.add((product_uri, BASE.foreignAdmissionNumber, Literal(adm_num, datatype=XSD.string)))
                if pd.notna(row.get("w_number_of_reference_product")):
                    pkg_val = row.get("w_number_of_reference_product")
                    pkg_ins_num = str(pkg_val).split('.')[0]
                    graph.add((product_uri, BASE.packageInsertNumber, Literal(pkg_ins_num, datatype=XSD.string)))

            # Add producing country
            if pd.notna(row.get("producing_country_id")):
                country_uuid_str = str(row.get("producing_country_id")).strip()
                if country_uuid_str in COUNTRY_MAPPING:
                    country_uri = URIRef(COUNTRY_MAPPING[country_uuid_str])
                    graph.add((product_uri, SCHEMA.countryOfOrigin, country_uri))

            # Add dates (Exhaustion and Sold Out Deadlines)
            # Input format may be: "2027-01-01 00:00:00.0000000"
            # Output format needs to be: "2027-01-01"^^xsd:date
            if pd.notna(row.get("exhaustion_deadline")):
                exhaustion_raw = row.get("exhaustion_deadline")
                if str(exhaustion_raw).strip():
                    try:
                        dt = pd.to_datetime(exhaustion_raw)
                        date_str = dt.strftime("%Y-%m-%d")
                        graph.add((product_uri, BASE.exhaustionDeadline, Literal(date_str, datatype=XSD.date)))
                    except ValueError:
                        pass 

            if pd.notna(row.get("sold_out_deadline")):
                sold_out_raw = row.get("sold_out_deadline")
                if str(sold_out_raw).strip():
                    try:
                        dt = pd.to_datetime(sold_out_raw)
                        date_str = dt.strftime("%Y-%m-%d")
                        graph.add((product_uri, BASE.soldOutDeadline, Literal(date_str, datatype=XSD.date)))
                    except ValueError:
                        pass 

            rdf_type_uri = TYPE_MAPPING.get(raw_type, BASE.Product)
            graph.add((product_uri, RDF.type, rdf_type_uri))

            # Add link to reference product
            if pd.notna(row.get("product_ref_or_id")):
                ref_id_str = str(row.get("product_ref_or_id")).strip()
                # Constraint: Only add triple if ID differs from Reference ID
                if product_id_str != ref_id_str:
                    ref_product_uri = PRODUCT[ref_id_str]
                    graph.add((product_uri, BASE.referenceProduct, ref_product_uri))

        except Exception as error:
            print(f"Row {i} (Product {product_id_str}): {error}")

    # Print graph info
    print(f"[i] Total triples: {len(graph)}")

    # Save to file
    out_path = Path("rdf/data/products.ttl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=out_path, format="turtle")
    print(f"\nSaved to `{out_path}`")
    return graph

if __name__ == "__main__":
    products_ttl()