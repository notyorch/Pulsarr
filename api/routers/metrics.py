from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models import Server, Metric, Alert, AlertSeverity
from schemas import MetricCreate, MetricOut, MetricSummary

router = APIRouter(prefix="/servers/{server_id}/metrics", tags=["Metrics"])

THRESHOLDS = {
    "cpu_usage":    {"warning": 75.0, "critical": 90.0},
    "memory_usage": {"warning": 80.0, "critical": 95.0},
    "disk_usage":   {"warning": 80.0, "critical": 90.0},
    "temperature":  {"warning": 70.0, "critical": 85.0},
}


def _auto_generate_alerts(db: Session, server: Server, metric: Metric):
    checks = {
        "cpu_usage":    metric.cpu_usage,
        "memory_usage": metric.memory_usage,
        "disk_usage":   metric.disk_usage,
        "temperature":  metric.temperature,
    }
    for metric_name, value in checks.items():
        limits = THRESHOLDS[metric_name]
        severity = None
        threshold = None

        if value >= limits["critical"]:
            severity = AlertSeverity.critical
            threshold = limits["critical"]
        elif value >= limits["warning"]:
            severity = AlertSeverity.warning
            threshold = limits["warning"]

        if severity:
            alert = Alert(
                server_id=server.id,
                severity=severity,
                metric=metric_name,
                message=(
                    f"{server.hostname}: {metric_name.replace('_', ' ').title()} "
                    f"is {value:.1f} (threshold: {threshold})"
                ),
                value=value,
                threshold=threshold,
            )
            db.add(alert)


@router.post("/", response_model=MetricOut, status_code=201,
             summary="Record a new metric snapshot")
def record_metric(
    server_id: int,
    payload: MetricCreate,
    db: Session = Depends(get_db)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    metric = Metric(server_id=server_id, **payload.model_dump())
    db.add(metric)
    db.flush()

    _auto_generate_alerts(db, server, metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.get("/", response_model=List[MetricOut], summary="List metrics for a server")
def list_metrics(
    server_id: int,
    hours: int = Query(default=1, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    since = datetime.utcnow() - timedelta(hours=hours)
    metrics = (
        db.query(Metric)
        .filter(Metric.server_id == server_id, Metric.recorded_at >= since)
        .order_by(Metric.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return metrics


@router.get("/latest", response_model=MetricOut, summary="Get latest metric snapshot")
def latest_metric(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    metric = (
        db.query(Metric)
        .filter(Metric.server_id == server_id)
        .order_by(Metric.recorded_at.desc())
        .first()
    )
    if not metric:
        raise HTTPException(status_code=404, detail="No metrics recorded yet.")
    return metric


@router.get("/summary", response_model=MetricSummary, summary="Aggregated stats")
def metric_summary(
    server_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    since = datetime.utcnow() - timedelta(hours=hours)
    result = (
        db.query(
            func.avg(Metric.cpu_usage).label("avg_cpu"),
            func.avg(Metric.memory_usage).label("avg_memory"),
            func.avg(Metric.disk_usage).label("avg_disk"),
            func.avg(Metric.temperature).label("avg_temperature"),
            func.max(Metric.cpu_usage).label("max_cpu"),
            func.max(Metric.temperature).label("max_temperature"),
            func.count(Metric.id).label("sample_count"),
        )
        .filter(Metric.server_id == server_id, Metric.recorded_at >= since)
        .first()
    )

    if not result or result.sample_count == 0:
        raise HTTPException(status_code=404, detail="No metrics in the requested window.")

    return MetricSummary(
        server_id=server_id,
        hostname=server.hostname,
        avg_cpu=round(result.avg_cpu, 2),
        avg_memory=round(result.avg_memory, 2),
        avg_disk=round(result.avg_disk, 2),
        avg_temperature=round(result.avg_temperature, 2),
        max_cpu=round(result.max_cpu, 2),
        max_temperature=round(result.max_temperature, 2),
        sample_count=result.sample_count,
    )
