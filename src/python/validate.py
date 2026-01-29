import sys
import argparse
from pathlib import Path
import rdflib

# Define colors
RED = "\033[91m"
GRAY   = "\033[90m"
RESET = "\033[0m"

def validate_ttl_files(root_path: Path, recursive: bool = True) -> bool:
    """
    Parses Turtle files to validate syntax.
    """
    pattern = "**/*.ttl" if recursive else "*.ttl"
    ttl_files = list(root_path.glob(pattern))
    
    if not ttl_files:
        print(f"No Turtle files found in '{root_path}'.")
        return True
    
    all_valid = True
    for ttl_file in ttl_files:
        print(f"[+] Validating {ttl_file}...")
        g = rdflib.Graph()
        try:
            g.parse(str(ttl_file), format="turtle")
        except Exception as e:
            print(f"{RED}[!] Error in file {ttl_file}, {GRAY}{e}{RESET}")
            all_valid = False
            
    return all_valid

def main():
    parser = argparse.ArgumentParser(
        description="CLI tool to validate RDF Turtle (.ttl) syntax using rdflib."
    )
    
    # Positional argument for the root directory
    parser.add_argument(
        "directory", 
        type=Path, 
        nargs="?", 
        default=Path("."),
        help="The root directory to search for .ttl files (default: current directory)"
    )
    
    # Optional flag to disable recursion if desired
    parser.add_argument(
        "--no-recursive", 
        action="store_false", 
        dest="recursive",
        help="Disable recursive directory searching"
    )
    
    args = parser.parse_args()

    if not args.directory.is_dir():
        print(f"Error: {args.directory} is not a valid directory.")
        sys.exit(1)

    success = validate_ttl_files(args.directory, recursive=args.recursive)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()