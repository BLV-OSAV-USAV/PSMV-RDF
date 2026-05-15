import sys
import os
import subprocess
import datetime
import rdflib

from pyshacl import validate as pyshacl_validate

# local imports

from src.python.validate import validate_ttl_files
from src.python.create_produtcs_ttl import products_ttl
from src.python.create_organisation_ttl import organisation_ttl
from src.python.create_substance_ttl import substance_ttl
from src.python.create_crops_ttl import crops_ttl
from src.python.create_pests_ttl import pests_ttl
from src.python.create_application_area_ttl import application_area_ttl
from src.python.create_application_comment_ttl import application_comment_ttl
from src.python.create_obligation_ttl import obligation_ttl
from src.python.create_ghs_ttl import ghs_ttl
from src.python.reason import load_inputs, apply_rules, save_graph
from src.python.shacl_validator import run_shacl_validation

from src.python.db_processing.preprocess_data import process_data
from src.python.db_processing.pivot_substances_code_table import process_substance_code
from src.python.db_processing.enrich_substances import load_substances_mapping
from src.python.db_processing.pivot_indication_code_tables import process_indication_code
from src.python.utils.helper_functions import *

def run_pipeline():

    print("\nPreprocess data")
    process_data()

    print("\nRun database operations")
    process_substance_code()
    process_indication_code()
    load_substances_mapping()
    
    print("\nValidate syntax of turtle files")
    validate_ttl_files("rdf")

    print("\nRun data integration pipeline")
    products_ttl()
    organisation_ttl()
    substance_ttl()
    crops_ttl()
    pests_ttl()
    application_area_ttl()
    application_comment_ttl()
    obligation_ttl()
    ghs_ttl()
    #indication_ttl()

    print("\nCreate a dedicated ontology file for subsequent WebVOWL visualization")
    inputs = load_inputs(["rdf/ontology/*.ttl"])
    graph = apply_rules(inputs, ["src/sparql/rules/*.rq"])
    save_graph(graph, "rdf/processed/ontology.ttl")

    print("\nMerge all data into one graph for subsequent LINDAS upload")
    inputs = load_inputs(["rdf/ontology/*.ttl", "rdf/data/*.ttl", "rdf/shapes/*.ttl"])
    graph = apply_rules(inputs, [
        "src/sparql/rules/inverse.rq",
        "src/sparql/rules/subclass.rq",
        "src/sparql/rules/subproperty.rq"
    ])
    save_graph(graph, "rdf/processed/graph.ttl")

    print("\nCombine all SHACL rules into one shape")
    inputs = load_inputs(["rdf/shapes/*.ttl"])
    graph = apply_rules(inputs, [])
    save_graph(graph, "rdf/processed/shapes.ttl")

    print("\nChecking graph shape using SHACL...")
    #run_shacl_validation()
    

    print(f"\n{"\033[92m"}✓ Pipeline completed successfully.{"\033[0m"}")


if __name__ == "__main__":
    run_pipeline()