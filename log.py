import logging
import pathlib
import datetime
import sys

LOG_DIR = pathlib.Path("logs")
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"ai_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
    force=True,
)
