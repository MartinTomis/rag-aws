from fastapi import FastAPI
from src.api import ingest
from src.api import query
from src.api import documents
import logging
from pythonjsonlogger import jsonlogger
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app, endpoint="/custom-metrics")

# Set up structured logging
logger = logging.getLogger()
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()

log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

# Register router
app.include_router(ingest.router, prefix="/ingest")
app.include_router(query.router, prefix="/query")
app.include_router(documents.router, prefix="/documents")