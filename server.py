import os
import json
import time
import hashlib
import uuid
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from screenshot import take_screenshot
from analyzer import analyze_landing_page

app = FastAPI(title="Landing Page Critic")
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_FILE = "data.db"
HISTORY_DIR = "history"
CACHE_DIR = "cache"
os.makedirs(HISTORY_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS pro_keys (
        key TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        activated_at TEXT,
        is_active INTEGER DEFAULT 1
    )""")
    conn.commit()
    conn.close()

def seed_pro_keys():
    conn = get_db()
    keys = [
        "PRO-ISNODRZLUSWB", "PRO-R0N3YO2UV5UW", "PRO-05YI1ODSVNCP",
        "PRO-AC1SZEI06A7P", "PRO-VDIS6WDAK6D8", "PRO-XXE3MMT8TL9D",
        "PRO-EDMA26QOT2LG", "PRO-YOSHG2DFZ8SB", "PRO-J3XWHBJCQQDL",
        "PRO-JYO1VVUTU11V"
    ]
    now = datetime.now().isoformat()
    for key in keys:
        try:
            conn.execute("INSERT OR IGNORE INTO pro_keys (key, created_at, is_active) VALUES (?, ?, 1)", (key, now))
        except:
            pass
    conn.commit()
    conn.close()

init_db()
seed_pro_keys()

rate_limits = {}
FREE_LIMIT = 3
RATE_WINDOW = 3600

def is_valid_pro(key):
    if not key:
        return False
    conn = get_db()
    row = conn.execute("SELECT is_active FROM pro_keys WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row is not None and row["is_active"] == 1

def activate_pro(key):
    conn = get_db()
    conn.execute("UPDATE pro_keys SET activated_at = ? WHERE key = ?", (datetime.now().isoformat(), key))
    conn.commit()
    conn.close()

class AnalyzeRequest(BaseModel):
    url: str
    api_key: str = ""
    pro_key: str = ""

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest, req: Request):
    api_key = request.api_key
    is_pro = False

    if request.pro_key:
        if is_valid_pro(request.pro_key):
            api_key = os.environ.get("GROQ_API_KEY", "")
            is_pro = True
            activate_pro(request.pro_key)
        else:
            raise HTTPException(status_code=400, detail="Invalid Pro key")

    if not api_key:
        raise HTTPException(status_code=400, detail="API key required")

    client_ip = req.client.host
    now = time.time()

    if not is_pro:
        if client_ip in rate_limits:
            timestamps = [t for t in rate_limits[client_ip] if now - t < RATE_WINDOW]
            if len(timestamps) >= FREE_LIMIT:
                raise HTTPException(status_code=429, detail="Free limit: 3 per hour. Get Pro for unlimited.")
            rate_limits[client_ip] = timestamps
        else:
            rate_limits[client_ip] = []
        rate_limits[client_ip].append(now)

    url = request.url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_file = f"{CACHE_DIR}/{url_hash}.json"

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
        age_minutes = (now - cached.get("timestamp_unix", 0)) / 60
        if age_minutes < 1440:
            return cached

    screenshot_path = f"history/screenshot_{uuid.uuid4().hex[:8]}.png"
    try:
        await take_screenshot(url, screenshot_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to capture: {str(e)}")

    try:
        result = analyze_landing_page(screenshot_path, "", url, api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    analysis_id = uuid.uuid4().hex[:8]
    record = {
        "id": analysis_id,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "timestamp_unix": now,
        "result": result,
        "screenshot": screenshot_path,
        "is_pro": is_pro
    }

    with open(f"{HISTORY_DIR}/{analysis_id}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return record

@app.post("/api/verify-pro")
async def verify_pro(data: dict):
    key = data.get("key", "").strip()
    if is_valid_pro(key):
        return {"valid": True, "message": "Pro activated"}
    return {"valid": False, "message": "Invalid key"}

@app.post("/api/create-pro-key")
async def create_pro_key():
    new_key = f"PRO-{uuid.uuid4().hex[:12].upper()}"
    conn = get_db()
    conn.execute("INSERT INTO pro_keys (key, created_at, is_active) VALUES (?, ?, 1)", (new_key, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return {"key": new_key}

@app.get("/api/keys")
async def get_keys():
    conn = get_db()
    rows = conn.execute("SELECT key, created_at, activated_at, is_active FROM pro_keys ORDER BY created_at DESC").fetchall()
    conn.close()
    return [{"key": r["key"], "created": r["created_at"], "activated": r["activated_at"], "active": bool(r["is_active"])} for r in rows]

@app.get("/api/history")
async def get_history():
    records = []
    for filename in sorted(os.listdir(HISTORY_DIR), reverse=True):
        if filename.endswith(".json"):
            with open(f"{HISTORY_DIR}/{filename}", "r", encoding="utf-8") as f:
                records.append(json.load(f))
    return records[:50]

@app.get("/api/history/{analysis_id}")
async def get_analysis(analysis_id: str):
    filepath = f"{HISTORY_DIR}/{analysis_id}.json"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Not found")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/screenshot/{filename}")
async def get_screenshot(filename: str):
    filepath = f"{HISTORY_DIR}/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(filepath, media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
