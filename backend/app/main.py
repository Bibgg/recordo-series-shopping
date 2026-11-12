import os
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recordo.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class ProductRow(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    price_npr: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(40), default="piece")
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class OrderRow(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_code: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(80), nullable=False)
    municipality: Mapped[str] = mapped_column(String(100), nullable=False)
    ward: Mapped[str] = mapped_column(String(20), nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(300), nullable=False)
    delivery_note: Mapped[str] = mapped_column(String(300), default="")
    total_npr: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="placed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    items: Mapped[list["OrderItemRow"]] = relationship(back_populates="order", cascade="all, delete-orphan")

class OrderItemRow(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(36), nullable=False)
    product_name: Mapped[str] = mapped_column(String(140), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_npr: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_npr: Mapped[int] = mapped_column(Integer, nullable=False)
    order: Mapped[OrderRow] = relationship(back_populates="items")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Recordo Nepal Shopping API",
    version="0.2.0",
    description="Nepal-first marketplace API. All prices and order totals are NPR.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    expected = os.getenv("ADMIN_API_TOKEN")
    if not expected:
        raise HTTPException(status_code=503, detail="Admin API is not configured. Set ADMIN_API_TOKEN.")
    if not x_admin_token or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Invalid admin token.")

class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=140)
    description: str = Field(default="", max_length=2000)
    category: str = Field(min_length=2, max_length=60)
    price_npr: int = Field(gt=0, le=100000000)
    unit: str = Field(default="piece", max_length=40)
    stock_quantity: int = Field(ge=0, le=1000000)

class OrderLineInput(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=100)

class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=20)
    district: str = Field(min_length=2, max_length=80)
    municipality: str = Field(min_length=2, max_length=100)
    ward: str = Field(min_length=1, max_length=20)
    delivery_address: str = Field(min_length=5, max_length=300)
    delivery_note: str = Field(default="", max_length=300)
    items: list[OrderLineInput] = Field(min_length=1, max_length=30)

class OrderStatusUpdate(BaseModel):
    status: str

ALLOWED_STATUSES = {"confirmed", "packed", "dispatched", "delivered", "cancelled"}

from .logistics import router as logistics_router
app.include_router(logistics_router)

@app.get("/health")
def health():
    return {"ok": True, "service": "recordo-nepal-api", "country": "NP", "currency": "NPR"}

@app.get("/api/v1/config")
def config():
    return {"market": "Nepal", "country_code": "NP", "currency_code": "NPR",
            "currency_symbol": "रु", "supported_languages": ["ne", "en"]}

@app.get("/api/v1/categories")
def categories():
    return [{"id": "vegetables", "name": "Vegetables"},
            {"id": "fruits", "name": "Fruits"},
            {"id": "groceries", "name": "Groceries"},
            {"id": "daily-essentials", "name": "Daily Essentials"}]

@app.get("/api/v1/products")
def products(category: str | None = Query(default=None), db: Session = Depends(get_db)):
    query = select(ProductRow).where(ProductRow.is_active.is_(True)).order_by(ProductRow.name)
    if category:
        query = query.where(ProductRow.category.ilike(category))
    rows = db.scalars(query).all()
    return [{"id": p.id, "name": p.name, "description": p.description,
             "category": p.category, "price_npr": p.price_npr, "currency": "NPR",
             "unit": p.unit, "stock_quantity": p.stock_quantity} for p in rows]

@app.post("/api/v1/admin/products", status_code=201)
def add_product(payload: ProductCreate, _: None = Depends(require_admin), db: Session = Depends(get_db)):
    product = ProductRow(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"id": product.id, "name": product.name, "price_npr": product.price_npr,
            "currency": "NPR", "stock_quantity": product.stock_quantity}

@app.patch("/api/v1/admin/products/{product_id}")
def update_product(product_id: str, payload: ProductCreate, _: None = Depends(require_admin),
                   db: Session = Depends(get_db)):
    product = db.get(ProductRow, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in payload.model_dump().items():
        setattr(product, key, value)
    db.commit()
    return {"ok": True, "id": product.id}

@app.post("/api/v1/orders", status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    # Aggregate duplicate product lines to prevent stock/price inconsistencies.
    quantities: dict[str, int] = {}
    for line in payload.items:
        quantities[line.product_id] = quantities.get(line.product_id, 0) + line.quantity
    try:
        total = 0
        order = OrderRow(
            order_code="RC" + uuid.uuid4().hex[:10].upper(),
            customer_name=payload.customer_name, phone=payload.phone,
            district=payload.district, municipality=payload.municipality, ward=payload.ward,
            delivery_address=payload.delivery_address, delivery_note=payload.delivery_note,
            total_npr=0, status="placed",
        )
        for product_id, quantity in quantities.items():
            product = db.get(ProductRow, product_id)
            if not product or not product.is_active:
                raise HTTPException(status_code=400, detail="A selected product is unavailable.")
            if product.stock_quantity < quantity:
                raise HTTPException(status_code=409, detail=f"Insufficient stock for {product.name}.")
            line_total = product.price_npr * quantity
            total += line_total
            product.stock_quantity -= quantity
            order.items.append(OrderItemRow(
                product_id=product.id, product_name=product.name, quantity=quantity,
                unit_price_npr=product.price_npr, line_total_npr=line_total,
            ))
        order.total_npr = total
        db.add(order)
        db.commit()
        db.refresh(order)
        return {"order_code": order.order_code, "status": order.status,
                "total_npr": order.total_npr, "currency": "NPR"}
    except Exception:
        db.rollback()
        raise

@app.get("/api/v1/orders/{order_code}")
def track_order(order_code: str, phone: str = Query(min_length=7, max_length=20),
                db: Session = Depends(get_db)):
    order = db.scalar(select(OrderRow).where(OrderRow.order_code == order_code))
    if not order or not secrets.compare_digest(order.phone, phone):
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_code": order.order_code, "status": order.status, "total_npr": order.total_npr,
            "currency": "NPR", "created_at": order.created_at,
            "items": [{"name": i.product_name, "quantity": i.quantity,
                       "unit_price_npr": i.unit_price_npr, "line_total_npr": i.line_total_npr}
                      for i in order.items]}

@app.get("/api/v1/admin/orders")
def admin_orders(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(OrderRow).order_by(OrderRow.created_at.desc()).limit(200)).all()
    return [{"order_code": o.order_code, "customer_name": o.customer_name, "phone": o.phone,
             "district": o.district, "municipality": o.municipality, "ward": o.ward,
             "delivery_address": o.delivery_address, "total_npr": o.total_npr, "status": o.status}
            for o in rows]

@app.patch("/api/v1/admin/orders/{order_code}")
def update_order_status(order_code: str, payload: OrderStatusUpdate,
                        _: None = Depends(require_admin), db: Session = Depends(get_db)):
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail="Unsupported order status")
    order = db.scalar(select(OrderRow).where(OrderRow.order_code == order_code))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in {"delivered", "cancelled"}:
        raise HTTPException(status_code=409, detail="This order is already closed")
    if payload.status == "cancelled":
        for item in order.items:
            product = db.get(ProductRow, item.product_id)
            if product:
                product.stock_quantity += item.quantity
    order.status = payload.status
    db.commit()
    return {"ok": True, "order_code": order.order_code, "status": order.status}
