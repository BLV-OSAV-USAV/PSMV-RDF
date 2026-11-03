"""SHACL Play JAR management: version config and download."""

import os
import tempfile
import tomllib

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))


def _load_docgen_config() -> dict:
    """Read [tool.shacl-docgen] from the project's pyproject.toml."""
    pyproject = os.path.join(ROOT_DIR, "pyproject.toml")
    with open(pyproject, "rb") as f:
        config = tomllib.load(f).get("tool", {}).get("shacl-docgen")
    if config is None:
        raise RuntimeError(f"No [tool.shacl-docgen] section in {pyproject}")
    return config


DOCGEN_CONFIG = _load_docgen_config()

# Env var wins (handy for testing a new release locally), else pyproject.toml
SHACL_PLAY_VERSION = (
    os.environ.get("SHACL_PLAY_VERSION") or DOCGEN_CONFIG["shacl_play_version"]
)

SHACL_PLAY_JAR_PATH = os.path.join(
    ROOT_DIR,
    "service",
    "shacl_play",
    f"shacl-play-app-{SHACL_PLAY_VERSION}-onejar.jar",
)

SHACL_PLAY_JAR_URL = (
    f"https://github.com/sparna-git/shacl-play/releases/download/"
    f"{SHACL_PLAY_VERSION}/"
    f"shacl-play-app-{SHACL_PLAY_VERSION}-onejar.jar"
)


def ensure_jar(jar_path: str = SHACL_PLAY_JAR_PATH) -> str:
    """Return the path to the SHACL Play JAR, downloading it if missing."""
    if os.path.isfile(jar_path):
        return jar_path

    jar_dir = os.path.dirname(os.path.abspath(jar_path))
    os.makedirs(jar_dir, exist_ok=True)

    print(f"  JAR not found locally. Downloading v{SHACL_PLAY_VERSION} …")
    fd, tmp_path = tempfile.mkstemp(dir=jar_dir, suffix=".part")
    try:
        with os.fdopen(fd, "wb") as tmp, requests.get(
            SHACL_PLAY_JAR_URL, stream=True, timeout=60
        ) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=1 << 20):
                tmp.write(chunk)
        os.replace(tmp_path, jar_path)  # atomic on the same filesystem
    except Exception as exc:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise RuntimeError(
            f"Could not download SHACL Play {SHACL_PLAY_VERSION} "
            f"from {SHACL_PLAY_JAR_URL}"
        ) from exc

    print(f"  ✓ JAR cached at: {jar_path}")
    return jar_path