from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.orm import Session

from database import engine, SessionLocal
import models
from routers import servers, metrics, alerts


def seed_database(db: Session):
    if db.query(models.Server).count() > 0:
        return

    sample_servers = [
        models.Server(hostname="web-01",      ip_address="10.0.1.10", rack="A1",
                      datacenter_zone="Zone-1", role="web",
                      status=models.ServerStatus.online),
        models.Server(hostname="web-02",      ip_address="10.0.1.11", rack="A1",
                      datacenter_zone="Zone-1", role="web",
                      status=models.ServerStatus.online),
        models.Server(hostname="db-primary",  ip_address="10.0.2.10", rack="B1",
                      datacenter_zone="Zone-1", role="database",
                      status=models.ServerStatus.online),
        models.Server(hostname="db-replica",  ip_address="10.0.2.11", rack="B2",
                      datacenter_zone="Zone-1", role="database",
                      status=models.ServerStatus.online),
        models.Server(hostname="storage-01",  ip_address="10.0.3.10", rack="C1",
                      datacenter_zone="Zone-2", role="storage",
                      status=models.ServerStatus.online),
        models.Server(hostname="cache-01",    ip_address="10.0.4.10", rack="D1",
                      datacenter_zone="Zone-2", role="cache",
                      status=models.ServerStatus.maintenance),
    ]
    db.add_all(sample_servers)
    db.commit()
    print("Database seeded with sample servers.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="DC Monitor API",
    description=(
        "A REST API for monitoring Data Center infrastructure health. "
        "Track servers, ingest real-time metrics, and manage alerts."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(servers.router)
app.include_router(metrics.router)
app.include_router(alerts.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "DC Monitor API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
