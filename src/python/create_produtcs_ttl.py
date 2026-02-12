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

# Mappings
type_mapping = {
    "REGULAR": BASE.RegularProduct,
    "SALE_PERMISSION": BASE.SalePermission,
    "PARALLEL_IMPORT": BASE.ParallelImport
}

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

            # Normalize product_id
            product_id_str = str(row["product_id"]).strip()
            product_uri = PRODUCT[product_id_str]
            
            # Add product name
            graph.add((product_uri, SCHEMA.name, Literal(str(row["schema:name"]).strip(), lang="de")))

            # Get raw type
            raw_type = row.get("rdf:type")
            
            # Case 1: Regular Product or Sale Permission
            if raw_type in ["REGULAR", "SALE_PERMISSION"]:
                if pd.notna(row.get("w_number")):
                    w_number_str = str(row["w_number"]).strip()
                    # Apply W- prefix
                    fed_adm_num = f"W-{w_number_str}"
                    graph.add((product_uri, BASE.federalAdmissionNumber, Literal(fed_adm_num, datatype=XSD.string)))

            # Case 2: Parallel Import
            elif raw_type == "PARALLEL_IMPORT":
                if pd.notna(row.get("record_id")):
                    id_val = str(row.get("record_id")).strip()
                    graph.add((product_uri, BASE.federalAdmissionNumber, Literal(id_val, datatype=XSD.string)))

                # foreignAdmissionNumber from "admission_number"
                if pd.notna(row.get("admission_number")):
                    adm_num = str(row.get("admission_number")).strip()
                    graph.add((product_uri, BASE.foreignAdmissionNumber, Literal(adm_num, datatype=XSD.string)))

                # packageInsertNumber from "package_insert_flag"
                pkg_val = row.get("package_insert_flag")
                if pd.notna(pkg_val):
                    try:
                        # Fix: Cast to int first to drop decimal (4521.0 -> 4521)
                        pkg_ins_num = str(int(float(pkg_val)))
                    except (ValueError, TypeError):
                        # Fallback if the value is not numeric
                        pkg_ins_num = str(pkg_val).strip()
                        
                    graph.add((product_uri, BASE.packageInsertNumber, Literal(pkg_ins_num, datatype=XSD.string)))

            # Add product type
            rdf_type_uri = type_mapping.get(raw_type, BASE.Product) # Default to generic Product if unknown
            graph.add((product_uri, RDF.type, rdf_type_uri))

            # Add link to reference product
            ref_id_raw = row.get("product_ref_id")
            if pd.notna(ref_id_raw):
                ref_id_str = str(ref_id_raw).strip()
                # Constraint: Only add triple if ID differs from Reference ID
                if product_id_str != ref_id_str:
                    ref_product_uri = PRODUCT[ref_id_str]
                    graph.add((product_uri, BASE.referenceProduct, ref_product_uri))

        except Exception as error:
            print(f"Row {i}: {error}")

    # Print graph info
    print(f"[i] Total triples: {len(graph)}")

    # Save to file
    out_path = Path("rdf/data/products.ttl")
    graph.serialize(destination=out_path, format="turtle")
    print(f"\nSaved to `{out_path}`")
    return graph

if __name__ == "__main__":
    products_ttl()
