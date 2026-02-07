# app.py
from fastapi import FastAPI, Depends, HTTPException, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from celery import Celery, chord, states
from celery.exceptions import Ignore
from celery.result import AsyncResult
from pathlib import Path
import httpx
import uuid
import datetime
import json
import redis
import re
import os

# --- Import applicativi/DB ---
from sqdb import init_db, get_db, ChatSession, UserSession
from sqdb_pipe import Workflow, AllData, get_db2, init_db2
from langgraph.store.memory import InMemoryStore
from prompts import (
    cv_prompt_sezione1, cv_prompt_sezione2, cv_prompt_sezione3,
    cv_prompt_sezione4, cv_prompt_sezione5, cv_prompt_sezione6, cv_prompt_sezione7,
    judge_prompt_sezione1, judge_prompt_sezione2, judge_prompt_sezione3,
    judge_prompt_sezione4, judge_prompt_sezione5, judge_prompt_sezione6,
    judge_prompt_sezione7, judge_final_prompt,
)

# --- Costanti Regolo (override via env) ---
REGOLO_API_URL = os.getenv("REGOLO_API_URL", "https://api.regolo.ai/v1/completions")
REGOLO_API_KEY = os.getenv("REGOLO_API_KEY")
if not REGOLO_API_KEY:
    raise ValueError("REGOLO_API_KEY environment variable is required")
CV_CREATOR_MODEL = os.getenv("CV_CREATOR_MODEL", "gpt-oss-120b")

# --- Redis e Celery ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)
celery_app = Celery(
    "tasks",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)
celery_app.conf.update(
    task_track_started=True,
    result_expires=900,
    worker_prefetch_multiplier=1,
)

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Headers Regolo ---
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {REGOLO_API_KEY}",
}

# --- Inizializzazione DB2 e bootstrap delle 7 sezioni ---
init_db2()
_db2_init = next(get_db2())
_db2_init.query(Workflow).delete()
_db2_init.commit()
for section_num in range(1, 8):
    _db2_init.add(Workflow(section=section_num, status="da_generare"))
    _db2_init.commit()

# --- Lettura testi di esempio (una sola volta) ---
example_contract_texts: List[str] = []
example_filenames = [
    "header.txt", "subject.txt", "Contract.txt", "laws_n_regs.txt",
    "signature.txt", "privacy_notice.txt", "withdrawal.txt"
]
for filename in example_filenames:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            example_contract_texts.append(file.read())
    except FileNotFoundError:
        example_contract_texts.append("")

# --- Carica sample CV sezionali (1..7) ---
folder_path = "cvs"
sample_texts: Dict[int, str] = {}
for i in range(1, 8):
    sample_path = f"{folder_path}/{i}.txt"
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            sample_texts[i] = f.read()
    except FileNotFoundError:
        sample_texts[i] = ""

# --- Store memorie utente in RAM (per sessione) ---
user_memory_stores: Dict[str, InMemoryStore] = {}

# --- Pydantic models ---
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    final_cv: str
    score: float
    attempts: int
    feedback: str

# ========== Celery/Admin utils ==========

# Redis del backend Celery (stesso DB della tua backend= 'redis://localhost:6379/0')
_redis_backend = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def _scan_del(r: redis.Redis, patterns: List[str]) -> Dict[str, int]:
    """Cancella chiavi Redis per pattern e ritorna conteggi."""
    out: Dict[str, int] = {}
    for pat in patterns:
        cnt = 0
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor=cursor, match=pat, count=1000)
            if keys:
                r.delete(*keys)
                cnt += len(keys)
            if cursor == 0:
                break
        out[pat] = cnt
    return out

