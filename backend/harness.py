import sqlite3
import uuid
import json
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

SECRET = "drift-harness-2026"
DB = "/root/drift-harness/harness.db"

# Band stripped: run the agents directly in process via the shared direct module,
# no bridge, no Band session. The agent prompts live in the hackathon repo.
import sys as _sys, os as _os
_os.environ.setdefault("AGENTS_ROOT", "/root/hackathon-drift-agent")
_sys.path.insert(0, "/root/hackathon-drift-agent/coordinator")
from agents_direct import direct_call as _direct_call

# Roll every agent status into one turn verdict and bucket the findings, the same
# way the old Band harness logger did, so stored history is unchanged.
_CONFIRMED_WORDS = {"violation", "drifted", "drift", "gap-found", "gap_found",
                    "misaligned", "mismatch", "fail", "failed", "flagged", "flag"}
_UNCERTAIN_WORDS = {"uncertain", "unsure", "partial", "maybe", "ambiguous"}


def _classify(status) -> str:
    s = (status or "").strip().lower() if isinstance(status, str) else ""
    if s in _CONFIRMED_WORDS:
        return "confirmed"
    if s in _UNCERTAIN_WORDS:
        return "uncertain"
    return "clean"

class StripApiPrefix:
    # Accept an optional /api prefix on every route, matching what Caddy
    # strips on the public domain, so /api/x and /x behave identically.
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope.get('type') == 'http':
            path = scope.get('path', '')
            if path == '/api' or path.startswith('/api/'):
                scope = dict(scope)
                scope['path'] = path[4:] or '/'
                rp = scope.get('raw_path')
                if rp:
                    scope['raw_path'] = rp.replace(b'/api', b'', 1)
        await self.app(scope, receive, send)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(StripApiPrefix)

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            estimated_cost REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

class HarnessEntry(BaseModel):
    data: dict[str, Any]

class UsageEntry(BaseModel):
    agent_name: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float

@app.post("/write")
def write_entry(entry: HarnessEntry, x_secret: str = Header(None)):
    if x_secret != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO entries (id, timestamp, data) VALUES (?, ?, ?)",
        (entry_id, timestamp, json.dumps(entry.data))
    )
    conn.commit()
    conn.close()
    return {"entry_id": entry_id, "timestamp": timestamp}

@app.post("/write_usage")
def write_usage(entry: UsageEntry, x_secret: str = Header(None)):
    if x_secret != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO usage (id, timestamp, agent_name, input_tokens, output_tokens, estimated_cost) VALUES (?, ?, ?, ?, ?, ?)",
        (entry_id, timestamp, entry.agent_name, entry.input_tokens, entry.output_tokens, entry.estimated_cost)
    )
    conn.commit()
    conn.close()
    return {"entry_id": entry_id}

