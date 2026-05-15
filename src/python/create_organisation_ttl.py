# src/python/create_organisation_ttl.py

import os
import sys
import csv
import yaml
import duckdb
from pathlib import Path
import pandas as pd
import re
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

def parse_phone_numbers(raw_str):
    if pd.isna(raw_str) or not str(raw_str).strip():
        return []
    
    s = str(raw_str).strip()
    # Remove standard international (0) 
    s = re.sub(r'\(0\)', '', s)
    
    # Split by '/' if followed by '+', '00', or '0' and a digit
    s = re.sub(r'\s*/\s*(?=\+|00|0[1-9])', ' SEP ', s)
    # Split by '|'
    s = re.sub(r'\s*\|\s*', ' SEP ', s)
    # Split by any letters (e.g., 'mobile', 'direct call', 'M', 'T')
    s = re.sub(r'[a-zA-Z]+', ' SEP ', s)
    
    parts = s.split(' SEP ')
    
    formatted_nums = []
    for part in parts:
        # Keep only digits and the plus sign
        digits = re.sub(r'[^\d+]', '', part)
        
        if len(digits) < 7:
            continue
            
        # Convert initial '00' to '+'
        if digits.startswith('00'):
            digits = '+' + digits[2:]
        # Convert initial '0' to '+41'
        elif digits.startswith('0'):
            digits = '+41' + digits[1:]
        # Handle cases missing a country code prefix but having a length implying one
        elif not digits.startswith('+'):
            if len(digits) == 9:
                digits = '+41' + digits
            elif len(digits) > 9:
                digits = '+' + digits
                
        # Format typical Swiss numbers like: +41-76-472-24-53
        if digits.startswith('+41') and len(digits) == 12:
            formatted = f"{digits[0:3]}-{digits[3:5]}-{digits[5:8]}-{digits[8:10]}-{digits[10:12]}"
        # Format German numbers or long international numbers
        elif digits.startswith('+49') and len(digits) >= 12:
            formatted = f"{digits[0:3]}-" + "-".join(re.findall(r'.{1,4}', digits[3:]))
        # Format other numbers generically with hyphens
        else:
            if digits.startswith('+'):
                two_digit_cc = [
                    '30', '31', '32', '33', '34', '36', '39', '40', '41', '43', '44', '45', '46', 
                    '47', '48', '49', '51', '52', '53', '54', '55', '56', '57', '58', '60', '61', 
                    '62', '63', '64', '65', '66', '81', '82', '84', '86', '90', '91', '92', '93', 
                    '94', '95', '98'
                ]
                if digits[1] == '1' or digits[1] == '7':
                    cc_len = 2
                elif digits[1:3] in two_digit_cc:
                    cc_len = 3
                else:
                    cc_len = 4
                formatted = f"{digits[:cc_len]}-" + "-".join(re.findall(r'.{1,3}', digits[cc_len:]))
            else:
                formatted = "-".join(re.findall(r'.{1,3}', digits))
                
        if formatted not in formatted_nums:
            formatted_nums.append(formatted)
            
    return formatted_nums

# Create Products
def organisation_ttl(
    db_path = "data/processed/psmv-data.duckdb",
    out_path: str = "rdf/data/organisation.ttl"):

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
    con = duckdb.connect(db_path, read_only=True)
    # Join Organisation with the Code table to get the actual city name
    query = """
    SELECT 
        o.*,
        c.city_name
    FROM Organisation o
    LEFT JOIN (
        SELECT code_id, MAX(value) AS city_name 
        FROM Code 
        GROUP BY code_id
    ) c ON o.city_id = c.code_id
    """
    organsiation_df = con.execute(query).df()
    con.close()

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
                graph.add((org_uri, SCHEMA.legalName, Literal(str(row["organisation_name"]).strip())))

            # Add contact info
            if pd.notna(row.get("phone_number")):
                phones = parse_phone_numbers(row.get("phone_number"))
                for p in phones:
                    graph.add((org_uri, SCHEMA.telephone, Literal(p, datatype=XSD.string)))
                    
            if pd.notna(row.get("FAX")):
                faxes = parse_phone_numbers(row.get("FAX"))
                for f in faxes:
                    graph.add((org_uri, SCHEMA.faxNumber, Literal(f, datatype=XSD.string)))

            # Add address node
            address_node = BNode()
            graph.add((org_uri, SCHEMA.address, address_node))
            graph.add((address_node, RDF.type, SCHEMA.PostalAddress))

            if pd.notna(row.get("street_address")):
                graph.add((address_node, SCHEMA.streetAddress, Literal(str(row["street_address"]).strip(), datatype=XSD.string)))

            if pd.notna(row.get("post_office_box")):
                graph.add((address_node, SCHEMA.postOfficeBoxNumber, Literal(str(row["post_office_box"]).strip(), datatype=XSD.string)))

            # Add city
            if pd.notna(row.get("city_name")):
                # Prefer the mapped city name from the Code table
                graph.add((address_node, SCHEMA.addressLocality, Literal(str(row["city_name"]).strip(), datatype=XSD.string)))
            elif pd.notna(row.get("city_id")):
                # Fallback to ID if no match is found
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