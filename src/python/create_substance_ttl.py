import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, OWL

# local imports
from src.python.utils.helper_functions import load_namespaces, load_rdf_mappings, add_lang_labels

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
CHEBI = namespaces["chebi"]
PUBCHEM_COMPOUND = namespaces["pubchem_compound"]
PUBCHEM_SUBSTANCE = namespaces["pubchem_substance"]
WIKIDATA = namespaces["wikidata"]

# Load all RDF mappings
# Explicitly specify which namespace each mapping uses
namespace_config = {
    "country_mapping": "country",
    "type_mapping": "base"
}

rdf_mappings = load_rdf_mappings(namespaces, namespace_map=namespace_config)  

COUNTRY_MAPPING = rdf_mappings["country_mapping"]
TYPE_MAPPING = rdf_mappings["type_mapping"]

# Create Products
def substance_ttl(
    db_path = "data/processed/psmv-data.duckdb",
    out_path: str = "rdf/data/substance.ttl"):

    """
    Creates a substance_ttl
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
    graph.bind("chebi", CHEBI)
    graph.bind("pubchem_compound", PUBCHEM_COMPOUND)
    graph.bind("pubchem_substance", PUBCHEM_SUBSTANCE)
    graph.bind("wikidata", WIKIDATA)

    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)

    # Read data
    con = duckdb.connect(db_path, read_only=True)
    ingredient_df = con.execute("SELECT * FROM ProductIngredientCode").df()
    con.close()

    # Deduplicate nk_codetable_substance_id
    substance_df = (ingredient_df[[
        "nk_codetable_substance_id", "IUPAC_name", "public_name_de", 
        "active_substance_id", "co_formulant_id", "relevant_co_formulant", 
        "DE", "EN", "FR", "IT", "hasChebiIdentity", "hasPubChemCompoundIdentity", "hasPubChemSubstanceIdentity",
        "isDefinedByBiologicalTaxon"
        ]]
                    .dropna(subset=["nk_codetable_substance_id"]) 
                    .drop_duplicates(subset=["nk_codetable_substance_id"])
                    .reset_index(drop=True))

    # Create substance triples
    for i, row in substance_df.iterrows():
        substance_uri = None
        try:
            if (
                pd.isna(row.get("nk_codetable_substance_id"))
                or not str(row.get("nk_codetable_substance_id")).strip()
            ):
                print(f"Substance row {i}: missing nk_codetable_substance_id -> skipped")
                continue
        
            nk_codetable_substance_id = str(row.get("nk_codetable_substance_id")).strip().lower()
            substance_uri = SUBSTANCE[nk_codetable_substance_id]

            # Active substance or co-formulant
            if pd.notna(row.get("active_substance_id")):
                graph.add((substance_uri, RDF.type, BASE.ActiveSubstance))
            elif pd.notna(row.get("co_formulant_id")):
                graph.add((substance_uri, RDF.type, BASE.CoFormulant))
            else:
                graph.add((substance_uri, RDF.type, BASE.Substance))

            # IUPAC name
            if pd.notna(row.get("IUPAC_name")):
                graph.add((substance_uri, BASE.iupacName, Literal(str(row.get("IUPAC_name")).strip())))

             # Add language-tagged Names
            add_lang_labels(graph, substance_uri, SCHEMA.name, row)

            # ChEBI identities
            if pd.notna(row.get("hasChebiIdentity")):
                for chebi_id in str(row["hasChebiIdentity"]).split("|"):
                    chebi_id = chebi_id.strip()
                    if chebi_id and chebi_id.lower() != "nan":
                        graph.add((substance_uri, OWL.sameAs, CHEBI[chebi_id]))

            # PubChem Compound identities
            if pd.notna(row.get("hasPubChemCompoundIdentity")):
                for cid in str(row["hasPubChemCompoundIdentity"]).split("|"):
                    cid = cid.strip().removeprefix("CID:")
                    if cid and cid.lower() != "nan":
                        graph.add((substance_uri, OWL.sameAs, PUBCHEM_COMPOUND[cid]))

            # PubChem Substance identities
            if pd.notna(row.get("hasPubChemSubstanceIdentity")):
                for sid in str(row["hasPubChemSubstanceIdentity"]).split("|"):
                    sid = sid.strip().removeprefix("SID:")
                    if sid and sid.lower() != "nan":
                        graph.add((substance_uri, OWL.sameAs, PUBCHEM_SUBSTANCE[sid]))

            # Biological taxon
            if pd.notna(row.get("isDefinedByBiologicalTaxon")):
                for taxon in str(row["isDefinedByBiologicalTaxon"]).split("|"):
                    taxon = taxon.strip()
                    if taxon:
                        graph.add((substance_uri, OWL.sameAs, URIRef(taxon)))

        except Exception as error:
            print(
                f"Substance row {i} "
                f"({substance_uri or 'unknown'}): {error}"
            )

    # Print graph info
    print(f"[i] Total substance triples: {len(graph)}")

    # Save to file
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=out_file, format="turtle")
    print(f"\nSaved to `{out_path}`")
    return graph

if __name__ == "__main__":
    substance_ttl()