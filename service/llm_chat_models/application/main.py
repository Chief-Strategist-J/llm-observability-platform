import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from .config.settings import API_HOST, API_PORT
from .interaction.api.routes import router
from .interaction.api.admin_routes import admin_router
from .interaction.api.dynamic_routes import dynamic_router
from .core.telemetry.logger import log_event
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Model Service", version="2.0.0", description="AI Model Management and API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(admin_router)
app.include_router(dynamic_router)

@app.on_event("startup")
async def startup_event():
    logger.info("event=service_startup host=%s port=%d", API_HOST, API_PORT)
    log_event("service_startup", host=API_HOST, port=API_PORT)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("event=service_shutdown")
    log_event("service_shutdown")

@app.get("/health")
async def health_check():
    logger.info("event=health_check")
    return {"status": "healthy", "version": "2.0.0"}

try:
    FastAPIInstrumentor.instrument_app(app)
    logger.info("event=instrumentation_enabled")
    log_event("instrumentation_enabled")
except Exception as e:
    logger.error("event=instrumentation_failed error=%s", str(e))
    log_event("instrumentation_failed", error=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)

