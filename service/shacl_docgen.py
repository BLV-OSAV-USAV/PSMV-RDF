from src.python.generate_shacl_documentation import generate_documentation

GREEN = "\033[92m"
RESET = "\033[0m"


def main():
    print("\nWriting documentation using SHACL")
    generate_documentation(include_diagram=True)
    print(f"\n{GREEN}✓ Documentation generated successfully.{RESET}")


if __name__ == "__main__":
    main()