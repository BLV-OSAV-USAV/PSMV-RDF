import sys
import os
import subprocess
import datetime
import rdflib

# local imports
from src.python.generate_shacl_documentation import generate_documentation
from src.python.utils.helper_functions import *

def generate_documentaion():
    print("\nWriting documentation using SHACL")
    generate_documentation(
        include_diagram=True
    )

    print(f"\n{"\033[92m"}✓ Documentation generated successfully.{"\033[0m"}")

if __name__ == "__main__":
    generate_documentaion()
