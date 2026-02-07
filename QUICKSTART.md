# Quick Start - ZeroHR Setup

## Installazione Rapida (5 minuti)

### 1. Installa Prerequisiti

**Windows:**
```powershell
# Python 3.9+
# Install Redis: https://github.com/microsoftarchive/redis/releases
# Or use Docker: docker run -p 6379:6379 --name redis -d redis
```

**macOS/Linux:**
```bash
brew install redis  # macOS
sudo apt install redis-server  # Ubuntu
```

### 2. Configura il Progetto

```bash
# Clona il repo
git clone https://github.com/tuo-username/zerohr.git
cd zerohr

# Crea ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Installa dipendenze
pip install -r requirements.txt

# Configura environment
cp .env.example .env
# Modifica .env con la tua Regolo API key
```

**File .env esempio:**
```env
REGOLO_API_KEY=sk-tua_api_key_regolo
REGOLO_API_URL=https://api.regolo.ai/v1/completions
CV_CREATOR_MODEL=gpt-oss-120b
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Avvia i Servizi

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - FastAPI:**
```bash
python main.py
# oppure
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 - Celery Worker:**
```bash
celery -A main.celery_app worker --loglevel=info --concurrency=7 --pool=threads
```

### 4. Usa l'API

```bash
curl -X POST http://localhost:8000/main \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=test123" \
  -d '{"question": "Assumere Mario Rossi come sviluppatore con stipendio 45000€ annui"}'
```

**Risposta:**
```json
{
  "task_id": "abc-123-def"
}
```

```bash
# Check status
curl http://localhost:8000/task_status/abc-123-def
```

## 🔧 Troubleshooting

**Redis connection refused:**
```bash
# Verifica Redis in esecuzione
redis-cli ping
# Dovrebbe rispondere: PONG
```

**REGOLO_API_KEY missing:**
```
Verifica che .env contenga REGOLO_API_KEY=sk-...
```

**Celery worker not starting:**
```bash
# Verifica Redis broker
redis-cli ping
# Test Celery
celery -A main.celery_app inspect ping
```

## 📝 Note

- Il sistema generaAutomaticamente 7 sezioni per ogni documento
- Judge system valuta ogni sezione e richieda retry se punteggio < 9.0
- I dati sono salvati in SQLite (assunzioni.db, key_flow.db)
- Per produzione, usa PostgreSQL cambiando DATABASE_URL in .env

## 📚 Documentazione Completa

Vedi [README.md](./README.md) per architettura, sviluppo e dettagli tecnici.