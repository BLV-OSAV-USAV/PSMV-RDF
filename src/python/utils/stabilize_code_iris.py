"""Rewrite PSMV code IRIs to stable IDs derived from class + German name.

Phase 1: build old -> new IRI map from all .ttl files and write code_registry.csv
Phase 2: per file, rewrite IRIs, clean up identifiers and names,
         deduplicate identical blank nodes, write once
"""
import csv
import os
import re
from collections import defaultdict
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from src.python.utils.helper_functions import code_uuid

SCHEMA = Namespace("http://schema.org/")
CODE = "https://agriculture.ld.admin.ch/plant-protection/code/"
FILES = sorted(Path("rdf/data").glob("*.ttl"))
REGISTRY_FILE = "data/processed/code_registry.csv"

# Classes that get no fallback identifier when only unstable source IDs exist:
# ApplicationComment (closed shape without schema:identifier),
# PlantProtectionStatement (identifier is an optional phrase code)
NO_IDENTIFIER = {
    "https://agriculture.ld.admin.ch/plant-protection/ApplicationComment",
    "https://agriculture.ld.admin.ch/plant-protection/PlantProtectionStatement",
}

# Classes whose numeric identifiers are real, stable codes: never touch them
KEEP_IDENTIFIER: set[str] = set()

# Source IDs that change every dump: GUIDs, 36-char hex, plain numbers
UNSTABLE = re.compile(
    r"^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    r"|[0-9a-fA-F]{36}|\d+)$"
)


def pick(labels):
    """Deterministic choice: encoding errors last, then alphabetical."""
    return sorted(labels, key=lambda l: ("¿" in l or "\ufffd" in l, str(l)))[0]


def rewrite(g: Graph, id_map: dict) -> Graph:
    """Replace old code IRIs with stable ones in subjects and objects."""
    out = Graph()
    for prefix, ns in g.namespaces():
        out.bind(prefix, ns, override=True, replace=True)
    out.bind("schema", SCHEMA, override=True, replace=True)
    for s, p, o in g:
        out.add((id_map.get(s, s), p, id_map.get(o, o)))
    return out


def cleanup(g: Graph) -> tuple[int, int]:
    """Drop unstable identifiers and keep one schema:name per language."""
    n_ids = n_names = 0
    for s in {s for s in g.subjects() if str(s).startswith(CODE)}:
        cls = str(g.value(s, RDF.type))

        # identifiers
        ids = list(g.objects(s, SCHEMA.identifier))
        if ids and cls not in KEEP_IDENTIFIER:
            keep = [i for i in ids if not UNSTABLE.match(str(i))]
            if not keep and cls not in NO_IDENTIFIER:
                keep = [Literal(str(s).rsplit("/", 1)[-1], datatype=ids[0].datatype)]
            if set(keep) != set(ids):
                g.remove((s, SCHEMA.identifier, None))
                for i in keep:
                    g.add((s, SCHEMA.identifier, i))
                n_ids += 1

        # one name per language
        by_lang = defaultdict(list)
        for o in g.objects(s, SCHEMA.name):
            by_lang[o.language].append(o)
        for labels in by_lang.values():
            if len(labels) > 1:
                best = pick(labels)
                for o in labels:
                    if o != best:
                        g.remove((s, SCHEMA.name, o))
                n_names += 1
    return n_ids, n_names

def dedupe_bnodes(g: Graph) -> int:
    """On code nodes, keep one blank node per (predicate, identical content)."""
    removed = 0
    for s in {s for s in g.subjects() if str(s).startswith(CODE)}:
        seen = {}
        for p, b in list(g.predicate_objects(s)):
            if not isinstance(b, BNode):
                continue
            sig = (p, frozenset(g.predicate_objects(b)))
            if sig in seen:
                g.remove((s, p, b))
                g.remove((b, None, None))
                removed += 1
            else:
                seen[sig] = b
    return removed


def report_registry_changes(path: str, new_rows: list[tuple], max_lines: int = 20) -> None:
    """Warn (console + GitHub Actions) if the code registry changed."""
    old_rows = set()
    if os.path.exists(path):
        with open(path, newline="") as f:
            old_rows = {tuple(r) for r in list(csv.reader(f))[1:]}
    new_set = set(new_rows)

    added = sorted(new_set - old_rows)
    removed = sorted(old_rows - new_set)
    if not added and not removed:
        print("[+] Code registry unchanged")
        return

    msg = f"Code registry changed: {len(added)} added, {len(removed)} removed"
    print(f"\033[93m[!] {msg}\033[0m")
    for iri, cls, de in (removed[:max_lines]):
        print(f"\033[93m    - {cls.rsplit('/', 1)[-1]}: {de}\033[0m")
    for iri, cls, de in (added[:max_lines]):
        print(f"\033[93m    + {cls.rsplit('/', 1)[-1]}: {de}\033[0m")
    if len(added) + len(removed) > 2 * max_lines:
        print(f"\033[93m    ... see git diff {path}\033[0m")

    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning title=Code registry::{msg}. Code IRIs changed, check before release.")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as f:
                f.write(f"### ⚠️ {msg}\n\n| | Class | German label |\n|---|---|---|\n")
                for iri, cls, de in removed:
                    f.write(f"| ➖ | {cls.rsplit('/', 1)[-1]} | {de} |\n")
                for iri, cls, de in added:
                    f.write(f"| ➕ | {cls.rsplit('/', 1)[-1]} | {de} |\n")


def stabilize_code_iris():
    # Phase 1: map from all files + registry
    id_map = {}
    candidates = defaultdict(set)          # new IRI -> {(class, de label)}
    for path in FILES:
        g = Graph().parse(path)
        for s in set(g.subjects(RDF.type, None)):
            if not str(s).startswith(CODE):
                continue
            de = [o for o in g.objects(s, SCHEMA.name) if o.language == "de"]
            if not de:
                print(f"[!] no de name, kept: {s}")
                continue
            label = pick(de)
            cls = str(g.value(s, RDF.type))
            new = URIRef(CODE + code_uuid(str(label), cls))
            id_map[s] = new
            candidates[str(new)].add((cls, str(label)))

    # Merged codes may differ in case/whitespace: pick one deterministically
    registry = sorted((iri, *min(c)) for iri, c in candidates.items())
    report_registry_changes(REGISTRY_FILE, registry)
    with open(REGISTRY_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iri", "class", "label_de"])
        w.writerows(registry)
    print(f"[+] {len(id_map):,} codes -> {len(registry):,} IRIs, registry: {REGISTRY_FILE}")

    # Phase 2: rewrite + cleanup per file, write once
    for path in FILES:
        g = Graph().parse(path)
        out = rewrite(g, id_map)
        n_ids, n_names = cleanup(out)
        n_bnodes = dedupe_bnodes(out)
        out.serialize(path, format="turtle")
        print(f"[+] {path.name}: {len(g):,} -> {len(out):,} triples "
              f"(ids fixed: {n_ids}, names fixed: {n_names}, bnodes deduped: {n_bnodes})")


if __name__ == "__main__":
    stabilize_code_iris()