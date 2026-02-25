# PSMV-RDF

> [!NOTE]
> This repository is under active development. Features, documentation, and structure will change frequently.

## Plant Protection Products (PSMV) as Linked Data

A Python module for converting Swiss plant protection product data from CSV format to RDF and publishing it to the LINDAS Linked Data Service.

## Reproduce the data integration pipeline

1. Add variables to `.env`

    ``` bash
    USER=lindas-fsvo-psm
    PASSWORD=********
    GRAPH=https://lindas.admin.ch/foag/psm
    ENDPOINT=https://stardog.cluster.ldbar.ch/lindas
    ```

2. Create and activate the conda environment.

    ``` bash
    conda env create -f environment.yml
    conda activate psmv-rdf
    ```

3. Install the package in editable mode

    ``` bash
    pip install -e .
    ```

4. Start the data integration pipeline

    ``` bash
    python -m service.pipeline
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

Are more restricted data model is written in SHACL and [can be inspected here](https://shacl-play.sparna.fr/play/doc?format=html&url=https%3A%2F%2Fraw.githubusercontent.com%2FBLV-OSAV-USAV%2FPSMV-RDF%2Frefs%2Fheads%2Fmain%2Frdf%2Fshapes%2Fdata_shape.ttl&includeDiagram=false&sectionDiagram=false).

## Dependencies

Project dependencies are listed in [pyproject.toml](pyproject.toml).

## Acknowledgments 

- Built with [rdflib](https://github.com/RDFLib/rdflib)
- Integrates with [LINDAS](https://lindas.admin.ch/), the Swiss federal linked data service.
- Orignial ontology and pipeline by Damian Oswald with [plant protection pipeline](https://github.com/blw-ofag-ufag/plant-protection)
