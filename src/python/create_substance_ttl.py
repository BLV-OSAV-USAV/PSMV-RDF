import os
import sys
import csv
import yaml
import duckdb
from pathlib import Path
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
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
    out_path: str = "rdf/data/substance_ttl"):

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
        try:
            if pd.isna(row.get("nk_codetable_substance_id")):
                continue
        
            nk_codetable_substance_id = str(row.get("nk_codetable_substance_id")).strip()
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

            # German  name
            if pd.notna(row.get("DE")):
                graph.add((substance_uri, SCHEMA.name, Literal(str(row.get("DE")).strip(), lang="de")))
            
            # English name
            if pd.notna(row.get("EN")):
                graph.add((substance_uri, SCHEMA.name, Literal(str(row.get("EN")).strip(), lang="en")))
            
            # French name
            if pd.notna(row.get("FR")):
                graph.add((substance_uri, SCHEMA.name, Literal(str(row.get("FR")).strip(), lang="fr")))
            
            # Italian name
            if pd.notna(row.get("IT")):
                graph.add((substance_uri, SCHEMA.name, Literal(str(row.get("IT")).strip(), lang="it")))

            # ChEBI identities
            if pd.notna(row.get("hasChebiIdentity")):
                for chebi_id in str(row["hasChebiIdentity"]).split("|"):
                    chebi_id = chebi_id.strip()
                    if chebi_id:
                        graph.add((substance_uri, OWL.sameAs, CHEBI[chebi_id]))

            # PubChem Compound identities
            if pd.notna(row.get("hasPubChemCompoundIdentity")):
                for cid in str(row["hasPubChemCompoundIdentity"]).split("|"):
                    cid = cid.strip().removeprefix("CID:")
                    if cid:
                        graph.add((substance_uri, OWL.sameAs, PUBCHEM_COMPOUND[cid]))

            # PubChem Substance identities
            if pd.notna(row.get("hasPubChemSubstanceIdentity")):
                for sid in str(row["hasPubChemSubstanceIdentity"]).split("|"):
                    sid = sid.strip().removeprefix("SID:")
                    if sid:
                        graph.add((substance_uri, OWL.sameAs, PUBCHEM_SUBSTANCE[sid]))

            # Biological taxon
            if pd.notna(row.get("isDefinedByBiologicalTaxon")):
                for taxon in str(row["isDefinedByBiologicalTaxon"]).split("|"):
                    taxon = taxon.strip()
                    if taxon:
                        graph.add((substance_uri, OWL.sameAs, URIRef(taxon)))

        except Exception as error:
            print(f"Row {i} (Substance {substance_uri}): {error}")

    # Print graph info
    print(f"[i] Total triples: {len(graph)}")

    # Save to file
    out_path = Path("rdf/data/substance.ttl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=out_path, format="turtle")
    print(f"\nSaved to `{out_path}`")
    return graph

if __name__ == "__main__":
    substance_ttl()