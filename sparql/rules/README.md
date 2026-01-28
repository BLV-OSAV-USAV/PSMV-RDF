## SPARQL Inference Rules

This directory contains the SPARQL inference rules used to materialize implicit knowledge within the published graph.
Each rule must be implemented as a [SPARQL 1.1 CONSTRUCT](https://www.w3.org/TR/sparql11-query/#construct) query.

These queries serve to explicitly assert relationships, classifications, and properties that are logically implied by the underlying source data.

> [!IMPORTANT]
> The SPARQL rules use OWL and RDFS statements made in the ontology.
> Hence, logical statements there will change the materialization downstream.
