import os
import sys
import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF
from rdflib.namespace import NamespaceManager

# local imports
from src.python.utils.helper_functions import load_namespaces

def indication_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/indications.ttl"
):
    """
    Creates an indications.ttl graph linking products, crops, pests, 
    obligations, application areas, and application comments.
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    PRODUCT = namespaces["product"]
    SCHEMA = namespaces["schema"]
    
    # Fallback instantiations if explicitly missing in namespaces.yaml
    INDICATION = namespaces.get("indication", Namespace(str(BASE) + "indication/"))
    CROP = namespaces.get("crop", Namespace(str(BASE) + "crop/"))
    PEST = namespaces.get("pest", Namespace(str(BASE) + "pest/"))
    CODE = namespaces.get("code", Namespace(str(BASE) + "code/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("product", PRODUCT)
    graph.bind("indication", INDICATION)
    graph.bind("crop", CROP)
    graph.bind("pest", PEST)
    graph.bind("code", CODE)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)
    
    prod_ind_df    = con.execute("SELECT * FROM ProductIndication").df()
    cult_df        = con.execute("SELECT * FROM IndicationCultureLink").df()
    pest_df        = con.execute("SELECT * FROM IndicationPestLink").df()
    obl_df         = con.execute("SELECT * FROM IndicationObligationLink").df()
    app_area_df    = con.execute("SELECT * FROM ApplicationAreaLink").df()
    app_comment_df = con.execute("SELECT * FROM ApplicationCommentLink").df()

    con.close()

    # Ensure indication
    seen_indications = set()

    def ensure_indication(ind_id):
        """Helper to ensure the Indication node is declared only once."""
        if ind_id not in seen_indications:
            ind_uri = INDICATION[ind_id]
            graph.add((ind_uri, RDF.type, BASE.Indication))
            seen_indications.add(ind_id)
        return INDICATION[ind_id]

    # Map Product -> Indication
    for _, row in prod_ind_df.iterrows():
        prod_id = str(row["product_ref_or_id"]).strip()
        ind_id = str(row["product_indicator"]).strip()
        if prod_id and ind_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((PRODUCT[prod_id], BASE.indication, ind_uri))

    # Map Indication -> Crop
    for _, row in cult_df.iterrows():
        ind_id = str(row["indication"]).strip()
        cult_id = str(row["culture_id"]).strip()
        if ind_id and cult_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.crop, CROP[cult_id]))

    # Map Indication -> Pest
    for _, row in pest_df.iterrows():
        ind_id = str(row["indication"]).strip()
        pest_id = str(row["indication_pest_id"]).strip()
        if ind_id and pest_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.pest, PEST[pest_id]))

    # Map Indication -> Obligation
    for _, row in obl_df.iterrows():
        ind_id = str(row["indication"]).strip()
        obl_id = str(row["indication_obligation_id"]).strip()
        if ind_id and obl_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.obligation, CODE[obl_id]))

    # Map Indication -> Application Area
    for _, row in app_area_df.iterrows():
        ind_id = str(row["indication"]).strip()
        area_id = str(row["application_area_id"]).strip()
        if ind_id and area_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.applicationArea, CODE[area_id]))

    # Map Indication -> Application Comment
    for _, row in app_comment_df.iterrows():
        ind_id = str(row["indication"]).strip()
        comment_id = str(row["application_comment_id"]).strip()
        if ind_id and comment_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.applicationComment, CODE[comment_id]))

    print(f"[i] Total indication triples: {len(graph)}")

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    indication_ttl()