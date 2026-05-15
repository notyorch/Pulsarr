from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Server
from schemas import ServerCreate, ServerUpdate, ServerOut

router = APIRouter(prefix="/servers", tags=["Servers"])


@router.get("/", response_model=List[ServerOut], summary="List all servers")
def list_servers(
    zone: str = None,
    role: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Server)
    if zone:
        query = query.filter(Server.datacenter_zone == zone)
    if role:
        query = query.filter(Server.role == role)
    if status:
        query = query.filter(Server.status == status)
    return query.all()


@router.post("/", response_model=ServerOut, status_code=status.HTTP_201_CREATED,
             summary="Register a new server")
def create_server(payload: ServerCreate, db: Session = Depends(get_db)):
    existing = db.query(Server).filter(Server.hostname == payload.hostname).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Server with hostname '{payload.hostname}' already exists."
        )
    server = Server(**payload.model_dump())
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


@router.get("/{server_id}", response_model=ServerOut, summary="Get server by ID")
def get_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")
    return server


@router.patch("/{server_id}", response_model=ServerOut, summary="Update server fields")
def update_server(server_id: int, payload: ServerUpdate, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(server, field, value)
    db.commit()
    db.refresh(server)
    return server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Deregister a server")
def delete_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")
    db.delete(server)
    db.commit()
