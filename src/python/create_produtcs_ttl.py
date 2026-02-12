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
COUNTRY = namespaces["country"]

# Country mapping
COUNTRY_MAPPING = {
    "6698dcfd-d86e-4098-a5a4-da5b71062093": COUNTRY.CHE,
    "a0d7e6ea-cb57-4e37-8fad-2fcf26f69804": COUNTRY.GBR,
    "dac731ac-bb70-4164-b500-83559938b481": COUNTRY.GBR,
    "1f940d8d-2632-44a9-a4d5-8172ae6661e2": COUNTRY.GBR,
    "2d1a1c1b-2f41-4a9b-90ca-ed5afef79821": COUNTRY.IRL,
    "2e460bbe-6a62-40a2-8c1f-f7a7145a42c2": COUNTRY.IRL,
    "c3ffe09f-f38f-42b3-8601-ce60db2a37f5": COUNTRY.FRA,
    "9e495cc6-2d2c-4e76-b183-8d98611aeba4": COUNTRY.BEL,
    "29738aa2-5393-438d-be07-9d6b56d2accf": COUNTRY.AUT,
    "68921504-8a62-4b7b-b7f7-59399b483095": COUNTRY.JPN,
    "2233514d-c9d3-451e-961f-3a6b62af786d": COUNTRY.SRB,
    "c95be4f8-5218-4c95-9e7c-9b2ec712a45c": COUNTRY.GRC,
    "c9de192c-796f-4b51-bede-4b2cbab63a5f": COUNTRY.LUX,
    "02a7b748-c3de-440d-823e-5303232db2da": COUNTRY.DNK,
    "56cce907-f002-4b0c-b948-98299b1fea6e": COUNTRY.DEU,
    "5040d15a-cea6-41d8-a64e-def0dd366b18": COUNTRY.SVK,
    "fb4131dc-dca0-4e96-9664-e1d2484e4306": COUNTRY.CYP,
    "e815a08e-a569-4408-9c31-20a1702b0fda": COUNTRY.PRT,
    "70d1c2d0-f04e-47f3-9969-6f8d8b82ff2c": COUNTRY.SVN,
    "13ca0e2a-04ab-4bcd-a462-d4ea82b6fa74": COUNTRY.POL,
    "e4d16808-543e-47ec-9bcc-50a0caec7c9b": COUNTRY.ISR,
    "be1d323d-29e4-4570-8618-5463896be5d2": COUNTRY.ITA,
    "beb87459-db4c-4c85-84eb-bef7c6e012ef": COUNTRY.ESP,
    "a806bbc8-e72f-4dde-944f-5bc460a94c28": COUNTRY.LIE,
    "95635aeb-5ebb-4948-9595-6894b4ac0773": COUNTRY.HUN,
    "cda1f206-edb0-40d2-8ff6-15b29ead6c7f": COUNTRY.IND,
    "51f6122d-47ec-4051-97cc-01d7cf8e4758": COUNTRY.NLD,
}

# Mappings for Product Types
TYPE_MAPPING = {
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
    graph.bind("country", COUNTRY)

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
                    # Apply W- prefix (W-numbers only have the prefix for parallel products...)
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
                        # Cast to int first to drop decimal (4521.0 -> 4521)
                        pkg_ins_num = str(int(float(pkg_val)))
                    except (ValueError, TypeError):
                        # Fallback if the value is not numeric
                        pkg_ins_num = str(pkg_val).strip()
                        
                    graph.add((product_uri, BASE.packageInsertNumber, Literal(pkg_ins_num, datatype=XSD.string)))

            # Add producing country
            country_uuid = row.get("producing_country_id")
            if pd.notna(country_uuid):
                country_uuid_str = str(country_uuid).strip()
                # If the UUID is found in our mapping, link to the official ld.admin country URI
                if country_uuid_str in COUNTRY_MAPPING:
                    country_uri = COUNTRY_MAPPING[country_uuid_str]
                    graph.add((product_uri, BASE.producingCountry, country_uri))

            rdf_type_uri = TYPE_MAPPING.get(raw_type, BASE.Product)
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=out_path, format="turtle")
    print(f"\nSaved to `{out_path}`")
    return graph

if __name__ == "__main__":
    products_ttl()