def revoke_all_tasks(mode: str = "soft") -> Dict[str, Any]:
    """
    Revoca tutto ciò che è active/reserved/scheduled.
    mode='soft' -> revoke pending; mode='hard' -> revoke(terminate=True) [richiede prefork].
    """
    insp = celery_app.control.inspect()
    active = insp.active() or {}
    reserved = insp.reserved() or {}
    scheduled = insp.scheduled() or {}

    ids: List[str] = []

    for _, tasks in active.items():
        for t in tasks:
            if "id" in t:
                ids.append(t["id"])

    for _, tasks in reserved.items():
        for t in tasks:
            if "id" in t:
                ids.append(t["id"])

    for _, tasks in scheduled.items():
        for t in tasks:
            if isinstance(t, dict):
                if "request" in t and isinstance(t["request"], dict) and "id" in t["request"]:
                    ids.append(t["request"]["id"])
                elif "id" in t:
                    ids.append(t["id"])

    ids = list(dict.fromkeys(ids))  # dedup

    hard = (mode.lower() == "hard")
    for _id in ids:
        try:
            celery_app.control.revoke(_id, terminate=hard, signal="SIGTERM")
        except Exception as e:
            print("[REVOKE] error", _id, e)

    return {"revoked": len(ids), "hard": hard}

def purge_all_queues() -> int:
    """Svuota la/e coda/e del broker Redis (celery queue)."""
    try:
        return celery_app.control.purge()
    except Exception as e:
        print("[PURGE] failed:", e)
        return -1

def clear_celery_backend() -> Dict[str, int]:
    """
    Pulisce risultati/metadati Celery nel backend Redis:
    - risultati task
    - set di group/chord
    - chiavi chord-unlock
    """
    patterns = [
        "celery-task-meta-*",
        "celery-task-set-*",
        "chord-unlock*",
        "chord-counter-*",
        "celery-task-sig-*",
    ]
    return _scan_del(_redis_backend, patterns)

def reseed_workflow(db2: Session, status_all: str = "da_generare", status_map: Dict[int, str] | None = None):
    """Reset + semina con stato desiderato (uguale per tutti o per-sezione via mappa)."""
    db2.query(Workflow).delete()
    db2.commit()
    for section_num in range(1, 8):
        st = status_all
        if status_map and section_num in status_map:
            st = status_map[section_num]
        db2.add(Workflow(section=section_num, status=st))
    db2.commit()

# === Request models per gli endpoint admin ===
class KillRequest(BaseModel):
    mode: str = "soft"  # 'soft' | 'hard'

class ResetRequest(BaseModel):
    reseed: bool = True
    status_all: str = "da_generare"
    status_map: Dict[int, str] | None = None
    purge: bool = True
    flush_backend: bool = True
    kill_mode: str = "soft"  # 'soft' | 'hard'

class SeedRequest(BaseModel):
    status_all: str = "da_generare"
    status_map: Dict[int, str] | None = None

# --- Lock Redis corretta ---
class RedisLock:
    def __init__(self, name, timeout=60):
        self._lock = redis_client.lock(name, timeout=timeout)
    def __enter__(self):
        if not self._lock.acquire(blocking=False):
            raise HTTPException(status_code=429, detail="Too many concurrent requests, try again later")
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self._lock.release()
        except Exception:
            pass

# --- Utility sincrona per Regolo ---
def regolo_call_sync(client: httpx.Client, model: str, prompt: str, temperature: float = 0.7) -> str:
    data = {"model": model, "prompt": prompt, "temperature": temperature}
    resp = client.post(REGOLO_API_URL, headers=headers, json=data)
    if resp.status_code != 200:
        raise Exception(f"Regolo API error: {resp.text}")
    js = resp.json()
    try:
        text = js["choices"][0]["text"]
    except Exception:
        raise Exception(f"Invalid response from Regolo API: {js}")
    return text.strip()

# ========== CELERY TASKS ==========

