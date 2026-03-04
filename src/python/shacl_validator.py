import time
from pyshacl import validate as pyshacl_validate

def run_shacl_validation(
    data_graph: str = "rdf/processed/graph.ttl",
    shacl_graph: str = "rdf/processed/shapes.ttl",
    report_path: str = "docs/shacl_shape_report.ttl",
    serialize_report: bool = True,
):
    print(f"[*] Starting SHACL validation...")
    print(f"    Data graph : {data_graph}")
    print(f"    SHACL graph: {shacl_graph}")

    start = time.perf_counter()

    conforms, results_graph, results_text = pyshacl_validate(
        data_graph,
        shacl_graph=shacl_graph,
        serialize_report_graph=False,  
    )

    elapsed = time.perf_counter() - start
    print(f"[+] SHACL validation complete in {elapsed:.3f}s")
    print(f"    Conforms   : {conforms}")

    if serialize_report and results_graph:
        results_graph.serialize(destination=report_path, format="turtle")
        print(f"    Report saved to: {report_path}")

    return conforms

if __name__ == "__main__":
    run_shacl_validation()