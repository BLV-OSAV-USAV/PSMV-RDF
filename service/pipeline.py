import sys
import os
import time
import traceback
import subprocess
import datetime

# Third-party libraries
import rdflib
from pyshacl import validate as pyshacl_validate
from rdflib.namespace import RDF, SH

# Data processors
from src.python.utils.helper_functions import parse_phone_numbers, ensure_jar, load_rdf_mappings, load_namespaces

from src.python.db_processing.preprocess_data import preprocess_data
from src.python.db_processing.process_indication_code import process_indication_code
from src.python.db_processing.process_indication_links import process_indication_links
from src.python.db_processing.process_indication_product import process_indication_product
from src.python.db_processing.process_product_code import process_product_code
from src.python.db_processing.process_pest_code import process_pest_code
from src.python.db_processing.process_obligation_code import process_obligation_code
from src.python.db_processing.process_culture_code import process_culture_code
from src.python.db_processing.process_organisation import process_organisation
from src.python.db_processing.process_application_area_code import process_application_area_code
from src.python.db_processing.process_application_comment_code import process_application_comment_code

# Substances
from src.python.db_processing.process_substance_code import process_substance_code
from src.python.db_processing.enrich_substances import load_substances_mapping

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

    print("\n\033[1mPreprocess data\033[0m")
    preprocess_data()

    print("\n\033[1mRun database operations\033[0m")
    process_substance_code()
    load_substances_mapping()
    process_indication_code()
    process_product_code()
    process_pest_code()
    process_obligation_code()
    process_organisation()
    process_indication_links()
    process_indication_product()
    process_culture_code()
    process_application_area_code()
    process_application_comment_code()
    
    print("\n\033[1mValidate syntax of ontology turtle files and shacl shapes\033[0m")
    validate_ttl_files("rdf")

    print("\n\033[1mGenerate RDF datasets (ttl)\033[0m")
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

    print("\n\033[1mCreate a dedicated ontology file for subsequent WebVOWL visualization\033[0m")
    inputs = load_inputs(["rdf/ontology/*.ttl"])
    graph = apply_rules(inputs, ["src/sparql/rules/*.rq"])
    save_graph(graph, "rdf/processed/ontology.ttl")

    print("\n\033[1mMerge all data into one graph for subsequent LINDAS upload\033[0m")
    inputs = load_inputs(["rdf/ontology/*.ttl", "rdf/data/*.ttl", "rdf/shapes/*.ttl"])
    graph = apply_rules(inputs, [
        "src/sparql/rules/inverse.rq",
        "src/sparql/rules/subclass.rq",
        "src/sparql/rules/subproperty.rq",
        "src/sparql/processing/*.rq",
    ])
    save_graph(graph, "rdf/processed/graph.ttl")

    print("\n\033[1mCombine all SHACL rules into one shape\033[0m")
    inputs = load_inputs(["rdf/shapes/*.ttl"])
    graph = apply_rules(inputs, [])
    save_graph(graph, "rdf/processed/shapes.ttl")

    print("\n\033[1mChecking graph shape using SHACL...\033[0m")
    # uncomment when we are sure what to validate via SHACL here
    conforms, results_graph, results_text = run_shacl_validation()
    error_count = len(list(results_graph.subjects(RDF.type, SH.ValidationResult)))
    print(f"{error_count} errors were found.")  
    
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