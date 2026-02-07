import { useState, useEffect, useRef } from "react";
import "./App.css";
import logo from './assets/Zerohr.png';
import power from './assets/regolo.png';

interface ResultData {
  final_cv: string;
  score: number;
  attempts: number;
  feedback: string;
}

function ZeroHRDocGenerator() {
  const [question, setQuestion] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [result, setResult] = useState<ResultData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!taskId) return;
    let cancelled = false;

    const poll = async () => {
      try {
        const res = await fetch("/task_status/" + encodeURIComponent(taskId), {
          credentials: "include",
        });

        if (!res.ok) {
          setStatus("Polling error (" + res.status + ")");
          setIsLoading(false);
          return;
        }

        const data: ResultData = await res.json();
        setStatus(data.feedback || "In progress...");

        if (cancelled) return;

        if (data.final_cv) {
          setResult(data);
          setIsLoading(false);

          try {
            const r = await fetch("/finalize/" + encodeURIComponent(taskId), {
              method: "POST",
              credentials: "include",
            });
            try {
              const dbg = await r.json();
              if (dbg && dbg.uvicorn_reloaded) {
                setStatus("Completato. Reset e reload eseguiti.");
              } else {
                setStatus("Completato. Reset inviato.");
              }
            } catch (_e) {
              setStatus("Completato. Reset inviato.");
            }
          } catch (_e) {
            setStatus("Completato. Reset non confermato.");
          }

          return;
        }

        timerRef.current = setTimeout(poll, 2500);
      } catch (_e) {
        if (!cancelled) {
          setStatus("Network error during polling");
          timerRef.current = setTimeout(poll, 3500);
        }
      }
    };

    poll();

    return () => {
      cancelled = true;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [taskId]);

  const startMain = async (payload: { question: string }) => {
    const res = await fetch("/main", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      setIsLoading(false);
      setStatus("Failed to start task (" + res.status + ")");
      return;
    }

    const data = await res.json();
    if (data && data.task_id) {
      setTaskId(String(data.task_id));
      setStatus("Task avviata. Monitoraggio in corso...");
    } else {
      setIsLoading(false);
      setStatus("Nessun task_id ritornato");
    }
  };

  const handleSubmit = async () => {
    if (!question.trim()) {
      setStatus("Inserisci i dati necessari per il documento di assunzione.");
      return;
    }

    setStatus("Invio richiesta...");
    setResult(null);
    setTaskId(null);
    setIsLoading(true);

    try {
      await startMain({ question });
    } catch (_e) {
      setIsLoading(false);
      setStatus("Failed to start task");
    }
  };

  // Solo annulla: interrompe polling, resetta backend e NON riparte.
  const handleCancelOnly = async () => {
    // stop polling
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    const currentTask = taskId;
    setTaskId(null);
    setIsLoading(true);
    setStatus("Annullamento in corso…");

    try {
      // reset completo lato backend (kill + purge + flush + reseed)
      await fetch("/admin/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          reseed: true,
          status_all: "da_generare",
          purge: true,
          flush_backend: true,
          kill_mode: "soft"
        }),
      });
      setStatus(currentTask ? `Task ${currentTask} annullata.` : "Operazione annullata.");
    } catch (_e) {
      setStatus("Annullamento fallito (verifica backend).");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      if (result && result.final_cv) {
        await navigator.clipboard.writeText(result.final_cv);
        setStatus("Documento copiato negli appunti");
      }
    } catch (_e) {
      setStatus("Impossibile copiare negli appunti");
    }
  };

  return (
    <div className="zh-root">
      <header className="zh-topbar">
        <div className="zh-brand">
          <img src={logo} alt="ZeroHR Logo" className="zh-logo" />
          <div className="zh-title">
            <div className="zh-name">ZeroHR.ai</div>
            <div className="zh-sub">Agente AI per Consulenti del Lavoro</div>
          </div>
        </div>

        <div className="zh-top-actions">
          <span className="zh-badge zh-badge-ok">AI Lab Online</span>
          <span className="zh-badge">gpt-oss-120b</span>
          <img src={power} alt="power" className="badge-power" />

          <button
            className="zh-btn zh-btn-ghost"
            onClick={async function () {
              if (taskId) {
                try {
                  await fetch("/finalize/" + encodeURIComponent(taskId), {
                    method: "POST",
                    credentials: "include",
                  });
                } catch (_e) {}
              }
              window.location.reload();
            }}
          >
            Reset
          </button>
        </div>
      </header>

      <section className="zh-hero">
        <div className="zh-hero-left">
          <h1 className="zh-hero-title">Generatore Documenti di Assunzione</h1>
          <p className="zh-hero-desc">
            Automatizza la redazione e il controllo dei documenti di assunzione.
            ZeroHR reagisce agli eventi HR in tempo reale, senza input manuali ripetitivi.
          </p>
          <div className="zh-hero-cta">
            <button className="zh-btn zh-btn-primary" onClick={handleSubmit}>
              Avvia Automazione
            </button>
            <button className="zh-btn zh-btn-secondary" onClick={function () { setQuestion(""); }}>
              Pulisci Input
            </button>
          </div>
          <div className="zh-hero-flags">
            <span className="zh-flag">AI Act Compliant</span>
            <span className="zh-flag">HR Automation</span>
          </div>
        </div>

        <div className="zh-hero-right">
          <div className="zh-card zh-agent-card">
            <div className="zh-card-hd">
              <img src={logo} alt="ZeroHR Logo" className="zh-logo" />
              <div className="zh-card-title">ZeroHR AI Agent</div>
            </div>
            <div className="zh-card-bd">
              {isLoading ? (
                <div className="zh-loader">
                  <span className="zh-dot" />
                  <span className="zh-dot" />
                  <span className="zh-dot" />
                </div>
              ) : (
                <div className="zh-agent-idle">In attesa di input...</div>
              )}
            </div>
            <div className="zh-card-ft">
              <span className="zh-badge zh-badge-ok">Online</span>
              <span className="zh-badge">Agente: Assunzioni</span>
            </div>
          </div>
        </div>
      </section>

      <main className="zh-main">
        <div className="zh-col">
          <div className="zh-panel">
            <div className="zh-panel-hd">
              <h2 className="zh-panel-title">Dati per il Documento</h2>
              <span className="zh-badge">Richiesta</span>
            </div>
            <div className="zh-panel-bd">
              <textarea
                className="zh-textarea"
                value={question}
                onChange={function (e) { setQuestion(e.target.value); }}
                placeholder="Inserisci i dati di assunzione: anagrafica, ruolo, livello, CCNL, RAL, periodo di prova, sede, orario, benefit, scadenze..."
                rows={10}
              />
            </div>
            <div className="zh-panel-ft">
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <button className="zh-btn zh-btn-primary" onClick={handleSubmit}>
                  Genera e Controlla
                </button>
                {isLoading && taskId ? (
                  <button className="zh-btn zh-btn-danger" onClick={handleCancelOnly}>
                    Annulla
                  </button>
                ) : null}
              </div>
              <div className="zh-status">
                <span className="zh-status-label">Stato:</span>
                <span className="zh-status-text">{status || "Pronto"}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="zh-col">
          <div className="zh-panel">
            <div className="zh-panel-hd">
              <h2 className="zh-panel-title">Anteprima Documento</h2>
              {result ? <span className="zh-badge zh-badge-ok">Disponibile</span> : <span className="zh-badge">In attesa</span>}
            </div>

            <div className="zh-panel-bd">
              {result ? (
                <pre className="zh-doc">{result.final_cv}</pre>
              ) : (
                <div className="zh-empty">
                  Il documento generato apparirà qui. Avvia l’automazione per procedere.
                </div>
              )}
            </div>

            <div className="zh-panel-ft zh-panel-grid">
              <div className="zh-metrics">
                <div className="zh-metric">
                  <div className="zh-metric-k">Score</div>
                  <div className="zh-metric-v">{result ? `${result.score} / 10` : "-"}</div>
                </div>
                <div className="zh-metric">
                </div>
              </div>
              <div className="zh-actions">
                <button className="zh-btn zh-btn-secondary" onClick={handleCopy} disabled={!result}>
                  Copia Documento
                </button>
              </div>
            </div>

            {result && result.feedback ? (
              <div className="zh-panel-sub">
                <div className="zh-panel-sub-hd">Feedback di Controllo</div>
                <div className="zh-panel-sub-bd">{result.feedback}</div>
              </div>
            ) : null}
          </div>
        </div>
      </main>

      <footer className="zh-footer">
        <div>ZeroHR.ai • Event-driven HR Automation</div>
        <div>Demo tecnica: generatore e validatore documenti di assunzione</div>
      </footer>
    </div>
  );
}

export default ZeroHRDocGenerator;
