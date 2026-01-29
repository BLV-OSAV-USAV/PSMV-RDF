import argparse
import sys
from pathlib import Path
from typing import List, Optional
from rdflib import Graph
from otsrdflib import OrderedTurtleSerializer

def load_inputs(paths: List[Path]) -> Graph:
    """
    Initializes a single Graph and parses multiple source files into it.
    """
    g = Graph()
    for path in paths:
        try:
            g.parse(str(path), format="turtle")
            print(f"[+] Loaded triples from {path}")
        except Exception as e:
            print(f"[!] Error loading {path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    print(f"[i] Total graph size: {len(g)} triples")
    return g

def apply_rules(graph: Graph, rules: List[Path]):
    print(f"[i] Applying {len(rules)} inference rules...")
    
    for rule_path in rules:
        if not rule_path.exists():
            print(f"[!] Rule file not found: {rule_path}", file=sys.stderr)
            continue

        with open(rule_path, "r") as f:
            query_string = f.read()
        
        # Heuristic check: Is this an Update or a Construct?
        # rdflib requires .update() for DELETE/INSERT and .query() for CONSTRUCT
        if "DELETE" in query_string or "INSERT" in query_string:
            print(f"  -> {rule_path.name}: Executing SPARQL Update...")
            try:
                # Modifies graph in-place; no return value to iterate
                graph.update(query_string)
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

def bind_custom_prefixes(graph: Graph, prefix_path: Path):
    """
    Parses a TTL file containing prefix definitions and binds them 
    to the target graph's NamespaceManager.
    """
    if not prefix_path.exists():
        print(f"[!] Prefix file not found: {prefix_path}", file=sys.stderr)
        return

    # Use a temporary graph to parse the prefixes.ttl file
    temp_g = Graph()
    try:
        temp_g.parse(str(prefix_path), format="turtle")
        
        # Transfer namespaces to the main graph
        # override=True ensures these prefixes take precedence over auto-generated ones
        count = 0
        for prefix, namespace in temp_g.namespaces():
            graph.bind(prefix, namespace, override=True)
            count += 1
            
        print(f"[i] Bound {count} custom namespaces from {prefix_path}")
        
    except Exception as e:
        print(f"[!] Error parsing prefixes: {e}", file=sys.stderr)

def save_graph(graph: Graph, output_path: Path):
    """
    Serializes the graph to the specified output path using OrderedTurtleSerializer.
    """
    print(f"[+] Writing {len(graph)} triples to {output_path}...")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "wb") as f:
        serializer = OrderedTurtleSerializer(graph)
        # The serializer automatically uses the graph's NamespaceManager
        serializer.serialize(f)

def main():
    parser = argparse.ArgumentParser(
        description="RDF Materialization CLI: Merges inputs, applies SPARQL rules, and serializes output."
    )

    parser.add_argument(
        "-i", "--input", 
        nargs="+", 
        type=Path, 
        required=True,
        help="One or more input RDF files (Turtle format)."
    )

    parser.add_argument(
        "-o", "--output", 
        type=Path, 
        required=True,
        help="Destination path for the materialized graph."
    )

    parser.add_argument(
        "-r", "--rules", 
        nargs="+", 
        type=Path, 
        required=True,
        help="One or more SPARQL rule files (.rq or .sparql)."
    )
    
    # New Optional Argument
    parser.add_argument(
        "-p", "--prefixes", 
        type=Path, 
        required=False,
        help="A .ttl file containing @prefix definitions to control output QNames."
    )

    args = parser.parse_args()

    # 1. Load Inputs
    full_graph = load_inputs(args.input)

    # 2. Reason
    apply_rules(full_graph, args.rules)

    # 3. Apply Prefixes (if provided)
    # We do this before saving so the serializer sees the correct QNames
    if args.prefixes:
        bind_custom_prefixes(full_graph, args.prefixes)

    # 4. Serialize
    save_graph(full_graph, args.output)

if __name__ == "__main__":
    main()
