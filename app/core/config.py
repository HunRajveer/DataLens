import logging
# it sore logging info meansd who uplode at what time and when export just for more transparency and debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("datalens")