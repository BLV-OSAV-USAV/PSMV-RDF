import os
import sys
import argparse
import shutil
import subprocess

from src.python.utils.helper_functions import ensure_jar, SHACL_PLAY_JAR_PATH

DEFAULT_SHAPES_FILE = "rdf/processed/shapes.ttl"
DEFAULT_OUTPUT_FILE = "docs/shacl-documentation.html"

JAR_TIMEOUT_SECONDS = 300

def generate_documentation(
    shapes_file: str = DEFAULT_SHAPES_FILE,
    output_file: str = DEFAULT_OUTPUT_FILE,
    language: str = "en",
    include_diagram: bool = False,
    hide_datatype_properties: bool = False,
    output_format: str = "html",
    jar_path: str = SHACL_PLAY_JAR_PATH,
):
    """
    Generate HTML documentation from a SHACL shapes file.

    Parameters
    ----------
    shapes_file           : Path to the input .ttl shapes file.
    output_file           : Destination path for the generated documentation.
    language              : 2-letter language code, e.g. "en", "fr".
    include_diagram       : Embed a UML diagram at the top of the output.
    hide_datatype_properties: Hide datatype properties from the output.
    output_format         : "html" (default), "pdf", or "xml".
    jar_path              : Override the default JAR file location.

    Returns
    -------
    str : Absolute path to the generated documentation file.
    """
    if not os.path.isfile(shapes_file):
        raise FileNotFoundError(
            f"Shapes file not found: '{shapes_file}'\n"
            "Make sure the SHACL processing step ran first."
        )

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    if shutil.which("java") is None:
        raise RuntimeError("Java not found on PATH. Install Java 11+ and retry.")

    jar = ensure_jar(jar_path)

    cmd = [
        "java", "-jar", jar,
        "doc",
        "--input",    shapes_file,
        "--output",   output_file,
        "--language", language,
    ]

    if output_format != "html":
        cmd.extend(["--format", output_format])

    if include_diagram:
        cmd.append("--diagram")

    if hide_datatype_properties:
        cmd.append("--hide")

    log_path = os.path.join(os.path.dirname(os.path.abspath(output_file)), "shacl-documentaion-log.txt")

    print(f"  Shapes file : {shapes_file}")
    print(f"  Output file : {output_file}")
    print(f"  Format      : {output_format}  |  Language: {language}"
          f"  |  Diagram: {include_diagram}")
    print(f"  Log file    : {log_path}")
    print(f"  Running     : {' '.join(cmd)}")

    with open(log_path, "w") as log_file:
        result = subprocess.run(
            cmd,
            stdout=log_file,
            stderr=log_file,
            text=True,
            timeout=JAR_TIMEOUT_SECONDS,
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"shacl-play exited with code {result.returncode}.\n"
            f"See log for details: {log_path}"
        )

    abs_path = os.path.abspath(output_file)
    print(f"✓ Documentation generated: {abs_path}")
    return abs_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate SHACL documentation using the shacl-play JAR."
    )
    parser.add_argument("--shapes-file", default=DEFAULT_SHAPES_FILE,
                        help=f"Input shapes file (default: {DEFAULT_SHAPES_FILE})")

    parser.add_argument("--output-file", default=DEFAULT_OUTPUT_FILE,
                        help=f"Destination file (default: {DEFAULT_OUTPUT_FILE})")

    parser.add_argument("--language", default="en",
                        help="2-letter language code (default: en)")

    parser.add_argument("--diagram", action="store_true", default=False,
                        help="Include the UML diagram in the output")

    parser.add_argument("--format", dest="output_format", default="html",
                        choices=["html", "pdf", "xml"],
                        help="Output format (default: html)")

    parser.add_argument("--hide", action="store_true", default=False,
                        help="Hide datatype properties from the output")

    parser.add_argument("--jar-path", default=SHACL_PLAY_JAR_PATH,
                        help="Override the path to the shacl-play JAR file")

    args = parser.parse_args()

    try:
        generate_documentation(
            shapes_file=args.shapes_file,
            output_file=args.output_file,
            language=args.language,
            include_diagram=args.diagram,
            hide_datatype_properties=args.hide,
            output_format=args.output_format,
            jar_path=args.jar_path,
        )
    except (FileNotFoundError, RuntimeError) as err:
        print(f"\n✗ Error: {err}", file=sys.stderr)
        sys.exit(1)