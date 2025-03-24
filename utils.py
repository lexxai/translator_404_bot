import logging
from pathlib import Path
from tomllib import load as load_toml

logger = logging.getLogger("bot." + __name__)


def get_version():
    pyproject_toml = Path(__file__).parent / "pyproject.toml"
    try:
        if not pyproject_toml.exists():
            raise FileNotFoundError
        with pyproject_toml.open("rb") as f:
            return load_toml(f)["tool"]["poetry"]["version"]
    except Exception as e:
        logger.error(e)
        return "0.0.1-dev"
