from fastapi import FastAPI, Request, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, json, logging, os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from models import PegaEvent, EventProcessor, EventStatus
from pega_client import PegaClient

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "events.db"
app = FastAPI(
    title="Pega-Python Integration API",
    description="API providing two-way integration between Pega and Python",
    version="1.0.0"
)

# CORS middleware ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should be more restrictive in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Pega client
pega_client = None
if os.getenv("PEGA_URL"):
    pega_client = PegaClient(
        base_url=os.getenv("PEGA_URL"),
        username=os.getenv("PEGA_USERNAME"),
        password=os.getenv("PEGA_PASSWORD"),
        api_key=os.getenv("PEGA_API_KEY")
    )

event_processor = EventProcessor(pega_client)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        received_at TEXT NOT NULL,
        case_id TEXT,
        event TEXT,
        payload_json TEXT NOT NULL,
        status TEXT DEFAULT 'received',
        processed_at TEXT,
        processing_result TEXT
    )
    """)
    
    # Add indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_case_id ON events(case_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_event ON events(event)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_received_at ON events(received_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_status ON events(status)")
    
    conn.commit()
    conn.close()

init_db()

@app.get("/health")
def health_check():
    return {"status": "ok"}

async def process_event_background(event_id: int):
    """Background event processing"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Get event
        cur.execute("SELECT id, received_at, case_id, event, payload_json FROM events WHERE id = ?", (event_id,))
        row = cur.fetchone()
        
        if not row:
            logger.error(f"Event {event_id} not found")
            return
            
        event = PegaEvent.from_db_row(row)
        
        # Update status to processing
        cur.execute("UPDATE events SET status = ? WHERE id = ?", ("processing", event_id))
        conn.commit()
        
        # Process event
        result = event_processor.process_event(event)
        
        # Save result
        cur.execute(
            "UPDATE events SET status = ?, processed_at = ?, processing_result = ? WHERE id = ?",
            (event.status.value, datetime.utcnow().isoformat() + "Z", json.dumps(result), event_id)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Event {event_id} processed successfully: {result}")
        
    except Exception as e:
        logger.error(f"Failed to process event {event_id}: {e}")
        
        # Save error state
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "UPDATE events SET status = ?, processed_at = ?, processing_result = ? WHERE id = ?",
            ("failed", datetime.utcnow().isoformat() + "Z", json.dumps({"error": str(e)}), event_id)
        )
        conn.commit()
        conn.close()

@app.post("/webhook/pega")
async def pega_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    case_id = data.get("caseId")
    event = data.get("event")
    if not case_id or not event:
        raise HTTPException(status_code=400, detail="Fields 'caseId' and 'event' are required")

    logger.info(f"Received from PEGA - Case: {case_id}, Event: {event}")

    # Save event to database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (received_at, case_id, event, payload_json) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(timespec="seconds") + "Z", str(case_id), str(event), json.dumps(data))
    )
    event_id = cur.lastrowid
    conn.commit()
    conn.close()

    # Add to background processing
    background_tasks.add_task(process_event_background, event_id)

    return JSONResponse(content={
        "status": "received", 
        "eventId": event_id,
        "message": f"Event {event} for case {case_id} queued for processing"
    })

@app.get("/events")
def list_events(
    limit: int = Query(10, ge=1, le=100), 
    event: Optional[str] = None,
    status: Optional[str] = None,
    case_id: Optional[str] = None
) -> List[Dict]:
    """List events with advanced filtering"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    query = "SELECT id, received_at, case_id, event, payload_json, status, processed_at, processing_result FROM events WHERE 1=1"
    params = []
    
    if event:
        query += " AND event = ?"
        params.append(event)
        
    if status:
        query += " AND status = ?"
        params.append(status)
        
    if case_id:
        query += " AND case_id = ?"
        params.append(case_id)
    
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], 
            "received_at": r[1], 
            "caseId": r[2], 
            "event": r[3], 
            "payload": json.loads(r[4]),
            "status": r[5],
            "processed_at": r[6],
            "processing_result": json.loads(r[7]) if r[7] else None
        }
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

@app.post("/pega/case")
async def create_pega_case(
    case_type: str, 
    data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Create new case in Pega"""
    if not pega_client:
        raise HTTPException(status_code=503, detail="Pega client not configured")
    
    try:
        result = pega_client.create_case(case_type, data)
        if result:
            logger.info(f"Case created in Pega: {result}")
            return JSONResponse(content={"status": "success", "case": result})
        else:
            raise HTTPException(status_code=500, detail="Failed to create case in Pega")
    except Exception as e:
        logger.error(f"Error creating Pega case: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/pega/case/{case_id}")
