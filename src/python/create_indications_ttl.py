import os
import sys
import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal, BNode
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
    
    prod_ind_df   = con.execute("SELECT * FROM ProductIndicationExpanded").df()
    cult_df        = con.execute("SELECT * FROM IndicationCultureLink").df()
    #pest_df        = con.execute("SELECT * FROM IndicationPestLink").df()
    obl_df         = con.execute("SELECT * FROM IndicationObligationLink").df()
    app_area_df    = con.execute("SELECT * FROM ApplicationAreaLink").df()
    app_comment_df = con.execute("SELECT * FROM ApplicationCommentLink").df()
    
    ind_measure_df  = con.execute("SELECT * FROM IndicationMeasureCode").df()
    ind_time_masure_df = con.execute("SELECT * FROM IndicationTimeMeasureCode").df()
    ind_clt_df = con.execute("SELECT * FROM IndicationCultureCode").df()
    ind_clt_frm_df = con.execute("SELECT * FROM IndicationCultureFormCode").df()
    ind_obl_df = con.execute("SELECT * FROM IndicationObligationCode").df()
    ind_pst = con.execute("SELECT * FROM IndicationPestCode").df()
    
    print(prod_ind_df.columns)
    print(prod_ind_df.head(10))
    #print(pest_df.head(10))
    #ind_pst.to_csv("ind_pst.csv", index=False)
    #ind_time_masure_df.to_csv("ind_time_masure_df.csv", index=False)
    #ind_clt_df.to_csv("ind_clt_df.csv", index=False)
    #ind_clt_obl_df.to_csv("ind_clt_obl_df.csv", index=False)

    # Ensure indication
    seen_indications = set()

    def ensure_indication(ind_id):
        """Helper to ensure the Indication node is declared only once."""
        if ind_id not in seen_indications:
            ind_uri = INDICATION[ind_id]
            graph.add((ind_uri, RDF.type, BASE.Indication))
            seen_indications.add(ind_id)
        return INDICATION[ind_id]

    # Map Indication -> Product
    for _, row in prod_ind_df.iterrows():
        prod_id = str(row["product_ref_or_id"]).strip()
        ind_id = str(row["linked_product_indication"]).strip()

        if prod_id and ind_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.product, PRODUCT[prod_id]))

    # Map Indication -> Crop
    for _, row in cult_df.iterrows():
        ind_id = str(row["indication"]).strip()
        cult_id = str(row["culture_id"]).strip()
        if ind_id and cult_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.crop, CROP[cult_id]))

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

   # Create indication triples
    all_indications = pd.DataFrame(list(seen_indications), columns=["indication"])
    for i, row in all_indications.iterrows():
        try: 
            if pd.isna(row.get("indication")):
                continue
            
            # Add Identifier
            indication_id_str = str(row.get("indication")).strip()
            indication_uri = INDICATION[indication_id_str]
            graph.add((indication_uri, SCHEMA.identifier, Literal(indication_id_str)))

            # Measure
            match = ind_measure_df[ind_measure_df["indication"].astype(str).str.strip() == indication_id_str]

            if not match.empty:
                m_row = match.iloc[0]
                measure_node = BNode()
                graph.add((indication_uri, BASE.Measure, measure_node))
                graph.add((measure_node, RDF.type, BASE.Measure))

                if pd.notna(m_row.get("EN")): 
                    graph.add((measure_node, SCHEMA.name, Literal(str(m_row["EN"]).strip(), lang="en")))
                if pd.notna(m_row.get("DE")): 
                    graph.add((measure_node, SCHEMA.name, Literal(str(m_row["DE"]).strip(), lang="de")))
                if pd.notna(m_row.get("FR")): 
                    graph.add((measure_node, SCHEMA.name, Literal(str(m_row["FR"]).strip(), lang="fr")))
                if pd.notna(m_row.get("IT")): 
                    graph.add((measure_node, SCHEMA.name, Literal(str(m_row["IT"]).strip(), lang="it")))


            # Time Measure
            match_time = ind_time_masure_df[ind_time_masure_df["indication"].astype(str).str.strip() == indication_id_str]

            if not match_time.empty:
                mt_row = match_time.iloc[0]
                time_measure_node = BNode()
                graph.add((indication_uri, BASE.TimeMeasure, time_measure_node)) 
                graph.add((time_measure_node, RDF.type, BASE.TimeMeasure))

                if pd.notna(mt_row.get("EN")): 
                    graph.add((time_measure_node, SCHEMA.name, Literal(str(mt_row["EN"]).strip(), lang="en")))
                if pd.notna(mt_row.get("DE")): 
                    graph.add((time_measure_node, SCHEMA.name, Literal(str(mt_row["DE"]).strip(), lang="de")))
                if pd.notna(mt_row.get("FR")): 
                    graph.add((time_measure_node, SCHEMA.name, Literal(str(mt_row["FR"]).strip(), lang="fr")))
                if pd.notna(mt_row.get("IT")): 
                    graph.add((time_measure_node, SCHEMA.name, Literal(str(mt_row["IT"]).strip(), lang="it")))


            # Pest Type 
            pest_matches = ind_pst[ind_pst["indication"].astype(str).str.strip() == indication_id_str]

            for _, pest_row in pest_matches.iterrows():
                pest_id = str(pest_row.get("indication_pest_id", "")).strip()
                if not pest_id or pest_id.lower() == "nan":
                    continue

                pest_uri = PEST[pest_id]

                rel_node = BNode()
                graph.add((indication_uri, BASE.indicationPest, rel_node))
                graph.add((rel_node, RDF.type, BASE.IndicationPest))
                graph.add((rel_node, BASE.pest, pest_uri))

                pest_type = pest_row.get("pest_type")
                if pd.notna(pest_type):
                    graph.add((rel_node, BASE.pestType, Literal(str(pest_type).strip())))

        except Exception as error:
            print(f"Row {i} (INDICATION {indication_id_str}): {error}")


    print(f"[i] Total indication triples: {len(graph)}")

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    indication_ttl()