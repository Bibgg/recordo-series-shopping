from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .main import Base, OrderRow, engine, get_db, require_admin

router = APIRouter(prefix="/api/v1", tags=["village-logistics"])

class DeliveryZone(Base):
    __tablename__ = "delivery_zones"
    __table_args__ = (UniqueConstraint("district", "municipality", "ward", name="uq_delivery_zone"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    district: Mapped[str] = mapped_column(String(80), nullable=False)
    municipality: Mapped[str] = mapped_column(String(100), nullable=False)
    ward: Mapped[str] = mapped_column(String(20), default="*")
    delivery_fee_npr: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Rider(Base):
    __tablename__ = "riders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(40), default="motorcycle")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class DeliveryTask(Base):
    __tablename__ = "delivery_tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)
    rider_id: Mapped[str] = mapped_column(ForeignKey("riders.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="assigned")
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)

class ZoneCreate(BaseModel):
    district: str = Field(min_length=2, max_length=80)
    municipality: str = Field(min_length=2, max_length=100)
    ward: str = Field(default="*", max_length=20)
    delivery_fee_npr: int = Field(ge=0, le=100000)
    
class RiderCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=20)
    vehicle_type: str = Field(default="motorcycle", max_length=40)

class AssignRider(BaseModel):
    rider_id: str

class DeliveryStatus(BaseModel):
    status: str

DELIVERY_STATES = {"assigned", "picked_up", "out_for_delivery", "delivered", "failed", "returned"}

@router.get("/delivery-zones")
def get_delivery_zones(db: Session = Depends(get_db)):
    zones = db.scalars(select(DeliveryZone).where(DeliveryZone.is_active.is_(True))).all()
    return [{"id": z.id, "district": z.district, "municipality": z.municipality,
             "ward": z.ward, "delivery_fee_npr": z.delivery_fee_npr, "currency": "NPR"}
            for z in zones]

@router.post("/admin/delivery-zones", status_code=201)
def add_delivery_zone(payload: ZoneCreate, _: None = Depends(require_admin), db: Session = Depends(get_db)):
    import uuid
    zone = DeliveryZone(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(zone)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="This delivery zone already exists.")
    return {"id": zone.id, "district": zone.district, "municipality": zone.municipality,
            "ward": zone.ward, "delivery_fee_npr": zone.delivery_fee_npr, "currency": "NPR"}

@router.post("/admin/riders", status_code=201)
def add_rider(payload: RiderCreate, _: None = Depends(require_admin), db: Session = Depends(get_db)):
    import uuid
    rider = Rider(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(rider)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="A rider with this phone number already exists.")
    return {"id": rider.id, "name": rider.name, "phone": rider.phone, "vehicle_type": rider.vehicle_type}

@router.get("/admin/riders")
def list_riders(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(Rider).order_by(Rider.name)).all()
    return [{"id": r.id, "name": r.name, "phone": r.phone, "vehicle_type": r.vehicle_type,
             "is_active": r.is_active} for r in rows]

@router.post("/admin/orders/{order_code}/assign-rider", status_code=201)
def assign_rider(order_code: str, payload: AssignRider, _: None = Depends(require_admin),
                 db: Session = Depends(get_db)):
    order = db.scalar(select(OrderRow).where(OrderRow.order_code == order_code))
    rider = db.get(Rider, payload.rider_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not rider or not rider.is_active:
        raise HTTPException(status_code=404, detail="Active rider not found")
    task = db.scalar(select(DeliveryTask).where(DeliveryTask.order_id == order.id))
    if task and task.status not in {"failed", "returned"}:
        raise HTTPException(status_code=409, detail="This order already has an active delivery assignment.")
    import uuid
    if task:
        task.rider_id = rider.id
        task.status = "assigned"
        task.assigned_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
    else:
        task = DeliveryTask(id=str(uuid.uuid4()), order_id=order.id, rider_id=rider.id)
        db.add(task)
    order.status = "dispatched"
    db.commit()
    return {"order_code": order_code, "rider_name": rider.name, "rider_phone": rider.phone,
            "delivery_status": task.status}

@router.patch("/admin/deliveries/{order_code}")
def update_delivery(order_code: str, payload: DeliveryStatus, _: None = Depends(require_admin),
                    db: Session = Depends(get_db)):
    if payload.status not in DELIVERY_STATES:
        raise HTTPException(status_code=422, detail="Unsupported delivery status.")
    order = db.scalar(select(OrderRow).where(OrderRow.order_code == order_code))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    task = db.scalar(select(DeliveryTask).where(DeliveryTask.order_id == order.id))
    if not task:
        raise HTTPException(status_code=404, detail="No rider has been assigned yet.")
    task.status = payload.status
    task.updated_at = datetime.now(timezone.utc)
    if payload.status == "delivered":
        order.status = "delivered"
    elif payload.status in {"failed", "returned"}:
        order.status = "confirmed"
    db.commit()
    return {"order_code": order_code, "delivery_status": task.status, "order_status": order.status}
