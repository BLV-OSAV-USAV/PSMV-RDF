# src/python/create_application_area_ttl.py

import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF

# local imports
from src.python.utils.helper_functions import load_namespaces, add_lang_labels

def application_area_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/application_areas.ttl"
):
    """
    Creates an application_areas_ttl graph extracting ApplicationArea entities from the ApplicationAreaCode table.
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    XSD = namespaces["xsd"]
    
    # Fallback instantiation if explicitly missing in namespaces.yaml
    CODE = namespaces.get("code", Namespace(str(BASE) + "code/"))

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("code", CODE)
    graph.bind("xsd", XSD)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)
    
    try:
        app_area_df = con.execute("SELECT * FROM ApplicationAreaCode").df()
    except Exception as e:
        print(f"[!] Could not read ApplicationAreaCode ({e}).")
        app_area_df = pd.DataFrame()
        
    # As a fallback for the letters, we can also query the ApplicationArea link table and join it,
    # but only if code_value is empty.
    try:
        link_df = con.execute("SELECT * FROM ApplicationArea").df()
        
        # Find the correct column for code_id
        if 'application_area_id' in link_df.columns:
            link_df['link_code_id'] = link_df['application_area_id']
        elif 'NK_Codetable' in link_df.columns:
            link_df['link_code_id'] = link_df['NK_Codetable']
        elif 'nk_codetable' in link_df.columns:
            link_df['link_code_id'] = link_df['nk_codetable']
            
        # Find the correct column for code_value
        if 'short_name' in link_df.columns:
            link_df['link_code_value'] = link_df['short_name']
        elif 'SHORT_NAME' in link_df.columns:
            link_df['link_code_value'] = link_df['SHORT_NAME']
            
        if 'link_code_id' in link_df.columns and 'link_code_value' in link_df.columns:
            link_df = link_df[['link_code_id', 'link_code_value']].rename(columns={'link_code_id': 'code_id'}).drop_duplicates()
            if not app_area_df.empty:
                app_area_df = pd.merge(app_area_df, link_df, on='code_id', how='left')
                if 'code_value' in app_area_df.columns:
                    app_area_df['code_value'] = app_area_df['code_value'].fillna(app_area_df['link_code_value'])
                else:
                    app_area_df['code_value'] = app_area_df['link_code_value']
            else:
                app_area_df = link_df.rename(columns={'link_code_value': 'code_value'})
    except Exception as e:
        print(f"[i] Could not join link table for short names: {e}")
        
    con.close()

    # Create application area triples
    for i, row in app_area_df.iterrows():
        code_id = None
        try:
            if pd.isna(row.get("code_id")) or not str(row.get("code_id")).strip():
                print(f"Application area row {i}: missing code_id -> skipped")
                continue

            code_id = str(row["code_id"]).strip().lower()
            area_uri = CODE[code_id]

            # Add Type
            graph.add((area_uri, RDF.type, BASE.ApplicationArea))
            
            # Add Identifier (CODE_VALUE) - The letter identifier
            if 'code_value' in row and pd.notna(row.get("code_value")):
                code_val = str(row["code_value"]).strip()
                if code_val:
                    graph.add((area_uri, SCHEMA.identifier, Literal(code_val)))

            # Add language-tagged Names
            has_name = False
            if 'DE' in row and pd.notna(row.get("DE")) and str(row.get("DE")).strip():
                graph.add((area_uri, SCHEMA.name, Literal(str(row["DE"]).strip(), lang="de")))
                has_name = True
            if 'EN' in row and pd.notna(row.get("EN")) and str(row.get("EN")).strip():
                graph.add((area_uri, SCHEMA.name, Literal(str(row["EN"]).strip(), lang="en")))
                has_name = True
            if 'FR' in row and pd.notna(row.get("FR")) and str(row.get("FR")).strip():
                graph.add((area_uri, SCHEMA.name, Literal(str(row["FR"]).strip(), lang="fr")))
                has_name = True
            if 'IT' in row and pd.notna(row.get("IT")) and str(row.get("IT")).strip():
                graph.add((area_uri, SCHEMA.name, Literal(str(row["IT"]).strip(), lang="it")))
                has_name = True
                
            # Fallback: If no translation is matched, enforce the letter as schema:name
            if not has_name and 'code_value' in row and pd.notna(row.get("code_value")):
                code_val = str(row["code_value"]).strip()
                if code_val:
                    graph.add((area_uri, SCHEMA.name, Literal(code_val, datatype=XSD.string)))

        except Exception as error:
            print(f"Application area row {i} ({code_id or 'unknown'}): {error}")

    # Print graph info
    print(f"[i] Total application area triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    application_area_ttl()