@celery_app.task(bind=True)
def complete_creation(self, task_id: int, user_info: str, conversation_history: str):
    db2 = next(get_db2())
    task = db2.query(Workflow).filter(Workflow.id == task_id).first()
    if not task or task.status not in ("da_generare", "da_giudicare"):
        raise Exception("Task not found or not in valid state")

    section = task.section

    prompt_map = {
        1: cv_prompt_sezione1, 2: cv_prompt_sezione2, 3: cv_prompt_sezione3,
        4: cv_prompt_sezione4, 5: cv_prompt_sezione5, 6: cv_prompt_sezione6, 7: cv_prompt_sezione7,
    }
    judge_prompt_map = {
        1: judge_prompt_sezione1, 2: judge_prompt_sezione2, 3: judge_prompt_sezione3,
        4: judge_prompt_sezione4, 5: judge_prompt_sezione5, 6: judge_prompt_sezione6, 7: judge_prompt_sezione7,
    }

    example_text_map = {i + 1: t for i, t in enumerate(example_contract_texts)}
    sample_text = sample_texts.get(section, "")

    with httpx.Client(timeout=600.0) as client:
        task.status = "in_creazione"
        db2.commit()
        self.update_state(state=states.STARTED, meta={"section": section})

        prompt_text = prompt_map[section](user_info, example_text_map[section], conversation_history, task.notes or None)
        result_text = regolo_call_sync(client, CV_CREATOR_MODEL, prompt_text)

        task.text = result_text
        task.status = "da_giudicare"
        db2.commit()

        task.status = "in_giudizio"
        db2.commit()

        judge_prompt = judge_prompt_map[section](task.text, sample_text)
        judge_text = regolo_call_sync(client, CV_CREATOR_MODEL, judge_prompt)

        match = re.search(r"Punteggio\s*[:\-]?\s*([0-9]*\.?[0-9]+)", judge_text, re.I)
        score_val = float(match.group(1)) if match else 0.0

        task.notes = judge_text
        task.score = score_val

        if score_val < 7:
            try:
                task.status = "da_generare"
                db2.commit()
                self.retry(countdown=0, exc=Exception("Retry for low score"), max_retries=2)
            except self.MaxRetriesExceededError:
                task.status = "failed"
                db2.commit()
                return {"section": section, "status": "failed"}
        else:
            task.status = "giudicato"
            full_task = AllData(
                section=task.section,
                status=task.status,
                text=task.text,
                score=task.score,
                notes=task.notes,
                weighted_score=task.weighted_score,
                retry_count=task.retry_count,
            )
            db2.add(full_task)
            db2.commit()

    return {"section": section, "status": "ok", "score": score_val}

@celery_app.task(bind=True)
def finalize_cv(self, results, session_token: Optional[str] = None):
    from sqdb_pipe import get_db2, Workflow
    from sqdb import get_db, ChatSession
    import datetime as _dt

    db2 = next(get_db2())
    all_tasks = db2.query(Workflow).filter(Workflow.section.in_(range(1, 8))).all()

    weights = [0.03846, 0.00500, 0.41500, 0.30000, 0.00500, 0.11877, 0.11777]
    scores: List[float] = []
    for s in range(1, 8):
        t = next((t for t in all_tasks if t.section == s), None)
        scores.append((t.score or 0.0) if t else 0.0)
    weighted_score = sum(s * w for s, w in zip(scores, weights))

    judge_final = ""
    if weighted_score > 8:
        all_judge_texts = "\n\n".join((t.notes or "") for t in all_tasks)
        with httpx.Client(timeout=600.0) as client:
            judge_final = regolo_call_sync(client, CV_CREATOR_MODEL, judge_final_prompt(all_judge_texts))

    section_texts_ordered = db2.query(Workflow).order_by(Workflow.section).all()
    current_cv = "\n\n".join((t.text or "") for t in section_texts_ordered)

    first_section_task = next((t for t in all_tasks if t.section == 1), None)
    if first_section_task:
        first_section_task.weighted_score = weighted_score
        db2.commit()

    try:
        if session_token:
            db = next(get_db())
            db.add(ChatSession(
                session_id=session_token,
                type="Assistant",
                message=current_cv,
                created_at=_dt.datetime.now(),
            ))
            if judge_final:
                db.add(ChatSession(
                    session_id=session_token,
                    type="System",
                    message=f"[Judge finale]\n{judge_final}",
                    created_at=_dt.datetime.now(),
                ))
            db.commit()
    except Exception:
        pass

    attempts = 0
    try:
        attempts = max((t.retry_count or 0) for t in all_tasks if hasattr(t, "retry_count"))
    except Exception:
        attempts = 0

    return {
        "cv": current_cv,
        "weighted_score": weighted_score,
        "attempts": attempts,
        "feedback": judge_final,
    }

