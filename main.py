from typing import List, Optional
from datetime import datetime
import json
import secrets
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, create_engine, Session, select, text
from contextlib import asynccontextmanager

DB_URL = "sqlite:///./orders.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})


class Restaurant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    token: str = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    restaurant_id: int = Field(foreign_key="restaurant.id")
    table: Optional[str] = None
    items_json: str  # store items as JSON string for MVP
    total: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    printed_at: Optional[datetime] = None  # mark when sent to device


class JsLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    time: str
    type: str
    message: str
    stack: Optional[str] = None
    user_agent: Optional[str] = None
    source: Optional[str] = None
    line: Optional[int] = None
    col: Optional[int] = None
    reason: Optional[str] = None


def create_db():
    SQLModel.metadata.create_all(engine)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield


app = FastAPI(lifespan=lifespan)


# Restaurant Management Endpoints
@app.post("/api/restaurants", response_model=dict)
def create_restaurant(payload: dict):
    """Create a new restaurant with auto-generated token"""
    try:
        name = payload.get("name", "").strip()
        if not name:
            raise HTTPException(400, "Restaurant name is required")

        # Generate unique token
        token = secrets.token_urlsafe(16)

        restaurant = Restaurant(name=name, token=token)

        with Session(engine) as s:
            s.add(restaurant)
            s.commit()
            s.refresh(restaurant)
            return {
                "ok": True,
                "id": restaurant.id,
                "name": restaurant.name,
                "token": restaurant.token,
            }
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(400, "Restaurant name already exists")
        raise HTTPException(400, "Invalid payload")


@app.get("/api/restaurants", response_model=List[dict])
def list_restaurants():
    """List all restaurants"""
    with Session(engine) as s:
        restaurants = s.exec(
            select(Restaurant).order_by(Restaurant.created_at.desc())
        ).all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "token": r.token,
                "created_at": r.created_at.isoformat() + "Z",
            }
            for r in restaurants
        ]


@app.get("/api/restaurants/verify/{token}", response_model=dict)
def verify_restaurant_token(token: str):
    """Verify restaurant token and return restaurant info"""
    with Session(engine) as s:
        restaurant = s.exec(select(Restaurant).where(Restaurant.token == token)).first()
        if not restaurant:
            raise HTTPException(404, "Invalid token")
        return {"id": restaurant.id, "name": restaurant.name, "token": restaurant.token}


@app.post("/api/orders", response_model=dict)
def create_order(payload: dict):
    """
    payload example:
    {
      "restaurant_id": 1,
      "table": "5",
      "items": [{"qty":2,"name":"Latte","price":120},{"qty":1,"name":"Brownie","price":80}],
      "total": 320
    }
    """
    try:
        restaurant_id = payload.get("restaurant_id")
        if not restaurant_id:
            raise HTTPException(400, "restaurant_id is required")

        items = payload.get("items", [])
        order = Order(
            restaurant_id=int(restaurant_id),
            table=payload.get("table"),
            items_json=json.dumps(items, ensure_ascii=False),
            total=float(payload["total"]),
        )
    except Exception as e:
        raise HTTPException(400, f"Invalid payload: {str(e)}")

    with Session(engine) as s:
        s.add(order)
        s.commit()
        s.refresh(order)
        return {"ok": True, "id": order.id}


@app.get("/api/orders/poll", response_model=List[dict])
def poll_orders(token: str, limit: int = 5):
    """
    Return a few unprinted orders for the specified restaurant token and mark them as printed immediately
    so they don't reprint on the next poll.
    """
    with Session(engine) as s:
        # First verify the token and get restaurant
        restaurant = s.exec(select(Restaurant).where(Restaurant.token == token)).first()
        if not restaurant:
            raise HTTPException(404, "Invalid token")

        # Get orders for this restaurant only
        orders = s.exec(
            select(Order)
            .where(Order.restaurant_id == restaurant.id)
            .where(Order.printed_at.is_(None))
            .order_by(Order.id.asc())
            .limit(limit)
        ).all()
        result = []
        now = datetime.utcnow()
        for o in orders:
            result.append(
                {
                    "id": o.id,
                    "table": o.table,
                    "items": json.loads(o.items_json),
                    "total": o.total,
                    "created_at": o.created_at.isoformat() + "Z",
                }
            )
            o.printed_at = now
        if orders:
            s.add_all(orders)
            s.commit()
        return result


@app.post("/api/logs/js")
async def save_js_log(req: Request):
    """Store JavaScript error logs from the frontend"""
    try:
        data = await req.json()
        print("JS LOG:", data)  # debug

        # Create JsLog entry
        js_log = JsLog(
            time=data.get("time"),
            type=data.get("type"),
            message=data.get("message"),
            stack=data.get("stack"),
            user_agent=data.get("userAgent"),
            source=data.get("source"),
            line=data.get("line"),
            col=data.get("col"),
            reason=data.get("reason"),
        )

        with Session(engine) as s:
            s.add(js_log)
            s.commit()

        return {"ok": True}
    except Exception as e:
        print(f"Error saving JS log: {e}")
        return {"ok": False, "error": str(e)}