@app.get("/read")
def read_entries(limit: int = 50, x_secret: str = Header(None)):
    if x_secret != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = get_db()
    rows = conn.execute(
        "SELECT id, timestamp, data FROM entries ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "timestamp": r["timestamp"], "data": json.loads(r["data"])} for r in rows]

@app.get("/usage_stats")
def usage_stats(x_secret: str = Header(None)):
    if x_secret != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = get_db()
    rows = conn.execute("""
        SELECT agent_name,
               SUM(input_tokens) as total_input,
               SUM(output_tokens) as total_output,
               SUM(estimated_cost) as total_cost,
               COUNT(*) as call_count
        FROM usage
        GROUP BY agent_name
        ORDER BY total_cost DESC
    """).fetchall()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    last_24h = conn.execute(
        "SELECT SUM(estimated_cost) as cost FROM usage WHERE timestamp > ?",
        (cutoff,)
    ).fetchone()
    all_time = conn.execute("SELECT SUM(estimated_cost) as cost FROM usage").fetchone()
    conn.close()
    return {
        "all_time_cost": round(all_time["cost"] or 0, 6),
        "last_24h_cost": round(last_24h["cost"] or 0, 6),
        "per_agent": [
            {
                "agent": r["agent_name"],
                "input_tokens": r["total_input"],
                "output_tokens": r["total_output"],
                "cost": round(r["total_cost"], 6),
                "calls": r["call_count"],
            }
            for r in rows
        ]
    }


@app.get("/read_calls")
def read_calls(limit: int = 100, x_secret: str = Header(None)):
    if x_secret != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = get_db()
    rows = conn.execute(
        "SELECT id, timestamp, agent_name, input_tokens, output_tokens, estimated_cost FROM usage ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "timestamp": r["timestamp"], "agent": r["agent_name"], "input_tokens": r["input_tokens"], "output_tokens": r["output_tokens"], "cost": r["estimated_cost"]} for r in rows]
@app.get("/health")
def health():
    return {"status": "ok"}


from concurrent.futures import ThreadPoolExecutor

BRIDGE_LOCAL = "http://127.0.0.1:5055/api/agent"
BRIDGE_TIMEOUT = 35
PROFILERS = ["03-human-profiler", "04-engine-profiler"]
VERDICT_AGENTS = [
    "05-alignment-classifier",
    "06-question-generator",
    "07-gap-analyzer",
    "08-constraints-checker",
    "09-anti-patterns-checker",
    "10-voice-checker",
    "11-quality-checker",
    "12-identity-agent",
    "13-verifier",
]

# --- Engine generation -----------------------------------------------------
# In production the engine is the external AI being monitored. On the public
# page there is no external engine to intercept, so we stand one up: generate
# the engine turn from the human message, then run the existing pipeline on it.
# When an engine reply is supplied (the canned scenarios), generation is skipped.
ENGINE_MODEL = "claude-sonnet-4-6"
ENGINE_ENV_FILE = "/root/hackathon-drift-agent/.env"


def _load_anthropic_key() -> str:
    import os
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        with open(ENGINE_ENV_FILE) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def generate_engine_turn(human_input: str) -> str:
    import requests as req
    key = _load_anthropic_key()
    if not key:
        return ""
    try:
        r = req.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ENGINE_MODEL,
                "max_tokens": 1024,
                "system": "You are the AI assistant the user is talking to. Answer the user's message directly and naturally, as their assistant would.",
                "messages": [{"role": "user", "content": human_input}],
            },
            timeout=60,
        )
        data = r.json()
        parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        return "".join(parts).strip()
    except Exception:
        return ""


class AnalyzeRequest(BaseModel):
    human_input: str
    engine_response: str = ""

def bridge_call(route: str, payload: dict) -> tuple:
    # Band stripped: this used to POST to the bridge; now it calls the agent
    # directly in process. Same signature and return shape, so analyze is unchanged.
    return _direct_call(route, payload)


def _write_record(base: dict, findings: list) -> None:
    # Replaces the Band harness logger. Builds the same record and writes it to
    # the entries table directly so the dashboard history keeps populating.
    classes = {_classify(f.get("status")) for f in findings if isinstance(f, dict)}
    turn_status = "confirmed" if "confirmed" in classes else ("uncertain" if "uncertain" in classes else "clean")
    confirmed = [f for f in findings if isinstance(f, dict) and _classify(f.get("status")) == "confirmed"]
    uncertain = [f for f in findings if isinstance(f, dict) and _classify(f.get("status")) == "uncertain"]
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "turn_status": turn_status,
        "payload": base,
        "confirmed_findings": confirmed,
        "uncertain_findings": uncertain,
    }
    conn = get_db()
    conn.execute(
        "INSERT INTO entries (id, timestamp, data) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), record["timestamp"], json.dumps(record)),
    )
    conn.commit()
    conn.close()

@app.post("/analyze")
def analyze(payload: AnalyzeRequest):
    import requests as req
    input_id = str(uuid.uuid4())
    engine_response = (payload.engine_response or "").strip()
    if not engine_response:
        engine_response = generate_engine_turn(payload.human_input)
    base = {
        "input_id": input_id,
        "human_input": payload.human_input,
        "engine_response": engine_response,
    }

    profiles: dict = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        for route, res in pool.map(lambda r: bridge_call(r, base), PROFILERS):
            profiles[route] = res

    context = dict(base)
    context["human_profile"] = profiles.get("03-human-profiler")
    context["engine_profile"] = profiles.get("04-engine-profiler")

    findings = []
    with ThreadPoolExecutor(max_workers=len(VERDICT_AGENTS)) as pool:
        for route, res in pool.map(lambda r: bridge_call(r, context), VERDICT_AGENTS):
            findings.append(res)

    try:
        _write_record(base, findings)
    except Exception:
        pass

    return {"input_id": input_id, "engine_response": engine_response, "findings": findings}
