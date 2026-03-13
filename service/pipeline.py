import sys
import os
import subprocess
import datetime
import rdflib

from pyshacl import validate as pyshacl_validate

# local imports
from src.python.preprocess_data import process_data
from src.python.validate import validate_ttl_files
from src.python.create_produtcs_ttl import products_ttl
from src.python.create_organisation_ttl import organisation_ttl
from src.python.reason import load_inputs, apply_rules, save_graph
from src.python.shacl_validator import run_shacl_validation

from src.python.utils.helper_functions import *

def run_pipeline():

    print("\nPreprocess data")
    process_data()

    print("\nValidate syntax of turtle files")
    validate_ttl_files("rdf")

    print("\nRun data integration pipeline")
    products_ttl()
    organisation_ttl()

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
    run_shacl_validation()

    print(f"\n{"\033[92m"}✓ Pipeline completed successfully.{"\033[0m"}")


if __name__ == "__main__":
    run_pipeline()