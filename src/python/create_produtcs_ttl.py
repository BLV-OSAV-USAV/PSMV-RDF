import os
import sys
import csv
import yaml
from pathlib import Path
import pandas as pd
import duckdb
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS
from rdflib.namespace import NamespaceManager

# local imports
from src.python.utils.helper_functions import load_namespaces, load_rdf_mappings

def products_ttl(
    db_path = "data/processed/psmv-data.duckdb",
    product_organisation_link_path = "data/processed/ProductOrganisation.csv"):

    """
    Creates products_ttl
    """
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
    
    # Required for GHS linking
    CODE = namespaces.get("code", Namespace(str(BASE) + "code/"))

    # Load all RDF mappings
    # Explicitly specify which namespace each mapping uses
    namespace_config = {
        "country_mapping": "country",
        "type_mapping": "base",
        "unit_mapping": "unit",
        "category_mapping": "base"
    }

    rdf_mappings = load_rdf_mappings(namespaces, namespace_map=namespace_config)  

    COUNTRY_MAPPING = rdf_mappings["country_mapping"]
    TYPE_MAPPING = rdf_mappings["type_mapping"]
    UNIT_MAPPING = rdf_mappings["unit_mapping"]
    # Dict comprehension to ensure safe uppercase key matching
    CATEGORY_MAPPING = {k.upper(): v for k, v in rdf_mappings.get("category_mapping", {}).items()}

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
    graph.bind("code", CODE)
    graph.bind("rdfs", RDFS)
    graph.bind("xsd", XSD)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)
    products_df = con.execute("SELECT * FROM Product").df()
    pro_org_link_df = con.execute("SELECT * FROM ProductOrganisation").df()
    ingredient_df = con.execute("SELECT * FROM ProductIngredient").df()
    prod_cat_df = con.execute("SELECT * FROM ProductProductCategory").df()
    
    # Unify GHS mappings across the 4 newly added reference tables
    ghs_links_query = """
    SELECT product_id, code_id FROM ProductCodeR WHERE code_id IS NOT NULL AND code_id != ''
    UNION ALL
    SELECT product_id, code_id FROM ProductCodeS WHERE code_id IS NOT NULL AND code_id != ''
    UNION ALL
    SELECT product_id, code_id FROM ProductDangerSymbol WHERE code_id IS NOT NULL AND code_id != ''
    UNION ALL
    SELECT product_id, COALESCE(NULLIF(code_id, ''), signal_word_id) as code_id 
    FROM ProductSignalWords 
    WHERE COALESCE(NULLIF(code_id, ''), signal_word_id) IS NOT NULL AND COALESCE(NULLIF(code_id, ''), signal_word_id) != ''
    """
    ghs_df = con.execute(ghs_links_query).df()
    con.close()

    # Pre-process GHS mappings for O(1) lookup
    ghs_dict = {}
    for _, row in ghs_df.iterrows():
        pid = str(row["product_id"]).strip()
        cid = str(row["code_id"]).strip()
        if pid not in ghs_dict:
            ghs_dict[pid] = set()
        ghs_dict[pid].add(cid)

    # Pre-process Organisation links for O(1) lookup
    org_dict = {}
    for _, row in pro_org_link_df.iterrows():
        pid = str(row["product_id"]).strip()
        oid = str(row["organisation_id"]).strip()
        if pid not in org_dict:
            org_dict[pid] = []
        org_dict[pid].append(oid)
        
    # Pre-process Ingredient links for O(1) lookup
    ingredient_dict = {}
    for _, row in ingredient_df.iterrows():
        pid = str(row["product_ref_or_id"]).strip()
        if pid not in ingredient_dict:
            ingredient_dict[pid] = []
        ingredient_dict[pid].append(row)

    # Pre-process Product Categories for O(1) lookup
    cat_dict = {}
    for _, row in prod_cat_df.iterrows():
        pid = str(row["product_id"]).strip()
        cid = str(row["code_id"]).strip().upper()
        if pid not in cat_dict:
            cat_dict[pid] = []
        cat_dict[pid].append(cid)

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
                graph.add((product_uri, RDF.type, BASE.RegularProduct))
                if pd.notna(row.get("w_number")):
                    w_number_str = str(row.get("w_number")).strip()
                    fed_adm_num = f"W-{w_number_str}"
                    graph.add((product_uri, BASE.federalAdmissionNumber, Literal(fed_adm_num, datatype=XSD.string)))

            # Case 2: Sale Permission
            elif raw_type == "SALE_PERMISSION":
                graph.add((product_uri, RDF.type, BASE.SalePermission))
                if pd.notna(row.get("w_number")):
                    w_number_str = str(row.get("w_number")).strip()
                    fed_adm_num = f"W-{w_number_str}"
                    graph.add((product_uri, BASE.federalAdmissionNumber, Literal(fed_adm_num, datatype=XSD.string)))

            # Case 3: Parallel Import
            elif raw_type == "PARALLEL_IMPORT":
                graph.add((product_uri, RDF.type, BASE.ParallelImport))
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

            # Add permission holder
            if product_id_str in org_dict:
                for oid in org_dict[product_id_str]:
                    graph.add((product_uri, BASE.permissionHolder, COMPANY[oid]))

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

            # Add specific product categories from mapping as :productType
            if product_id_str in cat_dict:
                for cat_id in cat_dict[product_id_str]:
                    if cat_id in CATEGORY_MAPPING:
                        cat_uri = CATEGORY_MAPPING[cat_id]
                        graph.add((product_uri, BASE.productType, cat_uri))

            # Add link to reference product
            if pd.notna(row.get("product_ref_or_id")):
                ref_id_str = str(row.get("product_ref_or_id")).strip()
                # Constraint: Only add triple if ID differs from Reference ID
                if product_id_str != ref_id_str:
                    ref_product_uri = PRODUCT[ref_id_str]
                    graph.add((product_uri, BASE.referenceProduct, ref_product_uri))
                    
            # Add ingredients as nested Blank Nodes
            if product_id_str in ingredient_dict:
                for ing_row in ingredient_dict[product_id_str]:
                    substance_id = str(ing_row.get("nk_codetable_substance_id")).strip()
                    if substance_id == "nan" or not substance_id:
                        continue
                    
                    ingredient_node = BNode()
                    graph.add((product_uri, BASE.ingredient, ingredient_node))
                    graph.add((ingredient_node, RDF.type, BASE.Ingredient))
                    graph.add((ingredient_node, BASE.substance, SUBSTANCE[substance_id]))
                    
                    if pd.notna(ing_row.get("in_gram_per_litre")):
                        gpl_node = BNode()
                        graph.add((ingredient_node, BASE.share, gpl_node))
                        graph.add((gpl_node, RDF.type, SCHEMA.QuantitativeValue))
                        graph.add((gpl_node, SCHEMA.value, Literal(float(ing_row.get("in_gram_per_litre")), datatype=XSD.decimal)))
                        graph.add((gpl_node, SCHEMA.unitCode, URIRef(UNIT_MAPPING["gram_per_litre"])))

                    if pd.notna(ing_row.get("in_percent")):
                        pct_node = BNode()
                        graph.add((ingredient_node, BASE.share, pct_node))
                        graph.add((pct_node, RDF.type, SCHEMA.QuantitativeValue))
                        graph.add((pct_node, SCHEMA.value, Literal(float(ing_row.get("in_percent")), datatype=XSD.decimal)))
                        graph.add((pct_node, SCHEMA.unitCode, URIRef(UNIT_MAPPING["percent"])))

            # Add GHS connections
            if product_id_str in ghs_dict:
                for code_id in ghs_dict[product_id_str]:
                    graph.add((product_uri, BASE.ghs, CODE[code_id]))

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