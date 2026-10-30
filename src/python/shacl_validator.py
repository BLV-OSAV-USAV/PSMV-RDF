import time
from pyshacl import validate as pyshacl_validate

from src.python.shacl_report import summarise


def run_shacl_validation(
    data_graph: str = "rdf/processed/graph.ttl",
    shacl_graph: str = "rdf/processed/shapes.ttl",
    report_path: str = "rdf/processed/shacl_shape_report.ttl",
    serialize_report: bool = True,
    max_groups: int = 15,
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

    if serialize_report:
        results_graph.serialize(destination=report_path, format="turtle")
        print(f"    Report     : {report_path}")

    elapsed = time.perf_counter() - start
    print(f"[+] SHACL validation complete in {elapsed:.3f}s")
    print(f"    Conforms   : {conforms}")

    rows = summarise(results_graph)
    if rows:
        n_results = sum(r["n"] for r in rows)
        print(f"    Results    : {n_results} in {len(rows)} groups")
        for r in rows[:max_groups]:
            print(f'      [{r["n"]}] {r["severity"]} | {r["kind"]} | {r["path"]} | {r["constraint"]}')
        if len(rows) > max_groups:
            print(f"      ... {len(rows) - max_groups} more groups, see {report_path}")

    return conforms, results_graph, results_text


if __name__ == "__main__":
    run_shacl_validation()