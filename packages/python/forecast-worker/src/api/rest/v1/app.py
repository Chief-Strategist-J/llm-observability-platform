from fastapi import FastAPI
from prometheus_client import make_asgi_app
from api.rest.v1.router import router
from api.index import health as get_health, trigger_workflow as trigger_forecast_workflow
from api.rest.v1.handlers.forecasts import (
    get_redis,
    get_clickhouse,
    get_postgres,
    get_timesfm,
    authenticate_jwt,
)

app = FastAPI(title="Temporal Forecast Worker API", version="1.0.0")
app.mount("/metrics", make_asgi_app())
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
