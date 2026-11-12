import time
from src.python.shacl_report import summarise
from rdflib import Graph
from pyrudof import RDFFormat, ReaderMode, ResultShaclValidationFormat, Rudof, RudofConfig, ShaclFormat, ShaclValidationMode


def run_shacl_validation(
    data_graph: str = "rdf/processed/graph.ttl",
    shacl_graph: str = "rdf/processed/shapes.ttl",
    report_path: str = "rdf/processed/shacl_shape_report.ttl",
    serialize_report: bool = True,
    max_groups: int = 15,
):
    print(f"[*] Starting SHACL validation")
    print(f"    Data graph : {data_graph}")
    print(f"    SHACL graph: {shacl_graph}")

    start = time.perf_counter()

    rudof = Rudof(RudofConfig())
    rudof.read_shacl(shacl_graph, ShaclFormat.Turtle, reader_mode=ReaderMode.Strict)
    rudof.read_data(data_graph, RDFFormat.Turtle, reader_mode=ReaderMode.Strict)

    report = rudof.validate_shacl(ShaclValidationMode.Native)
    conforms = report.conforms

    results_text = rudof.serialize_shacl_validation_results(
        ResultShaclValidationFormat.Details
    )
    report_ttl = rudof.serialize_shacl_validation_results(
        ResultShaclValidationFormat.Turtle
    )

    elapsed = time.perf_counter() - start

    if serialize_report:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_ttl)
        print(f"    Report     : {report_path}")

    print(f"[+] SHACL validation complete in {elapsed:.3f}s")
    print(f"    Conforms   : {conforms}")

    results_graph = Graph().parse(data=report_ttl, format="turtle")

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