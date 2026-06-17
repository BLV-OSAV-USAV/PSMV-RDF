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

## Example queries

[List all products](https://agriculture.ld.admin.ch/sparql/#query=PREFIX%20rdf%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%3E%0APREFIX%20rdfs%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0A%0ASELECT%20DISTINCT%20%3Fproduct%20%3Flabel%0AWHERE%20%7B%0A%20%20GRAPH%20%3Chttps%3A%2F%2Flindas.admin.ch%2Ffsvo%2Fplant-protection-products%3E%20%7B%0A%20%20%20%20%3Fproduct%20a%20%3Chttps%3A%2F%2Fagriculture.ld.admin.ch%2Fplant-protection%2FProduct%3E%20.%0A%20%20%20%20OPTIONAL%20%7B%20%3Fproduct%20rdfs%3Alabel%20%3Flabel%20%7D%0A%20%20%7D%0A%7D%0ALIMIT%2020&endpoint=https%3A%2F%2Fagriculture.ld.admin.ch%2Fquery&requestMethod=POST&tabTitle=Query&headers=%7B%7D&contentTypeConstruct=application%2Fn-triples%2C*%2F*%3Bq%3D0.9&contentTypeSelect=application%2Fsparql-results%2Bjson%2C*%2F*%3Bq%3D0.9&outputFormat=table)

[List a specific product by W-Number](https://agriculture.ld.admin.ch/sparql/#query=PREFIX%20rdfs%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0A%0ASELECT%20%3Fp%20%3Fo%0AWHERE%20%7B%0A%20%20GRAPH%20%3Chttps%3A%2F%2Flindas.admin.ch%2Ffsvo%2Fplant-protection-products%3E%20%7B%0A%20%20%20%20%3Chttps%3A%2F%2Fagriculture.ld.admin.ch%2Fplant-protection%2Fproduct%2FW-6847%3E%0A%20%20%20%20%20%20%3Fp%20%3Fo%20.%0A%20%20%7D%0A%7D%0A%0A&endpoint=https%3A%2F%2Fagriculture.ld.admin.ch%2Fquery&requestMethod=POST&tabTitle=Query&headers=%7B%7D&contentTypeConstruct=application%2Fn-triples%2C*%2F*%3Bq%3D0.9&contentTypeSelect=application%2Fsparql-results%2Bjson%2C*%2F*%3Bq%3D0.9&outputFormat=table)

[List all prodcuts containing sulphur](https://agriculture.ld.admin.ch/sparql/#query=PREFIX%20fsvo%3A%20%3Chttps%3A%2F%2Fagriculture.ld.admin.ch%2Fplant-protection%2F%3E%0APREFIX%20schema%3A%20%3Chttp%3A%2F%2Fschema.org%2F%3E%0A%0ASELECT%20DISTINCT%20%3Fproduct%20%3Fname%0AWHERE%20%7B%0A%20%20GRAPH%20%3Chttps%3A%2F%2Flindas.admin.ch%2Ffsvo%2Fplant-protection-products%3E%20%7B%0A%0A%20%20%20%20%3Fproduct%20%3Fp%20%3Fingredient%20.%0A%20%20%20%20%3Fingredient%20fsvo%3Asubstance%20%3Fsubstance%20.%0A%0A%20%20%20%20%3Fsubstance%20schema%3Aname%20%3Fname%20.%0A%0A%20%20%20%20FILTER(%0A%20%20%20%20%20%20REGEX(STR(%3Fname)%2C%20%22sulphur%22%2C%20%22i%22)%0A%20%20%20%20)%0A%20%20%7D%0A%7D&endpoint=https%3A%2F%2Fagriculture.ld.admin.ch%2Fquery&requestMethod=POST&tabTitle=Query%201&headers=%7B%7D&contentTypeConstruct=application%2Fn-triples%2C*%2F*%3Bq%3D0.9&contentTypeSelect=application%2Fsparql-results%2Bjson%2C*%2F*%3Bq%3D0.9&outputFormat=table)

## Acknowledgments 

- Built with [rdflib](https://github.com/RDFLib/rdflib)
- Integrates with [LINDAS](https://lindas.admin.ch/), the Swiss federal linked data service.
- Orignial ontology and pipeline by Damian Oswald with [plant protection pipeline](https://github.com/blw-ofag-ufag/plant-protection)
