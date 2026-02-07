# ZeroHR - AI-Powered HR Document Assistant for Italy

**ZeroHR** è un assistente intelligente altamente specializzato progettato per automatizzare e semplificare la creazione di documenti di assunzione e la consulenza del lavoro in Italia.

## 🚀 Panoramica

ZeroHR è un agente AI professionale che gestisce l'intero flusso di workHR italiano,从 la raccolta delle informazioni del candidato alla generazione di contratti di assunzione conformi alla normativa vigente.

### Caratteristiche Principali

- ✅ **Pipeline Intelligente**: Generazione documenti in 7 sezioni (Header, Oggetto, Dettagli Contratto, Riferimenti Normativi, Firma, Privacy, Consenso)
- ✅ **Judge System**: Sistema di validazione automatica con punteggio e feedback per ogni sezione
- ✅ **Compliance Normativa**: Conformità ai principi del GDPR e normativa italiana sul lavoro
- ✅ **Multilingua**: Supporto per documenti in italiano con gestione semantica
- ✅ **Modulare**: Architettura event-driven scalabile e riutilizzabile per ogni tipo di documento HR

## 📁 Struttura Progetto

```
ZeroHR/
├── backend/                   # Backend Python (FastAPI + Celery)
│   ├── main.py               # FastAPI application con Celery worker
│   ├── prompts.py            # Prompt engineering per 7 sezioni + Judge system
│   ├── sqdb.py               # Database per sessioni e messaggi chat
│   ├── sqdb_pipe.py          # Database per workflow di generazione documenti
│   └── autocv.py             # API alternativa per generazione CV
├── frontend/                  # Frontend React + Vite
│   ├── src/
│   │   ├── App.tsx           # Componente principale
│   │   └── main.tsx          # Entry point
│   └── vite.config.ts
├── data/                      # File di dati e template
│   ├── header.txt
│   ├── subject.txt
│   ├── Contract.txt
│   ├── laws_n_regs.txt
│   ├── signature.txt
│   ├── privacy_notice.txt
│   ├── withdrawal.txt
│   └── names_tokens.json
├── cvs/                       # Campioni CV sezionali (1-7)
│   ├── 1.txt
│   ├── 2.txt
│   ├── ...
│   └── 7.txt
├── output/                    # Documenti generati (output directory)
├── tests/                     # Test unitari e di integrazione
├── .env.example               # Template per variabili d'ambiente
├── requirements.txt           # Dipendenze Python
├── package.json               # Configurazione frontend
├── run_backend.py             # Script per avvio backend
├── run_worker.py              # Script per avvio Celery worker
└── README.md                  # Documentation (this file)
```

## 🛠️ Architettura

### Pipeline di Generazione Documenti

ZeroHR utilizza una pipeline avanzata a 7 sezioni:

1. **Sezione 1 - Header e Indirizzo**: Informazioni mittente/destinatario
2. **Sezione 2 - Oggetto**: Typo documento (es. assunzione a tempo indeterminato)
3. **Sezione 3 - Dettagli Contratto**: Termini e condizioni lavorative
4. **Sezione 4 - Riferimenti Normativi**: Citazioni legislative pertinenti
5. **Sezione 5 - Firma**: Spazi per firme datore/lavoratore
6. **Sezione 6 - Informativa Privacy**: GDPR compliance
7. **Sezione 7 - Consenso**: Revoca trattamento dati

### Judge System

Ogni sezione passa attraverso un "giudice" AI che:
- Valuta conformità al template GOLD STANDARD
- Assegna punteggio da 1 a 10
- Fornisce feedback per miglioramenti
- Richieda retry se punteggio < 9.0

### Technology Stack

- **Backend**: FastAPI + Celery + Redis
- **Database**: SQLite (production-ready with PostgreSQL support via env vars)
- **AI**: Regolo AI (GPT-4o mini / GPT-oss-120b)
- **State Management**: LangGraph InMemoryStore

## 📦 Installazione

### Prerequisiti

- Python 3.9+
- Redis server (localhost:6379)
- API key da [Regolo AI](https://regolo.ai)

### Setup

```bash
# 1. Clona il repository
git clone https://github.com/tuo-username/zerohr.git
cd zerohr

# 2. Crea ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Configura environment
cp .env.example .env
# Modifica .env con le tue API keys
```

### Environment Variables

Crea un file `.env` con:

```env
# Required - Regolo AI
REGOLO_API_KEY=your_api_key_here
REGOLO_API_URL=https://api.regolo.ai/v1/completions
CV_CREATOR_MODEL=gpt-oss-120b

# Optional - Database (paths will be set automatically in backend/)
DATABASE_URL=sqlite:///./data/assunzioni.db
KEY_FLOW_DATABASE_URL=sqlite:///./data/key_flow.db

# Optional - Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Optional - Dev
ZEROHR_DEV_PURGE=0
```

## ▶️ Avvio Applicazione

### 1. Avvia Redis

```bash
redis-server
```

### 2. Avvia FastAPI

**Opzione A - Script semplificato:**
```bash
python run_backend.py
```

**Opzione B - Direct (da backend/):**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Avvia Celery Worker

**Opzione A - Script semplificato:**
```bash
python run_worker.py
```

**Opzione B - Direct (da backend/):**
```bash
cd backend
celery -A main.celery_app worker --loglevel=info --concurrency=7 --pool=threads
```

## 🧪 Uso API

### Genera Documento

```bash
curl -X POST http://localhost:8000/main \
  -H "Content-Type: application/json" \
  -d '{"question": "Nuova assunzione: Mario Rossi, developer, stipendio 40000€"}'
```

**Response:**
```json
{
  "task_id": "abc123-def456"
}
```

### Check Status

```bash
curl http://localhost:8000/task_status/abc123-def456
```

## 🏗️ Sviluppo

### Aggiungere Nuovi Template

1. Aggiungi file `.txt` con esempio GOLD STANDARD
2. Aggiungi prompt in `prompts.py`
3. Aggiorna mapping in `main.py` Celery tasks

### Struttura Prompt

Ogni sezione richiede:
- `cv_prompt_sezioneN()`: Generazione contenuto
- `judge_prompt_sezioneN()`: Validazione contenuto

## 🙏 Credits

**ZeroHR** è il mio primo progetto reale full-stack sviluppato durante l'estate 2025, 
dopo aver concluso il corso di Digital Maker 2025. Questo progetto è stato presentato 
come candidate per la competizione Digithon 2025.

Progetto ZeroHR - AI Powered HR Assistant for Italy  
🔗 [v0-zerohr-ai.vercel.app](https://v0-zerohr-ai.vercel.app/)  
🔗 [linktr.ee/zerohr.ai](https://linktr.ee/zerohr.ai)

## 📞 Supporto

Per domande o issues, apri un issue su GitHub.

---

**ZeroHR**: L'evoluzione della consulenza del lavoro italiana con l'AI.