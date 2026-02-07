import os
import re
import requests
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Response, Depends, Cookie
from .sqdb import init_db, get_db, ChatSession, UserSession
from sqlalchemy.orm import Session
import datetime
import uuid
import json
from langgraph.store.memory import InMemoryStore
from .prompts import (
    cv_prompt_sezione1,
    cv_prompt_sezione2,
    cv_prompt_sezione3,
    cv_prompt_sezione4,
    cv_prompt_sezione5,
    cv_prompt_sezione6,
    cv_prompt_sezione7,
    judge_prompt_sezione1,
    judge_prompt_sezione2,
    judge_prompt_sezione3,
    judge_prompt_sezione4,
    judge_prompt_sezione5,
    judge_prompt_sezione6,
    judge_prompt_sezione7,
    judge_final_prompt,
)
from pathlib import Path


REGOLO_API_URL = os.getenv("REGOLO_API_URL", "https://api.regolo.ai/v1/completions")
REGOLO_API_KEY = os.getenv("REGOLO_API_KEY")
if not REGOLO_API_KEY:
    raise ValueError("REGOLO_API_KEY environment variable is required")
CV_CREATOR_MODEL = os.getenv("CV_CREATOR_MODEL", "gpt-oss-120b")


app = FastAPI()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {REGOLO_API_KEY}",
}


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    final_cv: str
    score: float
    attempts: int
    feedback: str


data_dir = Path(__file__).parent.parent / "data"

with open(data_dir / "header.txt", "r", encoding="utf-8") as file:
    example_contract_text1 = file.read()
with open(data_dir / "subject.txt", "r", encoding="utf-8") as file:
    example_contract_text2 = file.read()
with open(data_dir / "Contract.txt", "r", encoding="utf-8") as file:
    example_contract_text3 = file.read()
with open(data_dir / "laws_n_regs.txt", "r", encoding="utf-8") as file:
    example_contract_text4 = file.read()
with open(data_dir / "signature.txt", "r", encoding="utf-8") as file:
    example_contract_text5 = file.read()
with open(data_dir / "privacy_notice.txt", "r", encoding="utf-8") as file:
    example_contract_text6 = file.read()
with open(data_dir / "withdrawal.txt", "r", encoding="utf-8") as file:
    example_contract_text7 = file.read()


cvs_dir = Path(__file__).parent.parent / "cvs"

sample_texts = {}
for i in range(1, 8):
    sample_path = cvs_dir / f"{i}.txt"
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            sample_texts[i] = f.read()
    except FileNotFoundError:
        sample_texts[i] = ""


output_dir = Path(__file__).parent.parent / "output"


names_tokens_path = data_dir / "names_tokens.json"


def call_regolo_completion(model: str, prompt: str, temperature=0.7) -> str:
    data = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
    }
    response = requests.post(REGOLO_API_URL, headers=headers, json=data)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Regolo API error: {response.text}")
    json_response = response.json()
    if "choices" in json_response and len(json_response["choices"]) > 0 and "text" in json_response["choices"][0]:
        return json_response["choices"][0]["text"].strip()
    else:
        raise HTTPException(status_code=500, detail="Invalid response from Regolo API")


# Memory store per session token
user_memory_stores = {}


