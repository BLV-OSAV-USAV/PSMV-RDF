import duckdb
from pathlib import Path

import pandas as pd
from rdflib import Graph, Namespace, Literal, BNode
from rdflib.namespace import RDF

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
    graph.bind("xsd", XSD)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)

    prod_ind_df = con.execute("SELECT * FROM ProductIndication").df()
    cult_df = con.execute("SELECT * FROM IndicationCultureLink").df()
    obl_df = con.execute("SELECT * FROM IndicationObligationLink").df()
    app_area_df = con.execute("SELECT * FROM ApplicationAreaLink").df()
    app_comment_df = con.execute("SELECT * FROM ApplicationCommentLink").df()

    ind_measure_df = con.execute("SELECT * FROM IndicationMeasureCode").df()
    ind_time_measure_df = con.execute("SELECT * FROM IndicationTimeMeasureCode").df()
    ind_pst = con.execute("SELECT * FROM IndicationPestCode").df()

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
        if pd.isna(row.get("product_ref_or_id")) or pd.isna(row.get("product_indicator")):
            continue

        prod_id = str(row["product_ref_or_id"]).strip()
        ind_id = str(row["product_indicator"]).strip()

        if prod_id and ind_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((PRODUCT[prod_id], BASE.indication, ind_uri))

    # Map Indication -> Crop
    for _, row in cult_df.iterrows():
        if pd.isna(row.get("indication")) or pd.isna(row.get("culture_id")):
            continue

        ind_id = str(row["indication"]).strip()
        cult_id = str(row["culture_id"]).strip()

        if ind_id and cult_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.crop, CROP[cult_id]))

    # Map Indication -> Obligation
    for _, row in obl_df.iterrows():
        if pd.isna(row.get("indication")) or pd.isna(row.get("indication_obligation_id")):
            continue

        ind_id = str(row["indication"]).strip()
        obl_id = str(row["indication_obligation_id"]).strip()

        if ind_id and obl_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.obligation, CODE[obl_id]))

    # Map Indication -> Application Area
    for _, row in app_area_df.iterrows():
        if pd.isna(row.get("indication")) or pd.isna(row.get("application_area_id")):
            continue

        ind_id = str(row["indication"]).strip()
        area_id = str(row["application_area_id"]).strip()

        if ind_id and area_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.applicationArea, CODE[area_id]))

    # Map Indication -> Application Comment
    for _, row in app_comment_df.iterrows():
        if pd.isna(row.get("indication")) or pd.isna(row.get("application_comment_id")):
            continue

        ind_id = str(row["indication"]).strip()
        comment_id = str(row["application_comment_id"]).strip()

        if ind_id and comment_id:
            ind_uri = ensure_indication(ind_id)
            graph.add((ind_uri, BASE.applicationComment, CODE[comment_id]))

    # Pre-process Measure links for O(1) lookup
    measure_dict = {}
    for _, row in ind_measure_df.iterrows():
        if pd.isna(row.get("indication")):
            continue

        ind_id = str(row["indication"]).strip()

        if ind_id:
            measure_dict.setdefault(ind_id, []).append(row)

    # Pre-process Time Measure links for O(1) lookup
    time_measure_dict = {}
    for _, row in ind_time_measure_df.iterrows():
        if pd.isna(row.get("indication")):
            continue

        ind_id = str(row["indication"]).strip()

        if ind_id:
            time_measure_dict.setdefault(ind_id, []).append(row)

    # Pre-process Pest links for O(1) lookup
    indication_pest_dict = {}
    for _, row in ind_pst.iterrows():
        if pd.isna(row.get("indication")):
            continue

        ind_id = str(row["indication"]).strip()

        if ind_id:
            indication_pest_dict.setdefault(ind_id, []).append(row)

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

                    if pd.notna(m_row.get("EN")) and str(m_row.get("EN")).strip():
                        graph.add((measure_node, SCHEMA.name, Literal(str(m_row["EN"]).strip(), lang="en")))
                    if pd.notna(m_row.get("DE")) and str(m_row.get("DE")).strip():
                        graph.add((measure_node, SCHEMA.name, Literal(str(m_row["DE"]).strip(), lang="de")))
                    if pd.notna(m_row.get("FR")) and str(m_row.get("FR")).strip():
                        graph.add((measure_node, SCHEMA.name, Literal(str(m_row["FR"]).strip(), lang="fr")))
                    if pd.notna(m_row.get("IT")) and str(m_row.get("IT")).strip():
                        graph.add((measure_node, SCHEMA.name, Literal(str(m_row["IT"]).strip(), lang="it")))

            # Time Measure
            if indication_id_str in time_measure_dict:
                for mt_row in time_measure_dict[indication_id_str]:
                    time_measure_node = BNode()

                    graph.add((indication_uri, BASE.timeMeasure, time_measure_node))
                    graph.add((time_measure_node, RDF.type, BASE.TimeMeasure))

                    if pd.notna(mt_row.get("EN")) and str(mt_row.get("EN")).strip():
                        graph.add((time_measure_node, SCHEMA.name, Literal(str(mt_row["EN"]).strip(), lang="en")))
                    if pd.notna(mt_row.get("DE")) and str(mt_row.get("DE")).strip():
                        graph.add((time_measure_node, SCHEMA.name, Literal(str(mt_row["DE"]).strip(), lang="de")))
                    if pd.notna(mt_row.get("FR")) and str(mt_row.get("FR")).strip():
                        graph.add((time_measure_node, SCHEMA.name, Literal(str(mt_row["FR"]).strip(), lang="fr")))
                    if pd.notna(mt_row.get("IT")) and str(mt_row.get("IT")).strip():
                        graph.add((time_measure_node, SCHEMA.name, Literal(str(mt_row["IT"]).strip(), lang="it")))

            # Pest Type
            if indication_id_str in indication_pest_dict:
                for pest_row in indication_pest_dict[indication_id_str]:
                    if pd.isna(pest_row.get("indication_pest_id")):
                        continue

                    pest_id = str(pest_row["indication_pest_id"]).strip()

                    if not pest_id:
                        continue

                    pest_type = ""
                    if pd.notna(pest_row.get("pest_type")) and str(pest_row.get("pest_type")).strip():
                        pest_type = str(pest_row["pest_type"]).strip().upper()
                    if pest_type == "PEST_FULL_EFFECT":
                        graph.add((indication_uri, BASE.pestFullEffect, PEST[pest_id]))
                    elif pest_type == "PEST_PARTIAL_EFFECT":
                        graph.add((indication_uri, BASE.pestPartialEffect, PEST[pest_id]))
                    elif pest_type == "PEST_SIDE_EFFECT":
                        graph.add((indication_uri, BASE.pestSideEffect, PEST[pest_id]))
                    else:
                        graph.add((indication_uri, BASE.pest, PEST[pest_id]))

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