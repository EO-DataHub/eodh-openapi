import logging
import os

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO").upper(),
    handlers=[logging.StreamHandler()],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("eodh-openapi")
