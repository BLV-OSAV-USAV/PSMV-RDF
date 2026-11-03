import sys
import os
import subprocess
import datetime
import rdflib

# local imports
from src.python.utils.shacl_play import ensure_jar, SHACL_PLAY_JAR_PATH
from src.python.utils.helper_functions import *

def generate_documentaion():
    print("\nWriting documentation using SHACL")
    generate_documentation(
        include_diagram=True
    )

    print(f"\n{"\033[92m"}✓ Documentation generated successfully.{"\033[0m"}")

if __name__ == "__main__":
    generate_documentaion()
