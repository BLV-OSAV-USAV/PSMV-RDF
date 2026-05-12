# PSMV-RDF

> [!NOTE]
> This repository is under active development. Features, documentation, and structure will change frequently.

## Plant Protection Products (PSMV) as Linked Data

A Python module for converting Swiss plant protection product data from CSV format to RDF and publishing it to the LINDAS Linked Data Service.

## Reproduce the data integration pipeline

1. Set up the virtual environment

    ``` bash
    uv venv psmv-rdf
    source psmv-rdf/bin/activate  
    uv pip install -r pyproject.toml
    ```
    > If `uv` is not available: `pip install uv`
    
2. Install the package in editable mode

    ``` bash
    uv pip install -e .
    ```

3. Start the data integration pipeline

    ``` bash
    python -m service.pipeline
    ```
    
4. Upload Graph

    ``` bash
    python -m service.upload_graph
    ```

## Project Structure

``` bash
psmv-rdf/
├── .github/
├── data/           # any non-RDF data files
│   ├── raw/        # input CSV files
│   ├── mapping/    # yaml mapping files
│   └── processed/  # intermediately generated CSV files
├── services/
│   └── pipeline.py       
├── src/
│    ├── sparql     # SPARQL inference rules
│    └── python/    # Python scripts for specific tasks
├── rdf/
│   ├── ontology/   # OWL ontology documentation
│   ├── shapes/     # SHACL shapes, also used as data model documentation
│   ├── data/       # the actual RDF data, split by classes
│   ├── example/    # example turtle files used for reference
│   └── processed/  # any automatically written/derived/merged turtle files
├── tests/
├── docs/           # project documentation
├── .gitignore
├── README.md
└── environment.yml
```

## Ontology documentation

All ontology documentation files are written to `rdf/ontology`.
You may inspect a visual representation of the ontology used here: <https://service.tib.eu/webvowl/#iri=https://raw.githubusercontent.com/BLV-OSAV-USAV/PSMV-RDF/refs/heads/main/rdf/ontology/core.ttl>

## Data model

Are more restricted data model is written in SHACL and [can be inspected here](https://blv-osav-usav.github.io/PSMV-RDF/shacl-documentation.html).

## Dependencies

Project dependencies are listed in [pyproject.toml](pyproject.toml).

## Acknowledgments 

- Built with [rdflib](https://github.com/RDFLib/rdflib)
- Integrates with [LINDAS](https://lindas.admin.ch/), the Swiss federal linked data service.
- Orignial ontology and pipeline by Damian Oswald with [plant protection pipeline](https://github.com/blw-ofag-ufag/plant-protection)
