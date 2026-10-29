import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF

# local imports
from src.python.utils.helper_functions import load_namespaces, add_lang_labels

def additional_texts_ttl(
    db_path="data/processed/psmv-data.duckdb",
    out_path="rdf/data/additional_texts.ttl"
):
    """
    Creates an additional_texts_ttl graph extracting CropAdditionalText and
    PestAdditionalText entities from the CodeEnriched table.
    """
    # Set namespaces
    namespaces = load_namespaces()
    
    BASE = namespaces["base"]
    SCHEMA = namespaces["schema"]
    XSD = namespaces["xsd"]
    
    # Fallback instantiation if they are not explicitly present in namespaces.yaml
    CROPADDTEXT = namespaces.get("cropaddtext", Namespace(str(BASE) + "cropaddtext/"))
    PESTADDTEXT = namespaces.get("pestaddtext", Namespace(str(BASE) + "pestaddtext/"))

    # Map text_key to namespace and class
    text_types = {
        "CultureAdditionalText": (CROPADDTEXT, BASE.CropAdditionalText),
        "PestAdditionalText": (PESTADDTEXT, BASE.PestAdditionalText),
    }

    # Create empty graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("", BASE)
    graph.bind("cropaddtext", CROPADDTEXT)
    graph.bind("pestaddtext", PESTADDTEXT)
    graph.bind("xsd", XSD)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)
    texts_df = con.execute("""
        SELECT * FROM CodeEnriched
        WHERE text_key IN ('CultureAdditionalText', 'PestAdditionalText')
    """).df()
    con.close()

    # Create additional text triples
    for i, row in texts_df.iterrows():
        code_id = None
        try:
            if pd.isna(row.get("code_id")) or not str(row.get("code_id")).strip():
                print(f"Additional text row {i}: missing code_id -> skipped")
                continue

            code_id = str(row["code_id"]).strip().lower()
            ns, text_class = text_types[row["text_key"]]
            text_uri = ns[code_id]

            # Add Type
            graph.add((text_uri, RDF.type, text_class))
            
            # Add Identifier
            graph.add((text_uri, SCHEMA.identifier, Literal(code_id, datatype=XSD.string)))

            # Add language-tagged Names
            add_lang_labels(graph, text_uri, SCHEMA.name, row)

        except Exception as error:
            print(f"Additional text row {i} ({code_id or 'unknown'}): {error}")

    # Print graph info
    print(f"[i] Total additional text triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_file), format="turtle")
    print(f"\nSaved to `{out_file}`")
    
    return graph

if __name__ == "__main__":
    additional_texts_ttl()