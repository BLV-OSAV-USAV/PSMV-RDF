#!/bin/bash
set -e # immediately exit on error
source .env


echo "Validate syntax of turtle files"
python3 src/python/validate.py rdf


echo "Create a dedicated ontology file for subsequent WebVOWL visualization"
python3 src/python/reason.py \
  -i rdf/ontology/*.ttl \
  -o rdf/processed/ontology.ttl \
  -r src/sparql/rules/*.rq


echo "Merge all data into one graph for subsequent LINDAS upload"
python3 src/python/reason.py \
  -i rdf/ontology/*.ttl rdf/data/*.ttl rdf/shapes/*.ttl \
  -o rdf/processed/graph.ttl \
  -r src/sparql/rules/inverse.rq src/sparql/rules/subclass.rq


echo "Combine all SHACL rules into one shape"
python3 src/python/reason.py \
  -i rdf/shapes/*.ttl \
  -o rdf/processed/shapes.ttl


echo "Check graph shape using SHACL"
pyshacl rdf/processed/graph.ttl --shapes rdf/processed/shapes.ttl --format human
