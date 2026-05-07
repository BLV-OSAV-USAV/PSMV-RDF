import os
import sys
import csv
import yaml
import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal, BNode
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
INGREDIENT = namespaces["ingredient"]

# Load all RDF mappings
# Explicitly specify which namespace each mapping uses
namespace_config = {
    "country_mapping": "country",
    "type_mapping": "base",
    "unit_mapping": "unit"
}

rdf_mappings = load_rdf_mappings(namespaces, namespace_map=namespace_config)  

COUNTRY_MAPPING = rdf_mappings["country_mapping"]
TYPE_MAPPING = rdf_mappings["type_mapping"]
UNIT_MAPPING = rdf_mappings["unit_mapping"]

# Create Products
def ingredient_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path: str = "rdf/data/ingredients.ttl"
):
    """
    Creates a ingredients_ttl
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
    graph.bind("ingredient", INGREDIENT)
    
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read Data
    con = duckdb.connect(db_path, read_only=True)
    ingredient_df = con.execute("SELECT * FROM ProductIngredient").df()
    con.close()

    # Create ingredient triples
    for i, row in ingredient_df.iterrows():
        try:
            if pd.isna(row.get("nk_codetable_substance_id")) or pd.isna(row.get("product_ref_or_id")):
                continue
            
            product_id = str(row.get("product_ref_or_id")).strip()
            substance_id = str(row.get("nk_codetable_substance_id")).strip()

            substance_uri = SUBSTANCE[substance_id]
            ingredient_uri = INGREDIENT[f"{product_id}-{substance_id}"]

            # Type ingredient
            graph.add((ingredient_uri, RDF.type, BASE.Ingredient))

            # Link ingredient to substance
            graph.add((ingredient_uri, BASE.substance, substance_uri))

            # Gram per litre
            if pd.notna(row.get("in_gram_per_litre")):
                gpl_uri = INGREDIENT[f"{product_id}-{substance_id}-gpl"]  # named URI
                graph.add((ingredient_uri, BASE.concentration, gpl_uri))
                graph.add((gpl_uri, RDF.type, SCHEMA.QuantitativeValue))
                graph.add((gpl_uri, SCHEMA.value, Literal(float(row.get("in_gram_per_litre")), datatype=XSD.decimal)))
                graph.add((gpl_uri, SCHEMA.unitCode, URIRef(UNIT_MAPPING["gram_per_litre"])))

            # Percent
            if pd.notna(row.get("in_percent")):
                pct_uri = INGREDIENT[f"{product_id}-{substance_id}-pct"]  # named URI
                graph.add((ingredient_uri, BASE.concentration, pct_uri))
                graph.add((pct_uri, RDF.type, SCHEMA.QuantitativeValue))
                graph.add((pct_uri, SCHEMA.value, Literal(float(row.get("in_percent")), datatype=XSD.decimal)))
                graph.add((pct_uri, SCHEMA.unitCode, URIRef(UNIT_MAPPING["percent"])))

        except Exception as error:
            print(f"Row {i} (Substance {ingredient_uri}): {error}")

    # Print graph info
    print(f"[i] Total triples: {len(graph)}")

    # Save to file
    out_path_obj = Path(out_path)
    out_path_obj.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=out_path_obj, format="turtle")
    print(f"\nSaved to `{out_path_obj}`")
    return graph

if __name__ == "__main__":
    ingredient_ttl()