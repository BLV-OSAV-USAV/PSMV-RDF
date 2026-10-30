import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF
from rdflib.namespace import NamespaceManager

# local imports
from src.python.utils.helper_functions import load_namespaces, ensure_indication, add_lang_labels, group_to_dict, load_unit_map

def indication_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/indications.ttl"
):
    """
    Creates an indications.ttl graph linking products, crops, pests,
    obligations, application areas, application comments, and crops
    and pests with additional texts.
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
    UNIT = namespaces.get("unit", Namespace(str(BASE) + "unit/"))
    CROPADDTEXT = namespaces.get("cropaddtext", Namespace(str(BASE) + "cropaddtext/"))
    PESTADDTEXT = namespaces.get("pestaddtext", Namespace(str(BASE) + "pestaddtext/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("product", PRODUCT)
    graph.bind("indication", INDICATION)
    graph.bind("crop", CROP)
    graph.bind("pest", PEST)
    graph.bind("code", CODE)
    graph.bind("unit", UNIT)
    graph.bind("cropaddtext", CROPADDTEXT)
    graph.bind("pestaddtext", PESTADDTEXT)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)

    prod_ind_df = con.execute("SELECT * FROM ProductIndicationExpanded").df()
    cult_df = con.execute("SELECT * FROM IndicationCultureLink").df()
    obl_df = con.execute("SELECT * FROM IndicationObligationLink").df()
    app_area_df = con.execute("SELECT * FROM ApplicationAreaLink").df()
    app_comment_df = con.execute("SELECT * FROM ApplicationCommentLink").df()
    
    ind_measure_df  = con.execute("SELECT * FROM IndicationMeasureCode").df()
    ind_time_measure_df = con.execute("SELECT * FROM IndicationTimeMeasureCode").df()
    ind_clt_df = con.execute("SELECT * FROM IndicationCultureCode").df()
    ind_clt_frm_df = con.execute("SELECT * FROM IndicationCultureFormCode").df()
    ind_obl_df = con.execute("SELECT * FROM IndicationObligationCode").df()
    ind_pst = con.execute("SELECT * FROM IndicationPestCode").df()
    valid_text_ids = set(con.execute("SELECT code_id FROM AdditionalTextCode").df()["code_id"])

    # Load Unit map
    UNIT_MAP = load_unit_map(UNIT)

    # Map Indication -> Product
    seen_indications = set()
    df = (
        prod_ind_df
        .dropna(subset=["product_ref_or_id", "indication"])
        [["product_ref_or_id", "indication"]]
        .astype(str)
        .apply(lambda c: c.str.strip().str.lower())
    )
    df = df[
        (df["product_ref_or_id"] != "") & (df["indication"] != "")
    ].drop_duplicates()

    ind_uri_map  = {ind_id: ensure_indication(graph, seen_indications, ind_id, INDICATION, BASE) for ind_id in df["indication"].unique()}
    # Only indications linked to a product are published
    valid_indications = set(df["indication"])
    prod_uri_map = {pid: PRODUCT[pid] for pid in df["product_ref_or_id"].unique()}

    triples = [
        (ind_uri_map[ind_id], BASE.product, prod_uri_map[prod_id], graph)
        for prod_id, ind_id in zip(df["product_ref_or_id"], df["indication"])
    ]
    graph.addN(triples)

    link_configs = [
    (cult_df,"culture_id","crop", CROP),
    (obl_df,"indication_obligation_id", "obligation", CODE),
    (app_area_df,"application_area_id", "applicationArea",CODE),
    (app_comment_df, "application_comment_id", "applicationComment", CODE),
    ]

    # Map Indication -> Crop, Obligation, Area, Comment
    for df_link, id_col, predicate_name, ns in link_configs:
        predicate = BASE[predicate_name]
        pairs = (
            df_link.dropna(subset=["indication", id_col])
            [["indication", id_col]]
            .astype(str)
            .apply(lambda c: c.str.strip().str.lower())
        )
        pairs = pairs[(pairs["indication"] != "") & (pairs[id_col] != "")].drop_duplicates()
        orphans = set(pairs["indication"]) - valid_indications
        if orphans:
            print(f"[!] {predicate_name}: {len(orphans)} indication(s) without product -> skipped")
        pairs = pairs[pairs["indication"].isin(valid_indications)]
        for _, row in pairs.iterrows():
            ind_uri = ensure_indication(graph, seen_indications, row["indication"], INDICATION, BASE)
            graph.add((ind_uri, predicate, ns[row[id_col]]))

    # Map Indication -> Crop with additional text
    crop_text_cols = ["indication", "culture_id", "codetable_culture_additional_text"]
    crop_text_pairs = (
        ind_clt_df.dropna(subset=crop_text_cols)
        [crop_text_cols]
        .astype(str)
        .apply(lambda c: c.str.strip().str.lower())
        .drop_duplicates()
    )
    for _, row in crop_text_pairs.iterrows():
        text_id = row["codetable_culture_additional_text"]
        if text_id not in valid_text_ids:
            print(f"Indication {row['indication']}: unknown crop additional text {text_id} -> skipped")
            continue
        ind_uri = ensure_indication(graph, seen_indications, row["indication"], INDICATION, BASE)
        q_uri = URIRef(f"{ind_uri}/crop/{row['culture_id']}/{text_id}")
        graph.add((ind_uri, BASE.cropWithAdditionalText, q_uri))
        graph.add((q_uri, RDF.type, BASE.CropWithAdditionalText))
        graph.add((q_uri, BASE.crop, CROP[row["culture_id"]]))
        graph.add((q_uri, BASE.additionalText, CROPADDTEXT[text_id]))

    # Create indication triples
    measure_dict = group_to_dict(ind_measure_df, "indication")
    time_measure_dict  = group_to_dict(ind_time_measure_df, "indication")
    indication_pest_dict = group_to_dict(ind_pst, "indication")
    
    dosage_cols = ["indication", "dosage_from", "dosage_to", "expenditure_from", "expenditure_to", "waiting_period"]
    dosage_dict = group_to_dict(
        prod_ind_df[dosage_cols].drop_duplicates(),
        "indication"
    )

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

            # Pest Type
            if indication_id_str in indication_pest_dict:
                for pest_row in indication_pest_dict[indication_id_str]:
                    if pd.isna(pest_row.get("indication_pest_id")):
                        continue

                    pest_id = str(pest_row["indication_pest_id"]).strip().lower()

                    if not pest_id:
                        continue

                    raw_effect = pest_row.get("pest_type")
                    if pd.notna(raw_effect) and str(raw_effect).strip():
                        pest_effect_slug = str(raw_effect).strip().upper().replace(" ", "_")
                        pest_predicate = {
                            "PEST_FULL_EFFECT": BASE.fullEffect,
                            "PEST_SIDE_EFFECT": BASE.sideEffect,
                            "PEST_PARTIAL_EFFECT": BASE.partialEffect,
                        }.get(pest_effect_slug, BASE.pest)
                    else:
                        pest_predicate = BASE.pest

                    graph.add((indication_uri, pest_predicate, PEST[pest_id]))

                    # Add Pest with additional text
                    raw_text = pest_row.get("additional_text")
                    if pd.notna(raw_text) and str(raw_text).strip():
                        text_id = str(raw_text).strip().lower()
                        if text_id in valid_text_ids:
                            q_uri = URIRef(f"{indication_uri}/pest/{pest_id}/{text_id}")
                            graph.add((indication_uri, BASE.pestWithAdditionalText, q_uri))
                            graph.add((q_uri, RDF.type, BASE.PestWithAdditionalText))
                            graph.add((q_uri, BASE.pest, PEST[pest_id]))
                            graph.add((q_uri, BASE.additionalText, PESTADDTEXT[text_id]))
                        else:
                            print(f"Pest {pest_id}: unknown pest additional text {text_id} -> skipped")

            # Dosage / Expenditure / Waiting Period
            if indication_id_str in dosage_dict:
                m_rows = measure_dict.get(indication_id_str, [])
                unit_str = m_rows[0].get("DE") or m_rows[0].get("EN") if m_rows else None

                unit_uri = UNIT_MAP.get(unit_str) if unit_str else None

                # time-measure lookup (Days / Week(s)) for waiting period unit
                t_rows = time_measure_dict.get(indication_id_str, [])
                time_unit_str = t_rows[0].get("EN") if t_rows else None
                time_unit_uri = UNIT_MAP.get(time_unit_str, UNIT.DAY)

                for d_row in dosage_dict[indication_id_str]:

                    # Dosage
                    v_dosage_from = d_row.get("dosage_from")
                    v_dosage_to   = d_row.get("dosage_to")

                    if pd.notna(v_dosage_from) or pd.notna(v_dosage_to):
                        dosage_node = BNode()
                        graph.add((indication_uri, BASE.dosage, dosage_node))
                        graph.add((dosage_node, RDF.type, SCHEMA.QuantitativeValue))
                        if pd.notna(v_dosage_from):
                            graph.add((dosage_node, SCHEMA.minValue, Literal(float(v_dosage_from), datatype=XSD.decimal)))
                        if pd.notna(v_dosage_to):
                            graph.add((dosage_node, SCHEMA.maxValue, Literal(float(v_dosage_to), datatype=XSD.decimal)))
                        if unit_str:
                            graph.add((dosage_node, SCHEMA.unitText, Literal(unit_str)))
                        if unit_uri:
                            graph.add((dosage_node, SCHEMA.unitCode, unit_uri))

                    # Expenditure
                    e_from = d_row.get("expenditure_from")
                    e_to   = d_row.get("expenditure_to")
                    if pd.notna(e_from) or pd.notna(e_to):
                        exp_node = BNode()
                        graph.add((indication_uri, BASE.expenditure, exp_node))
                        graph.add((exp_node, RDF.type, SCHEMA.QuantitativeValue))
                        if pd.notna(e_from):
                            graph.add((exp_node, SCHEMA.minValue, Literal(float(e_from), datatype=XSD.decimal)))
                        if pd.notna(e_to):
                            graph.add((exp_node, SCHEMA.maxValue, Literal(float(e_to), datatype=XSD.decimal)))
                        if unit_str:
                            graph.add((exp_node, SCHEMA.unitText, Literal(unit_str)))
                        if unit_uri:
                            graph.add((exp_node, SCHEMA.unitCode, unit_uri))

                    # Waiting Period
                    wp = d_row.get("waiting_period")
                    if pd.notna(wp) and str(wp).strip():
                        wp_node = BNode()
                        graph.add((indication_uri, BASE.waitingPeriod, wp_node))
                        graph.add((wp_node, RDF.type, SCHEMA.QuantitativeValue))
                        graph.add((wp_node, SCHEMA.value, Literal(int(float(wp)), datatype=XSD.integer)))
                        graph.add((wp_node, SCHEMA.unitCode, time_unit_uri))

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