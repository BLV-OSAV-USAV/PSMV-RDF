import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF
from rdflib.namespace import NamespaceManager

# local imports
from src.python.utils.helper_functions import load_namespaces, ensure_indication, add_lang_labels, group_to_dict

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
    XSD = namespaces["xsd"]
    
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
    obl_df         = con.execute("SELECT * FROM IndicationObligationLink").df()
    app_area_df    = con.execute("SELECT * FROM ApplicationAreaLink").df()
    app_comment_df = con.execute("SELECT * FROM ApplicationCommentLink").df()
    
    ind_measure_df  = con.execute("SELECT * FROM IndicationMeasureCode").df()
    ind_time_measure_df = con.execute("SELECT * FROM IndicationTimeMeasureCode").df()
    ind_clt_df = con.execute("SELECT * FROM IndicationCultureCode").df()
    ind_clt_frm_df = con.execute("SELECT * FROM IndicationCultureFormCode").df()
    ind_obl_df = con.execute("SELECT * FROM IndicationObligationCode").df()
    ind_pst = con.execute("SELECT * FROM IndicationPestCode").df()
    
    # Map Indication -> Product
    seen_indications = set()
    df = (
        prod_ind_df
        .dropna(subset=["product_ref_or_id", "indication"])
        [["product_ref_or_id", "indication"]]
        .astype(str)
        .apply(lambda c: c.str.strip())
    )
    df = df[
        (df["product_ref_or_id"] != "") & (df["indication"] != "")
    ].drop_duplicates()

    ind_uri_map  = {ind_id: ensure_indication(graph, seen_indications, ind_id, INDICATION, BASE) for ind_id in df["indication"].unique()}
    prod_uri_map = {pid: PRODUCT[pid] for pid in df["product_ref_or_id"].unique()}

    triples = [
        (ind_uri_map[ind_id], BASE.product, prod_uri_map[prod_id], graph)
        for prod_id, ind_id in zip(df["product_ref_or_id"], df["indication"])
    ]
    graph.addN(triples)

    link_configs = [
    (cult_df,        "culture_id",              "crop",               CROP),
    (obl_df,         "indication_obligation_id", "obligation",         CODE),
    (app_area_df,    "application_area_id",      "applicationArea",    CODE),
    (app_comment_df, "application_comment_id",   "applicationComment", CODE),
    ]

    # Crop, Obligation, Area, Comment
    for df_link, id_col, predicate_name, ns in link_configs:
        predicate = BASE[predicate_name]
        pairs = (
            df_link.dropna(subset=["indication", id_col])
            [["indication", id_col]]
            .astype(str)
            .apply(lambda c: c.str.strip())
        )
        pairs = pairs[(pairs["indication"] != "") & (pairs[id_col] != "")].drop_duplicates()
        for _, row in pairs.iterrows():
            ind_uri = ensure_indication(graph, seen_indications, row["indication"], INDICATION, BASE)
            graph.add((ind_uri, predicate, ns[row[id_col]]))

    # Create indication triples
    measure_dict       = group_to_dict(ind_measure_df, "indication")
    time_measure_dict  = group_to_dict(ind_time_measure_df, "indication")
    indication_pest_dict = group_to_dict(ind_pst, "indication")

    # Create indication triples
    
    for i, indication_id_str in enumerate(sorted(seen_indications)):
        try:
            if not indication_id_str:
                continue

            indication_uri = INDICATION[indication_id_str]

            # Add Identifier
            graph.add((
                indication_uri,
                SCHEMA.identifier,
                Literal(indication_id_str, datatype=XSD.string)
            ))

            # Measure
            if indication_id_str in measure_dict:
                for m_row in measure_dict[indication_id_str]:
                    measure_node = BNode()

                    graph.add((indication_uri, BASE.measure, measure_node))
                    graph.add((measure_node, RDF.type, BASE.Measure))

                    add_lang_labels(graph, measure_node, SCHEMA.name, m_row)

            # Time Measure
            if indication_id_str in time_measure_dict:
                for mt_row in time_measure_dict[indication_id_str]:
                    time_measure_node = BNode()

                    graph.add((indication_uri, BASE.timeMeasure, time_measure_node))
                    graph.add((time_measure_node, RDF.type, BASE.TimeMeasure))

                    add_lang_labels(graph, measure_node, SCHEMA.name, m_row)

            # Pest Type
            if indication_id_str in indication_pest_dict:
                for pest_row in indication_pest_dict[indication_id_str]:
                    if pd.isna(pest_row.get("indication_pest_id")):
                        continue

                    pest_id = str(pest_row["indication_pest_id"]).strip()

                    if not pest_id:
                        continue

                    rel_node = BNode()

                    graph.add((indication_uri, BASE.indicationPest, rel_node))
                    graph.add((rel_node, RDF.type, BASE.IndicationPest))
                    graph.add((rel_node, BASE.pest, PEST[pest_id]))

                    if pd.notna(pest_row.get("pest_type")) and str(pest_row.get("pest_type")).strip():
                        graph.add((
                            rel_node,
                            BASE.pestType,
                            Literal(str(pest_row["pest_type"]).strip(), datatype=XSD.string)
                        ))

        except Exception as error:
            print(f"Indication row {i} ({indication_id_str or 'unknown'}): {error}")

    print(f"[i] Total indication triples: {len(graph)}")

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    indication_ttl()