#!/usr/bin/env python
"""Run SHACL validation, summarise the report, and gate CI on the result."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import BNode, Graph

BASE = "https://agriculture.ld.admin.ch/plant-protection/"
SEVERITY_ORDER = {"Violation": 0, "Warning": 1, "Info": 2}
FAIL_LEVELS = {
    "violation": {"Violation"},
    "warning": {"Violation", "Warning"},
    "never": set(),
}

SUMMARY_QUERY = r"""
PREFIX sh: <http://www.w3.org/ns/shacl#>

SELECT ?severity ?kind ?path ?constraint (COUNT(*) AS ?n)
       (SAMPLE(?msg) AS ?message) (SAMPLE(?focus) AS ?example)
WHERE {
  ?r a sh:ValidationResult ;
     sh:resultSeverity ?sev ;
     sh:focusNode ?focus ;
     sh:sourceConstraintComponent ?component .
  OPTIONAL { ?r sh:resultPath ?path }
  OPTIONAL { ?r sh:resultMessage ?msg }
  BIND(REPLACE(STR(?sev), "^.*#", "") AS ?severity)
  BIND(REPLACE(STR(?component), "^.*#", "") AS ?constraint)
  BIND(
    IF(isBlank(?focus), "blank node",
       REPLACE(STR(?focus),
               "^https://agriculture\\.ld\\.admin\\.ch/plant-protection/([^/]+)/.*$", "$1"))
    AS ?kind)
}
GROUP BY ?severity ?kind ?path ?constraint
"""


def short(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, BNode):
        return "_:bnode"  # stable key for complex paths / blank focus nodes
    return str(v).replace(BASE, ":").replace("http://schema.org/", "schema:")


def md(s: str, limit: int = 120) -> str:
    s = s.replace("|", "\\|").replace("\n", " ")
    return s if len(s) <= limit else s[: limit - 3] + "..."


def group_key(r: dict) -> str:
    return f'{r["severity"]}|{r["kind"]}|{r["path"]}|{r["constraint"]}'


def load(paths: list[str]) -> Graph:
    g = Graph()
    for p in paths:
        g.parse(p)  # format guessed from file extension
    return g


def run_validation(data: list[str], shapes: list[str], ont: list[str], inference: str) -> Graph:
    _, report, _ = validate(
        load(data),
        shacl_graph=load(shapes),
        ont_graph=load(ont) if ont else None,
        inference=inference,
        abort_on_first=False,
        allow_warnings=True,
    )
    return report


def summarise(report: Graph) -> list[dict]:
    rows = [
        {
            "severity": str(sev),
            "kind": str(kind),
            "path": short(path),
            "constraint": str(constraint),
            "n": int(n),
            "message": short(msg),
            "example": short(ex),
        }
        for sev, kind, path, constraint, n, msg, ex in report.query(SUMMARY_QUERY)
    ]
    rows.sort(key=lambda r: (SEVERITY_ORDER.get(r["severity"], 9), -r["n"]))
    return rows


def to_markdown(rows, regressions, improvements, baseline_used: bool) -> str:
    out = ["## SHACL validation", ""]
    if not rows:
        out.append("✅ The data conforms to all shapes.")
        return "\n".join(out) + "\n"

    totals: dict[str, list[int]] = {}
    for r in rows:
        t = totals.setdefault(r["severity"], [0, 0])
        t[0] += r["n"]
        t[1] += 1
    out += ["| Severity | Results | Groups |", "|---|---:|---:|"]
    for sev in sorted(totals, key=lambda s: SEVERITY_ORDER.get(s, 9)):
        out.append(f"| {sev} | {totals[sev][0]} | {totals[sev][1]} |")
    out.append("")

    if baseline_used:
        if regressions:
            out += [
                "### ❌ New or increased issues compared to baseline",
                "",
                "| Severity | Kind | Path | Constraint | Baseline | Now | Example | Message |",
                "|---|---|---|---|---:|---:|---|---|",
            ]
            for r, old in regressions:
                out.append(
                    f'| {r["severity"]} | {md(r["kind"])} | `{md(r["path"])}` | {r["constraint"]} '
                    f'| {old} | {r["n"]} | `{md(r["example"], 80)}` | {md(r["message"])} |'
                )
            out.append("")
        else:
            out += ["✅ No new or increased issues compared to baseline.", ""]
        if improvements:
            out += [
                f"🎉 {len(improvements)} group(s) improved. Consider updating the baseline "
                "with `--write-baseline`.",
                "",
            ]

    out += [
        "<details><summary>All result groups</summary>",
        "",
        "| n | Severity | Kind | Path | Constraint | Example | Message |",
        "|---:|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f'| {r["n"]} | {r["severity"]} | {md(r["kind"])} | `{md(r["path"])}` | {r["constraint"]} '
            f'| `{md(r["example"], 80)}` | {md(r["message"])} |'
        )
    out += ["", "</details>"]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", nargs="+", help="RDF data files to validate")
    ap.add_argument("--shapes", nargs="+", help="SHACL shapes files")
    ap.add_argument("--ont", nargs="*", default=[], help="Ontology files (used for inference)")
    ap.add_argument("--inference", default="none", choices=["none", "rdfs", "owlrl", "both"])
    ap.add_argument("--report", help="Use an existing report instead of running validation")
    ap.add_argument("--report-out", help="Write the validation report as Turtle")
    ap.add_argument("--baseline", help="JSON with accepted counts per group")
    ap.add_argument("--write-baseline", help="Write current counts as a new baseline JSON")
    ap.add_argument("--summary-md", help="Write the Markdown summary to this file")
    ap.add_argument("--fail-on", default="violation", choices=list(FAIL_LEVELS))
    args = ap.parse_args()

    if args.report:
        report = Graph().parse(args.report)
    else:
        if not (args.data and args.shapes):
            ap.error("--data and --shapes are required unless --report is given")
        report = run_validation(args.data, args.shapes, args.ont, args.inference)
        if args.report_out:
            report.serialize(args.report_out, format="turtle")

    rows = summarise(report)
    current = {group_key(r): r["n"] for r in rows}

    for r in rows:
        print(f'\n[{r["n"]}] {r["severity"]} | {r["kind"]} | {r["path"]} | {r["constraint"]}')
        print(f'     message: {r["message"][:150]}')
        print(f'     example: {r["example"]}')

    baseline = None
    if args.baseline and Path(args.baseline).exists():
        baseline = json.loads(Path(args.baseline).read_text())

    regressions, improvements = [], []
    if baseline is not None:
        regressions = [(r, baseline.get(group_key(r), 0)) for r in rows
                       if r["n"] > baseline.get(group_key(r), 0)]
        improvements = [k for k, n in baseline.items() if current.get(k, 0) < n]

    if args.write_baseline:
        Path(args.write_baseline).write_text(json.dumps(dict(sorted(current.items())), indent=2) + "\n")

    summary = to_markdown(rows, regressions, improvements, baseline is not None)
    if args.summary_md:
        Path(args.summary_md).write_text(summary)
    if step_summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(step_summary, "a") as f:
            f.write(summary)

    fail_sev = FAIL_LEVELS[args.fail_on]
    if baseline is not None:
        failing = [r for r, _ in regressions if r["severity"] in fail_sev]
    else:
        failing = [r for r in rows if r["severity"] in fail_sev]

    print(f"\n{len(rows)} groups, {sum(current.values())} results, {len(failing)} failing groups")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())