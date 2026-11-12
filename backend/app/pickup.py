"""Area-based order collection and batch pickup workflow.

Orders are grouped by the seller/product pickup_area, never by the buyer's
delivery address. A batch can be created once the configurable threshold is met.
"""
import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, select, func
from sqlalchemy.orm import Mapped, Session, mapped_column

from .main import Base, OrderRow, OrderItemRow, engine, get_db, require_admin

router = APIRouter(prefix="/api/v1", tags=["pickup-collection"])
DEFAULT_THRESHOLD = int(os.getenv("PICKUP_ORDER_THRESHOLD", "50"))
OPEN_ORDER_STATES = ("placed", "confirmed", "packed")

class PickupBatch(Base):
    __tablename__ = "pickup_batches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_code: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    pickup_area: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    target_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=DEFAULT_THRESHOLD)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="collecting")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class PickupBatchOrder(Base):
    __tablename__ = "pickup_batch_orders"
    __table_args__ = (UniqueConstraint("batch_id", "order_id", name="uq_pickup_batch_order"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    batch_id: Mapped[str] = mapped_column(ForeignKey("pickup_batches.id"), nullable=False)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=False)
    pickup_area: Mapped[str] = mapped_column(String(120), nullable=False)
    order_code: Mapped[str] = mapped_column(String(24), nullable=False)

class BatchCreate(BaseModel):
    pickup_area: str = Field(min_length=2, max_length=120)
    target_orders: int = Field(default=DEFAULT_THRESHOLD, ge=1, le=10000)
    force: bool = False

class BatchStatusUpdate(BaseModel):
    status: str

Base.metadata.create_all(bind=engine)

BATCH_STATES = {"pickup_scheduled", "picked_up", "at_sorting_center", "sorted", "dispatched", "completed", "cancelled"}

def _area_counts(db: Session):
    rows = db.execute(
        select(OrderItemRow.pickup_area, func.count(func.distinct(OrderRow.id)))
        .join(OrderRow, OrderRow.id == OrderItemRow.order_id)
        .where(OrderRow.status.in_(OPEN_ORDER_STATES))
        .group_by(OrderItemRow.pickup_area)
        .order_by(OrderItemRow.pickup_area)
    ).all()
    return rows

@router.get("/pickup/areas")
def pickup_areas(db: Session = Depends(get_db)):
    """Public, privacy-safe progress board; contains no customer names or phones."""
    result = []
    for area, count in _area_counts(db):
        target = DEFAULT_THRESHOLD
        active_batch = db.scalar(select(PickupBatch).where(
            PickupBatch.pickup_area == area,
            PickupBatch.status.not_in(("completed", "cancelled"))
        ).order_by(PickupBatch.created_at.desc()))
        if active_batch:
            target = active_batch.target_orders
        result.append({
            "pickup_area": area, "ready_orders": int(count), "target_orders": target,
            "remaining_orders": max(target - int(count), 0),
            "progress_percent": min(100, int(count) * 100 // target),
            "ready_for_pickup": int(count) >= target,
            "batch_code": active_batch.batch_code if active_batch else None,
            "batch_status": active_batch.status if active_batch else "collecting",
        })
    return result

@router.get("/admin/pickup/orders")
def pickup_orders(pickup_area: str, _: None = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(
        select(OrderRow.order_code, OrderRow.customer_name, OrderRow.phone, OrderRow.district,
               OrderRow.municipality, OrderRow.ward, OrderRow.delivery_address)
        .join(OrderItemRow, OrderItemRow.order_id == OrderRow.id)
        .where(OrderItemRow.pickup_area == pickup_area, OrderRow.status.in_(OPEN_ORDER_STATES))
        .distinct().order_by(OrderRow.created_at)
    ).all()
    return [{"order_code": r[0], "customer_name": r[1], "phone": r[2], "district": r[3],
             "municipality": r[4], "ward": r[5], "delivery_address": r[6]} for r in rows]

@router.post("/admin/pickup/batches", status_code=201)
def create_pickup_batch(payload: BatchCreate, _: None = Depends(require_admin), db: Session = Depends(get_db)):
    area_orders = db.execute(
        select(OrderRow.id, OrderRow.order_code).join(OrderItemRow, OrderItemRow.order_id == OrderRow.id)
        .where(OrderItemRow.pickup_area == payload.pickup_area, OrderRow.status.in_(OPEN_ORDER_STATES))
        .distinct()
    ).all()
    if len(area_orders) < payload.target_orders and not payload.force:
        raise HTTPException(status_code=409, detail={
            "message": "Pickup target not reached", "ready_orders": len(area_orders),
            "target_orders": payload.target_orders, "remaining_orders": payload.target_orders-len(area_orders)
        })
    if not area_orders:
        raise HTTPException(status_code=409, detail="No orders available for this pickup area.")
    batch = PickupBatch(id=str(uuid.uuid4()), batch_code="PK" + uuid.uuid4().hex[:8].upper(),
                        pickup_area=payload.pickup_area, target_orders=payload.target_orders,
                        status="pickup_scheduled")
    db.add(batch)
    for order_id, order_code in area_orders:
        db.add(PickupBatchOrder(id=str(uuid.uuid4()), batch_id=batch.id, order_id=order_id,
                                pickup_area=payload.pickup_area, order_code=order_code))
    db.commit()
    return {"batch_code": batch.batch_code, "pickup_area": batch.pickup_area,
            "order_count": len(area_orders), "target_orders": batch.target_orders,
            "status": batch.status}

@router.get("/admin/pickup/batches")
def list_pickup_batches(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    batches = db.scalars(select(PickupBatch).order_by(PickupBatch.created_at.desc()).limit(200)).all()
    return [{"batch_code": b.batch_code, "pickup_area": b.pickup_area, "target_orders": b.target_orders,
             "status": b.status, "order_count": db.scalar(select(func.count(PickupBatchOrder.id)).where(PickupBatchOrder.batch_id == b.id)) or 0}
            for b in batches]

@router.patch("/admin/pickup/batches/{batch_code}")
def update_pickup_batch(batch_code: str, payload: BatchStatusUpdate,
                        _: None = Depends(require_admin), db: Session = Depends(get_db)):
    if payload.status not in BATCH_STATES:
        raise HTTPException(status_code=422, detail="Unsupported pickup batch status.")
    batch = db.scalar(select(PickupBatch).where(PickupBatch.batch_code == batch_code))
    if not batch:
        raise HTTPException(status_code=404, detail="Pickup batch not found.")
    batch.status = payload.status
    batch.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"batch_code": batch.batch_code, "status": batch.status}
