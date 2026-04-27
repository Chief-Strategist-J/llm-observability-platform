from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from typing import Optional

from application.api.v1.database_api import DatabaseAPI
from application.api.v1.schema_registry_api import SchemaRegistryAPI
from application.api.v1.event_handler_api import EventHandlerAPI, SchemaAwareEventHandlerAPI
from application.api.v1.producer_api import ProducerAPI
from application.api.v1.consumer_api import ConsumerAPI
from domain.ports.database_port import DatabasePort
from domain.ports.schema_registry_port import SchemaRegistryPort
from domain.ports.producer_port import ProducerPort
from domain.ports.consumer_port import ConsumerPort
from domain.services.event_handler import EventHandler
from domain.services.schema_aware_event_handler import SchemaAwareEventHandler


security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Messaging API",
    description="REST API for messaging operations including database, schema registry, and event handling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def get_database_port() -> DatabasePort:
    raise NotImplementedError("DatabasePort implementation not injected")


def get_schema_registry_port() -> SchemaRegistryPort:
    raise NotImplementedError("SchemaRegistryPort implementation not injected")


def get_event_handler() -> EventHandler:
    raise NotImplementedError("EventHandler implementation not injected")


def get_schema_aware_event_handler() -> SchemaAwareEventHandler:
    raise NotImplementedError("SchemaAwareEventHandler implementation not injected")


def get_producer_port() -> ProducerPort:
    raise NotImplementedError("ProducerPort implementation not injected")


def get_consumer_port() -> ConsumerPort:
    raise NotImplementedError("ConsumerPort implementation not injected")


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    token = credentials.credentials
    if token == "your-secret-token":
        return token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.get("/health")
@limiter.limit("100/minute")
async def health_check():
    return {"status": "healthy", "service": "messaging-api"}


@app.get("/")
@limiter.limit("100/minute")
async def root():
    return {
        "message": "Messaging API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


database_api = DatabaseAPI(get_database_port())
schema_registry_api = SchemaRegistryAPI(get_schema_registry_port())
event_handler_api = EventHandlerAPI(get_event_handler())
schema_aware_event_handler_api = SchemaAwareEventHandlerAPI(get_schema_aware_event_handler())
producer_api = ProducerAPI(get_producer_port())
consumer_api = ConsumerAPI(get_consumer_port())

app.include_router(database_api.router, prefix="/api/v1/database", tags=["Database"])
app.include_router(schema_registry_api.router, prefix="/api/v1/schema-registry", tags=["Schema Registry"])
app.include_router(event_handler_api.router, prefix="/api/v1/event-handler", tags=["Event Handler"])
app.include_router(schema_aware_event_handler_api.router, prefix="/api/v1/schema-aware-event-handler", tags=["Schema Aware Event Handler"])
app.include_router(producer_api.router, prefix="/api/v1/producer", tags=["Producer"])
app.include_router(consumer_api.router, prefix="/api/v1/consumer", tags=["Consumer"])