@app.post("/autocv", response_model=QueryResponse)
async def autocv_request(
    request: QueryRequest,
    db: Session = Depends(get_db),
    response: Response = None,
    session_token: str = Cookie(default=None),
):
    init_db()

    print("=== INIZIO GESTIONE RICHIESTA AUTOCV ===")

    # Load existing tokens from file or create empty dict
    names_tokens = {}
    try:
        with open(names_tokens_path, "r") as f:
            names_tokens = json.load(f)
    except FileNotFoundError:
        names_tokens = {}

    # Manage session token
    if session_token and session_token in names_tokens:
        token = session_token
        print(f"Token di sessione esistente rilevato: {token}, lo riutilizzo")
    else:
        token = str(uuid.uuid4())
        names_tokens[token] = True
        with open(names_tokens_path, "w") as f:
            json.dump(names_tokens, f)
        if response:
            response.set_cookie(key="session_token", value=token, httponly=True)
        print(f"Nuovo token di sessione creato ed impostato nel cookie: {token}")

    session_token = token

    # Create or update UserSession
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

    # Load conversation history
    last_message_obj = (
        db.query(ChatSession.session_id)
        .order_by(ChatSession.id.desc())
        .limit(1)
        .one_or_none()
    )

    if last_message_obj is None or last_message_obj[0] != session_token:
        chat_msgs = (
            db.query(ChatSession.message)
            .filter(ChatSession.session_id == session_token)
            .filter(ChatSession.type != "System")
            .order_by(ChatSession.id.desc())
            .limit(30)
            .all()
        )
        conversation_history = "\n".join(m[0] for m in reversed(chat_msgs))
        user_memory_stores[session_token] = InMemoryStore()
        memory_store = user_memory_stores[session_token]
        print("Storico conversazioni caricato da DB")
    else:
        memory_store = user_memory_stores.get(session_token)
        if memory_store is None:
            memory_store = InMemoryStore()
            user_memory_stores[session_token] = memory_store
        messages = memory_store.search(user_namespace, limit=30)
        conversation_history = "\n".join(msg.value.get("text", "") for msg in messages)
        print("Storico conversazioni caricato da memoria in sessione")

    print(f"Storico conversazioni:\n{conversation_history}\n")

    user_info = request.question

    max_attempts = 3
    attempts = 0
    judge_feedback = ""
    score = 0.0
    current_cv = ""

    while attempts < max_attempts:
        attempts += 1
        print(f"\n--- Avvio tentativo numero {attempts} ---")

        # Genera prompt di creazione sezione, passandogli feedback di giudice se presente
        print("Generazione prompt per ciascuna sezione del CV...")

        full_cv_prompt1 = cv_prompt_sezione1(
            user_info,
            example_contract_text1,
            conversation_history,
            judge_feedback if judge_feedback else None,
        )
        print("Prompt sezione 1 generato")
        full_cv_prompt2 = cv_prompt_sezione2(
            user_info,
            example_contract_text2,
            conversation_history,
            judge_feedback if judge_feedback else None,
        )
        print("Prompt sezione 2 generato")
        full_cv_prompt3 = cv_prompt_sezione3(
            user_info,
            example_contract_text3,
            conversation_history,
            judge_feedback if judge_feedback else None,
        )
        print("Prompt sezione 3 generato")
        full_cv_prompt4 = cv_prompt_sezione4(
            user_info,
            example_contract_text4,
            conversation_history,
            judge_feedback if judge_feedback else None,
        )
        print("Prompt sezione 4 generato")
        full_cv_prompt5 = cv_prompt_sezione5(
            user_info,
            example_contract_text5,
            conversation_history,
            judge_feedback if judge_feedback else None,
        )
        print("Prompt sezione 5 generato")
        full_cv_prompt6 = cv_prompt_sezione6(
            user_info,
            example_contract_text6,
            conversation_history,
            judge_feedback if judge_feedback else None,
        )
        print("Prompt sezione 6 generato")
        full_cv_prompt7 = cv_prompt_sezione7(
            user_info,
            example_contract_text7,
            conversation_history,
            judge_feedback if judge_feedback else None,
        )
        print("Prompt sezione 7 generato")

        print("\nChiamate API Regolo per generare le sezioni del CV...")

        current_cv_section1 = call_regolo_completion(CV_CREATOR_MODEL, full_cv_prompt1)
        print("Sezione 1 ricevuta")
        current_cv_section2 = call_regolo_completion(CV_CREATOR_MODEL, full_cv_prompt2)
        print("Sezione 2 ricevuta")
        current_cv_section3 = call_regolo_completion(CV_CREATOR_MODEL, full_cv_prompt3)
        print("Sezione 3 ricevuta")
        current_cv_section4 = call_regolo_completion(CV_CREATOR_MODEL, full_cv_prompt4)
        print("Sezione 4 ricevuta")
        current_cv_section5 = call_regolo_completion(CV_CREATOR_MODEL, full_cv_prompt5)
        print("Sezione 5 ricevuta")
        current_cv_section6 = call_regolo_completion(CV_CREATOR_MODEL, full_cv_prompt6)
        print("Sezione 6 ricevuta")
        current_cv_section7 = call_regolo_completion(CV_CREATOR_MODEL, full_cv_prompt7)
        print("Sezione 7 ricevuta")

        print(f"Risposta ricevuta da Regolo API al tentativo {attempts}")

        # Unisci le sezioni per i prompt di giudizio
        combined_cv_text = "\n\n".join(
            [
                current_cv_section1,
                current_cv_section2,
                current_cv_section3,
                current_cv_section4,
                current_cv_section5,
                current_cv_section6,
                current_cv_section7,
            ]
        )

        print("\nChiamate API Regolo per valutare ogni sezione del CV...")

        judge_text1 = call_regolo_completion(
            CV_CREATOR_MODEL, judge_prompt_sezione1(current_cv_section1, sample_texts[1])
        )
        print("Valutazione sezione 1 ricevuta")
        judge_text2 = call_regolo_completion(
            CV_CREATOR_MODEL, judge_prompt_sezione2(current_cv_section2, sample_texts[2])
        )
        print("Valutazione sezione 2 ricevuta")
        judge_text3 = call_regolo_completion(
            CV_CREATOR_MODEL, judge_prompt_sezione3(current_cv_section3, sample_texts[3])
        )
        print("Valutazione sezione 3 ricevuta")
        judge_text4 = call_regolo_completion(
            CV_CREATOR_MODEL, judge_prompt_sezione4(current_cv_section4, sample_texts[4])
        )
        print("Valutazione sezione 4 ricevuta")
        judge_text5 = call_regolo_completion(
            CV_CREATOR_MODEL, judge_prompt_sezione5(current_cv_section5, sample_texts[5])
        )
        print("Valutazione sezione 5 ricevuta")
        judge_text6 = call_regolo_completion(
            CV_CREATOR_MODEL, judge_prompt_sezione6(current_cv_section6, sample_texts[6])
        )
        print("Valutazione sezione 6 ricevuta")
        judge_text7 = call_regolo_completion(
            CV_CREATOR_MODEL, judge_prompt_sezione7(current_cv_section7, sample_texts[7])
        )
        print("Valutazione sezione 7 ricevuta")

        # Unisci tutti i giudizi delle sezioni in un unico testo, separati da due newline
        judge_text = "\n\n".join(
            [
                judge_text1,
                judge_text2,
                judge_text3,
                judge_text4,
                judge_text5,
                judge_text6,
                judge_text7,
            ]
        )

        current_cv = combined_cv_text
        judge_final = call_regolo_completion(
            CV_CREATOR_MODEL, judge_final_prompt(judge_text)
        )

        print(f"\nValutazione del documento al tentativo {attempts}")

        # Estrai punteggio da ciascun judge_textX
        judge_texts = [judge_text1, judge_text2, judge_text3, judge_text4, judge_text5, judge_text6, judge_text7]
        scores = []
        # Pesi normalizzati che sommano a 1
        weights = [0.03846, 0.03846, 0.38462, 0.26923, 0.03846, 0.11538, 0.11538]

        for idx, jt in enumerate(judge_texts, start=1):
            match = re.search(r"Punteggio\s*[:\-]?\s*([0-9]*\.?[0-9]+)", jt, re.I)
            if match:
                score_val = float(match.group(1))
                scores.append(score_val)
                print(f"Punteggio estratto dalla sezione {idx}: {score_val}")
            else:
                print(f"Nessun punteggio trovato nella valutazione della sezione {idx}")
                scores.append(0.0)  # o altra scelta se preferisci

        # Calcolo media ponderata
        weighted_score = sum(s * w for s, w in zip(scores, weights))

        print(f"Punteggio medio ponderato calcolato: {weighted_score}")

        if all(s >= 5 for s in scores) and weighted_score >= 9.5:
            print(f"Tutti i punteggi sono >= 5 e la media ponderata ({weighted_score}) è sufficiente. Esco dal ciclo.")
            break
        else:
            if any(s < 5 for s in scores):
                print(f"C'è almeno un punteggio sotto 5. Riprovo con feedback.")
            else:
                print(f"La media ponderata ({weighted_score}) non è sufficiente. Riprovo con feedback.")
            judge_feedback = judge_text


    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "Assunzione.txt"
    print("\nGenerazione ed salvataggio documento di assunzione")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(current_cv)
    print(f"Documento salvato su {output_file}")

    memory_store.put(user_namespace, f"user{attempts}", {"text": f"User: {request.question}"})
    memory_store.put(user_namespace, f"assistant{attempts}", {"text": f"System: {current_cv}"})

    # Save chat sessions to DB for history
    user_msg = ChatSession(
        session_id=session_token,
        type="User",
        message=str(request.question),
        created_at=datetime.datetime.now(),
    )
    system_msg = ChatSession(
        session_id=session_token,
        type="System",
        message=str(full_cv_prompt1),  # Save the first prompt for traceability
        created_at=datetime.datetime.now(),
    )
    judge_msg = ChatSession(
        session_id=session_token,
        type="Judge",
        message=str(judge_final),
        created_at=datetime.datetime.now(),
    )

    db.add(user_msg)
    db.add(system_msg)
    db.add(judge_msg)
    db.commit()

    print("Tutti i dati salvati nel database, risposta in uscita.\n=== FINE GESTIONE AUTOCV ===")
    return QueryResponse(final_cv=current_cv, score=score, attempts=attempts, feedback=judge_final)