async def update_pega_case(case_id: str, data: Dict[str, Any]):
    """Update case in Pega"""
    if not pega_client:
        raise HTTPException(status_code=503, detail="Pega client not configured")
    
    try:
        result = pega_client.update_case(case_id, data)
        if result:
            return JSONResponse(content={"status": "success", "case": result})
        else:
            raise HTTPException(status_code=500, detail="Failed to update case in Pega")
    except Exception as e:
        logger.error(f"Error updating Pega case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pega/case/{case_id}/note")
async def add_pega_case_note(case_id: str, note: str):
    """Add note to Pega case"""
    if not pega_client:
        raise HTTPException(status_code=503, detail="Pega client not configured")
    
    try:
        success = pega_client.add_case_note(case_id, note)
        if success:
            return JSONResponse(content={"status": "success", "message": "Note added"})
        else:
            raise HTTPException(status_code=500, detail="Failed to add note to Pega case")
    except Exception as e:
        logger.error(f"Error adding note to Pega case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pega/case/{case_id}/action/{action_id}")
async def execute_pega_case_action(case_id: str, action_id: str, data: Dict[str, Any] = None):
    """Execute action in Pega case"""
    if not pega_client:
        raise HTTPException(status_code=503, detail="Pega client not configured")
    
    try:
        success = pega_client.execute_case_action(case_id, action_id, data)
        if success:
            return JSONResponse(content={"status": "success", "message": f"Action {action_id} executed"})
        else:
            raise HTTPException(status_code=500, detail="Failed to execute action in Pega")
    except Exception as e:
        logger.error(f"Error executing action {action_id} on Pega case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events/{event_id}")
def get_event(event_id: int) -> Dict:
    """Get details of a specific event"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, received_at, case_id, event, payload_json, status, processed_at, processing_result FROM events WHERE id = ?",
        (event_id,)
    )
    row = cur.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "id": row[0],
        "received_at": row[1],
        "caseId": row[2],
        "event": row[3],
        "payload": json.loads(row[4]),
        "status": row[5],
        "processed_at": row[6],
        "processing_result": json.loads(row[7]) if row[7] else None
    }

@app.post("/events/{event_id}/reprocess")
async def reprocess_event(event_id: int, background_tasks: BackgroundTasks):
    """Reprocess failed event"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT status FROM events WHERE id = ?", (event_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if row[0] not in ["failed", "received"]:
        raise HTTPException(status_code=400, detail="Event cannot be reprocessed")
    
    # Reset status and reprocess
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE events SET status = 'received', processed_at = NULL, processing_result = NULL WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    
    background_tasks.add_task(process_event_background, event_id)
    
    return JSONResponse(content={"status": "queued", "message": "Event queued for reprocessing"})

@app.get("/dashboard")
def dashboard() -> Dict:
    """Summary information for dashboard"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Last 24 hours
    since_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
    
    # Total event count
    cur.execute("SELECT COUNT(*) FROM events WHERE received_at >= ?", (since_24h,))
    total_24h = cur.fetchone()[0]
    
    # Distribution by status
    cur.execute("""
        SELECT status, COUNT(*) 
        FROM events 
        WHERE received_at >= ? 
        GROUP BY status
    """, (since_24h,))
    status_breakdown = [{"status": r[0], "count": r[1]} for r in cur.fetchall()]
    
    # Distribution by event types
    cur.execute("""
        SELECT event, COUNT(*) 
        FROM events 
        WHERE received_at >= ?
        GROUP BY event 
        ORDER BY COUNT(*) DESC
    """, (since_24h,))
    event_breakdown = [{"event": r[0], "count": r[1]} for r in cur.fetchall()]
    
    # Last 7 days trend (daily)
    cur.execute("""
        SELECT DATE(received_at) as day, COUNT(*) 
        FROM events 
        WHERE received_at >= ?
        GROUP BY DATE(received_at) 
        ORDER BY day DESC
    """, ((datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",))
    daily_trend = [{"day": r[0], "count": r[1]} for r in cur.fetchall()]
    
    conn.close()
    
    return {
        "period": "last_24_hours",
        "total_events": total_24h,
        "status_breakdown": status_breakdown,
        "event_breakdown": event_breakdown,
        "daily_trend": daily_trend,
        "pega_connection": "connected" if pega_client else "not_configured"
    }
