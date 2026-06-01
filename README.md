# PSMV-RDF
![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/github/license/BLV-OSAV-USAV/PSMV-RDF)
![Status](https://img.shields.io/badge/status-active--development-orange)
[![Docs](https://img.shields.io/badge/docs-github--pages-blue)](https://blv-osav-usav.github.io/PSMV-RDF/)
![CI](https://github.com/BLV-OSAV-USAV/PSMV-RDF/actions/workflows/psmv_rdf_primary_pipeline.yml/badge.svg)

> [!NOTE]
> This repository is under active development. Features, documentation, and structure will change frequently.

## Plant Protection Products (PSMV) as Linked Data

A Python module for converting Swiss plant protection product data from CSV format to RDF and publishing it to the LINDAS Linked Data Service.

## Reproduce the data integration pipeline

1. Set up the virtual environment

   > If `uv` is not yet installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
    ``` bash
    uv venv psmv-rdf
    source psmv-rdf/bin/activate  
    ```
   
    
3. Install the package in editable mode

    ``` bash
    uv pip install -e .
    ```

4. Start the data integration pipeline

    ``` bash
    python -m service.pipeline
    ```
    
5. To upload the graph, first, place a `.env` file in the directory root:

    ``` bash
    LINDAS_USER=********
    LINDAS_PASSWORD=************
    ENDPOINT=https://graphdb.lindas.admin.ch/repositories/lindas/rdf-graphs/service
    GRAPH=https://lindas.admin.ch/fsvo/plant-protection-products
    ```

    Then trigger the upload to LINDAS:

    ``` bash
    python -m service.upload_graph
    ```

## Project Structure

``` bash
psmv-rdf/
├── .github/
│   └── workflows/  # github actions
├── data/           # any non-RDF data files, used as input data
│   ├── mapping/    # yaml mapping files
│   ├── namespaces/ # 
│   ├── processed/  # 
│   └── mapping/    # input CSV files
├── docs/           # project documentation
├── rdf/
│   ├── ontology/   # OWL ontology documentation
│   ├── shapes/     # SHACL shapes, also used as data model documentation
│   ├── data/       # the actual RDF data, split by classes
│   ├── example/    # example turtle files used for reference
│   └── processed/  # any automatically written/derived/merged turtle files
├── services/
│   └── pipeline.py       
├── src/
│    ├── sparql     # SPARQL queries and inference rules
│    └── python/    # Python scripts for specific tasks
├── tests/
├── LICENSE
├── README.md
└── .gitignore
```

## Documentation

All ontology documentation files are written to `rdf/ontology`.
[You may inspect a visual representation of the ontology used here.](https://service.tib.eu/webvowl/#iri=https://raw.githubusercontent.com/BLV-OSAV-USAV/PSMV-RDF/refs/heads/main/rdf/ontology/core.ttl)

A more restricted data model is written in SHACL and [can be inspected here](https://blv-osav-usav.github.io/PSMV-RDF/shacl-documentation.html).

Project dependencies are listed in [pyproject.toml](pyproject.toml).

## Acknowledgments 

- Built with [rdflib](https://github.com/RDFLib/rdflib)
- Integrates with [LINDAS](https://lindas.admin.ch/), the Swiss federal linked data service.
- Orignial ontology and pipeline by Damian Oswald with [plant protection pipeline](https://github.com/blw-ofag-ufag/plant-protection)