# ========== RESET + RELOAD (1 + 2) ==========

def reset_workflow_state(db2: Session) -> None:
    _db2_init = next(get_db2())
    _db2_init.query(Workflow).delete()
    _db2_init.commit()
    for section_num in range(1, 8):
        _db2_init.add(Workflow(section=section_num, status="da_generare"))
        _db2_init.commit()

def cleanup_task_artifacts(task_id: str) -> None:
    try:
        AsyncResult(task_id, app=celery_app).forget()
    except Exception as e:
        print("[CLEANUP] forget error:", e)
    try:
        redis_client.delete("start_task_lock")
    except Exception as e:
        print("[CLEANUP] redis lock del error:", e)

def trigger_uvicorn_reload_dev() -> bool:
    _file_ = os.path.abspath(__file__)
    # Necessario avviare uvicorn con --reload
    try:
        p = Path(_file_)
        p.touch()
        print("[RELOAD] touched:", p)
        return True
    except Exception as e:
        print("[RELOAD] failed:", e)
        return False

# ========== ENDPOINTS BUSINESS ==========

@app.post("/main")
async def main_trigger(
    request: QueryRequest,
    response: Response = None,
    db2: Session = Depends(get_db2),
    db: Session = Depends(get_db),
    session_token: Optional[str] = Cookie(default=None),
):
    init_db2()
    init_db()

    # === RESET AUTOMATICO OGNI VOLTA ===
    revoke_all_tasks(mode="soft")       # revoca task attivi/pending
    purge_all_queues()                  # svuota le code
    clear_celery_backend()              # pulizia risultati/metadati
    reseed_workflow(db2, status_all="da_generare")  # reset workflow

    # === Gestione token/sessione ===
    try:
        with open("names_tokens.json", "r") as f:
            names_tokens = json.load(f)
    except FileNotFoundError:
        names_tokens = {}

    if session_token and session_token in names_tokens:
        token = session_token
        print(f"Token di sessione esistente rilevato: {token}, lo riutilizzo")
    else:
        token = str(uuid.uuid4())
        names_tokens[token] = True
        with open("names_tokens.json", "w") as f:
            json.dump(names_tokens, f)
        if response:
            response.set_cookie(key="session_token", value=token, httponly=True)
        print(f"Nuovo token di sessione creato ed impostato nel cookie: {token}")

    session_token = token

    user_session = db.query(UserSession).filter(UserSession.user_id == session_token).first()
    now = datetime.datetime.now()
    if user_session is None:
        user_session = UserSession(
            user_id=session_token,
            start_time=now,
            last_access_time=now,
        )
        db.add(user_session)
        print("Nuova sessione utente creata")
    else:
        user_session.last_access_time = now
        print("Sessione utente aggiornata")
    db.commit()

    user_namespace = (session_token, "memories")

    chat_msgs = (
        db.query(ChatSession.message)
        .filter(ChatSession.session_id == session_token)
        .filter(ChatSession.type != "System")
        .order_by(ChatSession.id.desc())
        .limit(3)
        .all()
    )
    conversation_history = "\n".join(m[0] for m in reversed(chat_msgs))
    user_memory_stores[session_token] = InMemoryStore()
    memory_store = user_memory_stores[session_token]
    print("Storico conversazioni caricato da DB")
    print(conversation_history)

    user_info = request.question

    with RedisLock("start_task_lock", timeout=15):
        tasks_to_create = (
            db2.query(Workflow)
            .filter(Workflow.status == "da_generare")
            .filter(Workflow.section.in_(range(1, 8)))
            .order_by(Workflow.section)
            .all()
        )
        if not tasks_to_create:
            raise HTTPException(status_code=404, detail="No tasks in 'da_generare' state available")

    header = [
        complete_creation.s(
            task_id=t.id,
            user_info=user_info,
            conversation_history=conversation_history
        )
        for t in tasks_to_create
    ]

    callback_result = chord(header)(finalize_cv.s(session_token=session_token))

    user_msg = ChatSession(
        session_id=session_token,
        type="User",
        message=request.question,
        created_at=datetime.datetime.now(),
    )
    message = cv_prompt_sezione1(user_info, example_contract_texts[0], conversation_history, None)
    system_msg = ChatSession(
        session_id=session_token,
        type="System",
        message=message,
        created_at=datetime.datetime.now(),
    )
    db.add(user_msg)
    db.add(system_msg)
    db.commit()

    memory_store.put(user_namespace, "user", {"text": f"User: {request.question}"})

    return {"task_id": callback_result.id}


