import argparse
import sys
import rdflib
from pathlib import Path
from typing import List
from rdflib import Graph, Namespace
from otsrdflib import OrderedTurtleSerializer

ROOT = Path(__file__).resolve().parents[2]


def resolve_globs(patterns: List[str | Path]) -> List[Path]:
    """Expands glob patterns relative to ROOT into concrete file paths."""
    resolved = []
    for pattern in patterns:
        pattern = Path(pattern)
        pattern = ROOT / pattern if not pattern.is_absolute() else pattern
        matches = sorted(pattern.parent.glob(pattern.name))
        if not matches:
            print(f"[!] No files matched: {pattern}", file=sys.stderr)
            sys.exit(1)
        resolved.extend(matches)
    return resolved


def load_inputs(patterns: List[str | Path]) -> rdflib.ConjunctiveGraph:
    """
    Initializes a single Graph and parses multiple source files into it.
    """
    g = rdflib.ConjunctiveGraph()
    for path in resolve_globs(patterns):
        try:
            g.parse(str(path), format="turtle")
            print(f"[+] Loaded triples from {path.relative_to(ROOT)}")
        except Exception as e:
            print(f"[!] Error loading {path}: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"[i] Total graph size: {len(g)} triples")
    return g


def apply_rules(graph: Graph, patterns: List[str | Path]) -> Graph:
    """
    Applies SPARQL Update (INSERT/DELETE) or Construct queries to the graph.
    """
    if not patterns:
        return graph

    rules = resolve_globs(patterns)
    print(f"[i] Applying {len(rules)} inference rules...")

    for rule_path in rules:
        with open(rule_path, "r") as f:
            query_string = f.read()

        # Heuristic check: Is this an Update or a Construct?
        if "DELETE" in query_string or "INSERT" in query_string:
            try:
                # 1. Snapshot for Diff
                before_triples = set(graph)

                # 2. Execute Update
                graph.update(query_string)

                # 3. Calculate Diff
                after_triples = set(graph)
                added = len(after_triples - before_triples)
                removed = len(before_triples - after_triples)

                print(f"  -> {rule_path.name}: +{added}/-{removed} triples")

            except Exception as e:
                print(f"[!] Error executing update {rule_path.name}: {e}", file=sys.stderr)

        else:
            # Fallback to standard CONSTRUCT/SELECT logic
            try:
                results = graph.query(query_string)

                initial_count = len(graph)
                for triple in results:
                    graph.add(triple)
                added_count = len(graph) - initial_count

                print(f"  -> {rule_path.name}: +{added_count} triples")
            except Exception as e:
                print(f"[!] Error executing query {rule_path.name}: {e}", file=sys.stderr)

    return graph


def save_graph(graph: Graph, output_path: str | Path):
    """
    Serializes the graph to the specified output path using OrderedTurtleSerializer.
    """
    output_path = Path(output_path)
    output_path = ROOT / output_path if not output_path.is_absolute() else output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[+] Writing {len(graph)} triples to {output_path.relative_to(ROOT)}...")

    # 1. Force Schema.org binding (http) just before save
    # This overrides whatever rdflib might have guessed during parsing
    try:
        graph.bind("schema", Namespace("http://schema.org/"), override=True, replace=True)
    except TypeError:
        # Fallback for older rdflib versions that don't support 'replace'
        graph.bind("schema", Namespace("http://schema.org/"), override=True)

    # 2. Serialize
    with open(output_path, "wb") as f:
        serializer = OrderedTurtleSerializer(graph)
        serializer.serialize(f)


def main():
    parser = argparse.ArgumentParser(
        description="RDF CLI tool: sorts, merges, and optionally reasons over RDF data."
    )

    parser.add_argument(
        "-i", "--input",
        nargs="+",
        type=Path,
        required=True,
        help="One or more input turtle RDF files (.ttl format)."
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Destination path for the materialized/sorted graph."
    )

    # Made optional (required=False) to allow for simple merge/sort operations
    parser.add_argument(
        "-r", "--rules",
        nargs="+",
        type=Path,
        required=False,
        help="Optional: One or more SPARQL rule files (.rq or .sparql)."
    )

    args = parser.parse_args()

    # 1. Load Inputs (Supports multiple files -> Merging)
    full_graph = load_inputs(args.input)

    # 2. Reason (Only if rules are provided)
    if args.rules:
        apply_rules(full_graph, args.rules)

    # 3. Serialize (Handles Sorting & Prefix Binding)
    save_graph(full_graph, args.output)


if __name__ == "__main__":
    main()