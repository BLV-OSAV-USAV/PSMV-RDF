import os
import time

from pyrudof import (
    RDFFormat,
    ReaderMode,
    ResultShaclValidationFormat,
    Rudof,
    RudofConfig,
    ShaclFormat,
    ShaclValidationMode,
)
from rdflib import Graph
from rdflib.namespace import SH

from src.python.shacl_report import summarise


def run_shacl_validation(
    data_graph: str = "rdf/processed/graph.ttl",
    shacl_graph: str = "rdf/processed/shapes.ttl",
    report_path: str = "rdf/processed/shacl_shape_report.ttl",
    serialize_report: bool = True,
    details: bool = False,
    fail_on_violation: bool = False,
    max_groups: int = 15,
):
    print("[*] Starting SHACL validation")
    print(f"    Data graph : {data_graph}")
    print(f"    SHACL graph: {shacl_graph}")

    timings = {}
    t = time.perf_counter()

    def lap(name):
        nonlocal t
        now = time.perf_counter()
        timings[name] = now - t
        t = now

    # Load
    rudof = Rudof(RudofConfig())
    rudof.read_shacl(shacl_graph, ShaclFormat.Turtle, reader_mode=ReaderMode.Strict)
    lap("read shapes")
    rudof.read_data(data_graph, RDFFormat.Turtle, reader_mode=ReaderMode.Strict)
    lap("read data")

    # Validate
    report = rudof.validate_shacl(ShaclValidationMode.Native)
    conforms = report.conforms
    lap("validate")

    # Serialize
    report_ttl = rudof.serialize_shacl_validation_results(ResultShaclValidationFormat.Turtle)
    lap("serialize ttl")
    results_text = None
    if details:
        results_text = rudof.serialize_shacl_validation_results(ResultShaclValidationFormat.Details)
        lap("serialize details")

    if serialize_report:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_ttl)
        lap("write report")

    # Summarise
    results_graph = Graph().parse(data=report_ttl, format="turtle")
    lap("parse report")
    rows = summarise(results_graph)
    lap("summarise")

    total = sum(timings.values())
    print(f"[+] SHACL validation complete in {total:.3f}s")
    print("    " + " | ".join(f"{k} {v:.2f}s" for k, v in timings.items()))
    print(f"    Conforms   : {conforms}")
    if serialize_report:
        print(f"    Report     : {report_path}")

    if rows:
        n_results = sum(r["n"] for r in rows)
        print(f"    Results    : {n_results} in {len(rows)} groups")
        for r in rows[:max_groups]:
            print(f'      [{r["n"]}] {r["severity"]} | {r["kind"]} | {r["path"]} | {r["constraint"]}')
        if len(rows) > max_groups:
            where = f", see {report_path}" if serialize_report else ""
            print(f"      ... {len(rows) - max_groups} more groups{where}")

    n_violations = sum(1 for _ in results_graph.subjects(SH.resultSeverity, SH.Violation))
    if n_violations:
        msg = f"SHACL: {n_violations} violation(s)" + (f", see {report_path}" if serialize_report else "")
        if fail_on_violation:
            raise RuntimeError(msg)
        print(f"\033[93m[!] {msg} (not blocking)\033[0m")
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::warning title=SHACL::{msg}")

    return conforms, results_graph, results_text

    return conforms, results_graph, results_text
    return conforms, results_graph, results_text


if __name__ == "__main__":
    run_shacl_validation()