import sys
import argparse
from pathlib import Path
import rdflib

ROOT = Path(__file__).resolve().parents[2]

RED   = "\033[91m"
GREEN = "\033[92m"
GRAY  = "\033[90m"
RESET = "\033[0m"

def validate_ttl_files(root_path: Path, recursive: bool = True) -> bool:
    """
    Parses Turtle files to validate syntax.
    """
    root_path = Path(root_path)
    pattern = "**/*.ttl" if recursive else "*.ttl"
    ttl_files = list(root_path.glob(pattern))

    if not ttl_files:
        print(f"No Turtle files found in '{root_path}'.")
        return True

    errors = []
    for ttl_file in ttl_files:
        rel = ttl_file.relative_to(ROOT) if ttl_file.is_relative_to(ROOT) else ttl_file
        try:
            rdflib.Graph().parse(str(ttl_file), format="turtle")
            print(f"{GREEN}[✓]{RESET} {rel}")
        except Exception as e:
            print(f"{RED}[✗]{RESET} {rel}\n    {GRAY}{e}{RESET}")
            errors.append(ttl_file)

    print(f"\n{len(ttl_files)} files checked, {len(errors)} error(s).")
    return len(errors) == 0

def main():
    parser = argparse.ArgumentParser(
        description="Validate RDF Turtle (.ttl) syntax using rdflib."
    )
    parser.add_argument(
        "directory", type=Path, nargs="?", default=Path("rdf"),
        help="Root directory to search for .ttl files (default: rdf/)"
    )
    parser.add_argument(
        "--no-recursive", action="store_false", dest="recursive",
        help="Disable recursive directory searching"
    )
    args = parser.parse_args()

    resolved = ROOT / args.directory if not args.directory.is_absolute() else args.directory
    if not resolved.is_dir():
        print(f"Error: '{resolved}' is not a valid directory.")
        sys.exit(1)

    sys.exit(0 if validate_ttl_files(resolved, recursive=args.recursive) else 1)

if __name__ == "__main__":
    main()