import sys
import os
import time
import traceback
import subprocess
import datetime

# Third-party libraries
import rdflib
from pyshacl import validate as pyshacl_validate

# Data processors
from src.python.utils.helper_functions import parse_phone_numbers, ensure_jar, load_rdf_mappings, load_namespaces

from src.python.db_processing.preprocess_data import process_data
from src.python.db_processing.process_substance_code import process_substance_code
from src.python.db_processing.process_indication_code import process_indication_code
from src.python.db_processing.process_product_code import process_product_code
from src.python.db_processing.process_pest_code import process_pest_code
from src.python.db_processing.process_obligation_code import process_obligation_code
from src.python.db_processing.process_culture_code import process_culture_code
from src.python.db_processing.process_organisation import process_organisation
from src.python.db_processing.process_application_comment_code import process_application_comment_code

from src.python.db_processing.enrich_substances import load_substances_mapping
from src.python.db_processing.process_indication_links import process_indication_links

# Class modules
from src.python.create_produtcs_ttl import products_ttl
from src.python.create_organisation_ttl import organisation_ttl
from src.python.create_substance_ttl import substance_ttl
from src.python.create_crops_ttl import crops_ttl
from src.python.create_pests_ttl import pests_ttl
from src.python.create_application_area_ttl import application_area_ttl
from src.python.create_application_comment_ttl import application_comment_ttl
from src.python.create_obligation_ttl import obligation_ttl
from src.python.create_ghs_ttl import ghs_ttl
from src.python.create_indications_ttl import indication_ttl

# Reasoning
from src.python.reason import load_inputs, apply_rules, save_graph

# Validation
from src.python.validate import validate_ttl_files
from src.python.shacl_validator import run_shacl_validation

def run_pipeline():

    pipeline_start = time.perf_counter()
    print("\n\033[1m── PSMV RDF Pipeline ──\033[0m")

    print("\nPreprocess data")
    process_data()

    print("\nRun database operations")
    process_substance_code()
    load_substances_mapping()
    process_indication_code()
    process_product_code()
    process_pest_code()
    process_obligation_code()
    process_organisation()
    process_indication_links()
    process_culture_code()
    
    process_application_comment_code()
    
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
    indication_ttl()

    print("\nCreate a dedicated ontology file for subsequent WebVOWL visualization")
    inputs = load_inputs(["rdf/ontology/*.ttl"])
    graph = apply_rules(inputs, ["src/sparql/rules/*.rq"])
    save_graph(graph, "rdf/processed/ontology.ttl")

    print("\nMerge all data into one graph for subsequent LINDAS upload")
    inputs = load_inputs(["rdf/ontology/*.ttl", "rdf/data/*.ttl", "rdf/shapes/*.ttl"])
    graph = apply_rules(inputs, [
        "src/sparql/rules/inverse.rq",
        "src/sparql/rules/subclass.rq",
        "src/sparql/rules/subproperty.rq",
        "src/sparql/processing/*.rq",
    ])
    save_graph(graph, "rdf/processed/graph.ttl")

    print("\nCombine all SHACL rules into one shape")
    inputs = load_inputs(["rdf/shapes/*.ttl"])
    graph = apply_rules(inputs, [])
    save_graph(graph, "rdf/processed/shapes.ttl")

    print("\nChecking graph shape using SHACL...")
    # run_shacl_validation()
    # uncomment when we are sure what to validate via SHACL here
    
    # Pipeline completed
    total = time.perf_counter() - pipeline_start
    print(f"\n\033[92m\033[1m✓ Pipeline completed in {total:.1f}s\033[0m\n")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as exc:
        print("\n\033[91m\033[1m" + "─" * 50 + "\033[0m")
        print("\033[91m\033[1m✗ Pipeline aborted\033[0m")
        print("\033[91m\033[1m" + "─" * 50 + "\033[0m")
        print(f"\n  \033[1mError type:\033[0m  {type(exc).__name__}")
        print(f"  \033[1mMessage:\033[0m     {exc}")
        print("\n  \033[1mTraceback:\033[0m")
        traceback.print_exc()
        print("\033[91m\033[1m" + "─" * 50 + "\033[0m\n")
        sys.exit(1)