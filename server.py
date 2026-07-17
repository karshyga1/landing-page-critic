import os
import json
import time
import hashlib
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from screenshot import take_screenshot
from analyzer import analyze_landing_page

app = FastAPI(title="Landing Page Critic")
app.mount("/static", StaticFiles(directory="static"), name="static")

HISTORY_DIR = "history"
CACHE_DIR = "cache"
PRO_KEYS_FILE = "pro_keys.json"
os.makedirs(HISTORY_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_PRO_KEYS = {
    "PRO-ISNODRZLUSWB": {"created": "2026-07-17", "used": False},
    "PRO-R0N3YO2UV5UW": {"created": "2026-07-17", "used": False},
    "PRO-05YI1ODSVNCP": {"created": "2026-07-17", "used": False},
    "PRO-AC1SZEI06A7P": {"created": "2026-07-17", "used": False},
    "PRO-VDIS6WDAK6D8": {"created": "2026-07-17", "used": False},
    "PRO-XXE3MMT8TL9D": {"created": "2026-07-17", "used": False},
    "PRO-EDMA26QOT2LG": {"created": "2026-07-17", "used": False},
    "PRO-YOSHG2DFZ8SB": {"created": "2026-07-17", "used": False},
    "PRO-J3XWHBJCQQDL": {"created": "2026-07-17", "used": False},
    "PRO-JYO1VVUTU11V": {"created": "2026-07-17", "used": False}
}

rate_limits = {}
FREE_LIMIT = 3
RATE_WINDOW = 3600

def load_pro_keys():
    if os.path.exists(PRO_KEYS_FILE):
        try:
            with open(PRO_KEYS_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULT_PRO_KEYS.copy()
    save_pro_keys(DEFAULT_PRO_KEYS)
    return DEFAULT_PRO_KEYS.copy()

def save_pro_keys(keys):
    with open(PRO_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

def check_pro_key(key):
    keys = load_pro_keys()
    return key in keys and not keys[key].get("used")

def use_pro_key(key):
    keys = load_pro_keys()
    if key in keys:
        keys[key]["used"] = True
        keys[key]["used_at"] = datetime.now().isoformat()
        save_pro_keys(keys)

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
        if check_pro_key(request.pro_key):
            api_key = os.environ.get("GROQ_API_KEY", "")
            is_pro = True
        else:
            raise HTTPException(status_code=400, detail="Invalid or already used Pro key")

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
            if is_pro:
                use_pro_key(request.pro_key)
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

    if is_pro:
        use_pro_key(request.pro_key)

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
async def verify_pro(request: dict):
    key = request.get("key", "")
    if not key:
        raise HTTPException(status_code=400, detail="Key required")
    if check_pro_key(key):
        return {"valid": True, "message": "Pro key is valid"}
    return {"valid": False, "message": "Invalid or already used key"}

@app.post("/api/create-pro-key")
async def create_pro_key():
    new_key = f"PRO-{uuid.uuid4().hex[:12].upper()}"
    keys = load_pro_keys()
    keys[new_key] = {"created": datetime.now().isoformat(), "used": False}
    save_pro_keys(keys)
    return {"key": new_key}

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

@app.get("/api/keys")
async def get_keys():
    keys = load_pro_keys()
    result = []
    for k, v in keys.items():
        result.append({"key": k, "used": v.get("used", False)})
    return result

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
