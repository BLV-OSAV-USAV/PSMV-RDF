from src.python.generate_shacl_documentation import generate_documentation
from src.python.utils.shacl_play import ensure_jar, SHACL_PLAY_JAR_PATH

GREEN = "\033[92m"
RESET = "\033[0m"


def main():
    print("\nWriting documentation using SHACL")
    generate_documentation(include_diagram=True)
    print(f"\n{GREEN}✓ Documentation generated successfully.{RESET}")


if __name__ == "__main__":
    main()