from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse
import sqlite3, json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

DB_PATH = "events.db"
app = FastAPI()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        received_at TEXT NOT NULL,
        case_id TEXT,
        event TEXT,
        payload_json TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/webhook/pega")
async def pega_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    case_id = data.get("caseId")
    event = data.get("event")
    if not case_id or not event:
        raise HTTPException(status_code=400, detail="Fields 'caseId' and 'event' are required")

    print("Received from PEGA:", data)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (received_at, case_id, event, payload_json) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(timespec="seconds") + "Z", str(case_id), str(event), json.dumps(data))
    )
    conn.commit()
    conn.close()

    return JSONResponse(content={"status": "received"})

@app.get("/events")
def list_events(limit: int = Query(10, ge=1, le=100), event: Optional[str] = None) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if event:
        cur.execute(
            "SELECT id, received_at, case_id, event, payload_json FROM events WHERE event = ? ORDER BY id DESC LIMIT ?",
            (event, limit)
        )
    else:
        cur.execute(
            "SELECT id, received_at, case_id, event, payload_json FROM events ORDER BY id DESC LIMIT ?",
            (limit,)
        )
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "received_at": r[1], "caseId": r[2], "event": r[3], "payload": json.loads(r[4])}
        for r in rows
    ]

@app.get("/metrics")
def metrics():
    since = (datetime.utcnow() - timedelta(days=7)).isoformat(timespec="seconds") + "Z"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM events WHERE received_at >= ?", (since,))
    total = cur.fetchone()[0]
    cur.execute("""
        SELECT event, COUNT(*)
        FROM events
        WHERE received_at >= ?
        GROUP BY event
        ORDER BY COUNT(*) DESC
    """, (since,))
    breakdown = [{"event": r[0], "count": r[1]} for r in cur.fetchall()]
    conn.close()
    return {"since": since, "total": total, "by_event": breakdown}
