from typing import List, Optional
from datetime import datetime
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, create_engine, Session, select, text
from contextlib import asynccontextmanager

DB_URL = "sqlite:///./orders.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
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


@app.post("/api/orders", response_model=dict)
def create_order(payload: dict):
    """
    payload example:
    {
      "table": "5",
      "items": [{"qty":2,"name":"Latte","price":120},{"qty":1,"name":"Brownie","price":80}],
      "total": 320
    }
    """
    try:
        items = payload.get("items", [])
        order = Order(
            table=payload.get("table"),
            items_json=json.dumps(items, ensure_ascii=False),
            total=float(payload["total"]),
        )
    except Exception:
        raise HTTPException(400, "Invalid payload")

    with Session(engine) as s:
        s.add(order)
        s.commit()
        s.refresh(order)
        return {"ok": True, "id": order.id}


@app.get("/api/orders/poll", response_model=List[dict])
def poll_orders(limit: int = 5):
    """
    Return a few unprinted orders and mark them as printed immediately
    so they don't reprint on the next poll.
    """
    with Session(engine) as s:
        orders = s.exec(
            select(Order)
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