@app.get("/task_status/{task_id}", response_model=Optional[QueryResponse])
def get_task_status(task_id: str, db2: Session = Depends(get_db2)):
    async_result = celery_app.AsyncResult(task_id)

    if async_result.status == "PENDING":
        return QueryResponse(final_cv="", score=0.0, attempts=0, feedback=f"Task pending id(={task_id})")
    elif async_result.status == "STARTED":
        return QueryResponse(final_cv="", score=0.0, attempts=0, feedback="Task in progress")
    elif async_result.status == "FAILURE":
        feedback = ""
        if isinstance(async_result.result, dict):
            feedback = async_result.result.get("feedback", "")
        raise HTTPException(
            status_code=500,
            detail=f"Task failed: {async_result.info}. Feedback: {feedback or 'None'}"
        )
    elif async_result.status == "SUCCESS":
        result = async_result.result or {}
        return QueryResponse(
            final_cv=result.get("cv", ""),
            score=result.get("weighted_score", 0.0),
            attempts=result.get("attempts", 0),
            feedback=result.get("feedback", "") or ""
        )
    else:
        return QueryResponse(final_cv="", score=0.0, attempts=0, feedback=f"Task state: {async_result.status}")

@app.post("/finalize/{task_id}")
def finalize_and_reset(task_id: str):
    db2 = next(get_db2())

    before = db2.query(Workflow).count()
    reset_workflow_state(db2)
    after = db2.query(Workflow).count()

    cleanup_task_artifacts(task_id)

    purged = False
    if os.getenv("ZEROHR_DEV_PURGE") == "1":
        try:
            celery_app.control.purge()
            purged = True
            print("[CELERY] queue purged (DEV)")
        except Exception as e:
            print("[CELERY] purge failed:", e)

    reloaded = trigger_uvicorn_reload_dev()

    return {
        "ok": True,
        "workflow_rows_before": before,
        "workflow_rows_after": after,
        "celery_purged_dev": purged,
        "uvicorn_reloaded": reloaded,
    }

@app.get("/debug/state")
def debug_state():
    db2 = next(get_db2())
    rows = db2.query(Workflow).order_by(Workflow.section).all()
    data = [
        {"id": r.id, "section": r.section, "status": r.status, "score": r.score}
        for r in rows
    ]
    return {"workflow": data}

# ========== ENDPOINTS ADMIN ==========

@app.post("/admin/kill")
def admin_kill(req: KillRequest):
    stats = revoke_all_tasks(mode=req.mode)
    return {"ok": True, "killed": stats}

@app.post("/admin/reset")
def admin_reset(req: ResetRequest, db2: Session = Depends(get_db2)):
    killed = revoke_all_tasks(mode=req.kill_mode)
    purged = purge_all_queues() if req.purge else 0
    cleared = clear_celery_backend() if req.flush_backend else {}

    if req.reseed:
        reseed_workflow(db2, status_all=req.status_all, status_map=req.status_map)

    # azzera anche memoria in-process (utile in dev)
    try:
        user_memory_stores.clear()
    except Exception:
        pass

    return {
        "ok": True,
        "killed": killed,
        "purged": purged,
        "cleared_backend": cleared,
        "reseeded": req.reseed,
        "status_all": req.status_all,
        "status_map": req.status_map or {},
    }

@app.post("/admin/seed")
def admin_seed(req: SeedRequest, db2: Session = Depends(get_db2)):
    reseed_workflow(db2, status_all=req.status_all, status_map=req.status_map)
    return {"ok": True, "status_all": req.status_all, "status_map": req.status_map or {}}
