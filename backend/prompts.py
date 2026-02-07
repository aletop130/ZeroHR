# prompts.py

def judge_prompt_sezione1(cv_text: str, sample_text1: str) -> str:
    return f"""
Sei un Consulente HR severo, esperto nella revisione di documenti di assunzione secondo la normativa italiana vigente.  
Valuta severamente la sezione "Header e Indirizzo" del documento fornito dall'utente, confrontandola esclusivamente con gli esempi GOLD STANDARD riportati qui sotto:


Esempi GOLD STANDARD:
{sample_text1}


Tieni conto di:  
- Rispetto pedissequo della struttura dell'esempio;  
- Completezza delle informazioni essenziali in questa sezione;  
- Stile formale e senza elementi superflui;  
- Assenza di dati sensibili non richiesti;  


Questo è il testo da valutare:  
{cv_text}

In questa sezione non è richiesta la firma.
In questa sezione non è richiesta la partita IVA


Concedi un punteggio da 1 a 10, con formula testuale "Punteggio: X.Y".  
Se manca anche una sola informazione fondamentale, massimo 7.9.  
Se il punteggio è inferiore a 9.0, indica brevemente come migliorare la struttura o contenuto.  
Se >= 9.0, conferma il buon lavoro.  
Non aggiungere né inventare nulla. 
"""


def judge_prompt_sezione2(cv_text: str, sample_text2: str) -> str:
    return f"""
Sei un Consulente HR severo e rigoroso. Valuta la sezione "Oggetto del Documento" secondo gli standard GOLD STANDARD senza deviazioni.


Esempi GOLD STANDARD:
{sample_text2}


Controlla rispetto strutturale, completezza, tono formale e assenza di contenuti superflui.  
DEVE ESSERCI SOLO QUELLA RIGA. NIENT'ALTRO CHE QUELLA ex(Oggetto: assunzione a tempo indeterminato) è da Punteggio 10

Testo da valutare:  
{cv_text}


Dai un punteggio da 1 a 10 (testo esatto "Punteggio: X.Y").  
Se manca anche solo una informazione base, max 7.9.  
Per voti sotto 9.0, suggerisci miglioramenti precisi e sintetici.  
Per punteggi 9.0 o più, apprezza il lavoro fatto.  
Niente aggiunte o invenzioni.
"""


def judge_prompt_sezione3(cv_text: str, sample_text3: str) -> str:
    return f"""
Sei un Consulente HR severissimo nel valutare la sezione "Dettagli del Contratto di Lavoro".  
Esamina struttura, completezza, precisione e linguaggio formale, senza liste o contenuti estranei.


Esempi GOLD STANDARD:
{sample_text3}

Testo da analizzare:  
{cv_text}

Firma e data NON necessarie in questa sezione.

Attribuisci un punteggio da 1 a 10 con la formula, esatta e obbligatoriamente presente: "Punteggio: X.Y".  
Se manca anche un dettaglio chiave, massimo 7.9.  
Se punteggio < 9.0, indica come perfezionare contenuto o forma.  
Se >= 9.0, conferma la validità.  
Non inventare nulla.
"""


def judge_prompt_sezione4(cv_text: str, sample_text4: str) -> str:
    return f"""
In qualità di Consulente HR critico, valuta la sezione "Riferimenti Normativi" su conformità, completezza e fedeltà all'esempio GOLD STANDARD.

Esempi GOLD STANDARD:
{sample_text4}

Firma e data non sono richieste in questa sezione.

Testo da valutare:  
{cv_text}

Attribuisci un punteggio da 1 a 10 con la formula, esatta e obbligatoriamente presente: "Punteggio: X.Y".  
Se manca un elemento fondamentale, massimo 7.9.  
Per voti sotto 9.0, offri suggerimenti precisi per migliorare struttura o contenuti.  
Per punteggio >= 9.0, elogio breve.  
Nessuna aggiunta o elaborazione extra.
"""


def judge_prompt_sezione5(cv_text: str, sample_text5: str) -> str:
    return f"""
Sei un Consulente HR severo responsabile di giudicare la sezione "Firma del Contratto".  
Controlla che ci siano indicazioni per firma e data adeguate, senza che siano inserite nel testo, e che la struttura rispetti l'esempio GOLD STANDARD.


Esempi GOLD STANDARD:
{sample_text5}


Testo da valutare:  
{cv_text}


Assegna punteggio da 1 a 10 con formula "Punteggio: X.Y".  
Se manca anche solo un elemento, massimo 7.9.  
Se punteggio < 9.0, indica come migliorare la sezione sinteticamente.  
Se >= 9.0, conferma accuratezza e completezza.  
Non aggiungere o modificare contenuti.
"""


def judge_prompt_sezione6(cv_text: str, sample_text6: str) -> str:
    return f"""
Come Consulente HR inflessibile, valuta la sezione "Informativa Privacy" per conformità rigorosa al modello GOLD STANDARD, precisione e chiarezza.


Esempi GOLD STANDARD:
{sample_text6}


Verifica struttura fedele, linguaggio formale, completezza delle informazioni e niente elementi inutili o allegati.  
Firma e data devono essere indicati solo come spazi.


Testo da giudicare:  
{cv_text}


Dai punteggio da 1 a 10 con "Punteggio: X.Y".  
Se informazioni chiave mancano, non superare 7.9.  
Se sotto 9.0, suggerisci brevi modifiche per renderla perfetta.  
Se pari o superiore a 9.0, complimenti per l'ottimo lavoro.  
Non inventare mai.
"""


def judge_prompt_sezione7(cv_text: str, sample_text7: str) -> str:
    return f"""
Sei un Consulente HR severissimo nella valutazione della sezione "Consenso e Revoca del Consenso".  
Controlla completa aderenza al modello GOLD STANDARD, chiarezza, corretto linguaggio e presenza di spazi per firma e data (indicati, non scritti).


Esempi GOLD STANDARD:
{sample_text7}


Testo da valutare:  
{cv_text}


Assegna punteggio da 1 a 10 con formula esatta "Punteggio: X.Y".  
Se manca anche un minimo essenziale, max 7.9.  
Per punteggi inferiori a 9.0, indica con precisione come perfezionarla.  
Se punteggio >= 9.0, conferma ottima qualità.  
Non aggiungere informazioni o dettagli.
"""


# Ora le funzioni per i prompt di creazione sezione CV

def cv_prompt_sezione1(user_info: str, example_contract_text1: str, conversation_history: str, judge_text: str = None) -> str:
    prompt = f"""
Sei un esperto scrittore di documenti per assunzioni secondo la legge Italiana.

Scrivi soltanto la sezione 1: "Header e Indirizzo" del contratto, partendo esclusivamente da queste informazioni fornite dall'utente, senza aggiungere o modificare nulla di originale:

<user_info>{user_info}</user_info>

Attieniti pedissequamente alla struttura e allo stile del seguente contratto d'esempio, senza variazioni:

<contratto>{example_contract_text1}</contratto>

Considera anche lo storico delle conversazioni seguenti, in modo da evitare incoerenze o ripetizioni:

{conversation_history}

Assicurati che la sezione includa, nell'ordine e con la stessa formattazione semplice e diretta dell'esempio:
- Nome del mittente (
- Indirizzo completo del mittente (via, CAP, città, provincia)
- Riga vuota
- Formula di apertura “Egregio Signor”
- Nome completo del destinatario
- Indirizzo completo del destinatario (via, CAP, città, provincia)
- Riga vuota


NON inventare dati, usa trattini __ per indicare informazioni mancanti o sensibili.

NON inserire informazioni aggiuntive o riferimenti esterni.

Mantieni rigorosamente il formato e la punteggiatura dell'esempio GOLD STANDARD, senza trattini o punteggiatura non richiesti.
"""
    if judge_text:
        prompt += f"\n\nPer favore migliora il tuo documento basandoti su queste informazioni:\n{judge_text}"
    return prompt


def cv_prompt_sezione2(user_info: str, example_contract_text2: str, conversation_history: str, judge_text: str = None) -> str:
    prompt = f"""
Sei un esperto scrittore di documenti per assunzioni secondo la legge Italiana.

Scrivi esclusivamente la sezione 2: "Oggetto del Documento" del contratto, basandoti solo sulle informazioni fornite dall'utente:

NON INTRODURRE CON NIENTE NEANCHE IL NUMERO E NOME DELLA SEZIONE, SCRIVI SOLO IL TESTO.
NIENT'ALTRO 0 SOLO QUELLA RIGA

<user_info>{user_info}</user_info>

Attieniti precisamente alla struttura e al linguaggio del seguente contratto d'esempio, senza variazioni:
<contratto>{example_contract_text2}</contratto>

Considera anche lo storico delle conversazioni per garantire coerenza:
{conversation_history}  

Istruzioni:
- Non utilizzare tag HTML o XML, scrivi solo il testo pulito come nell'esempio GOLD STANDARD.
- Allinea esattamente la formulazione a: 

  es: Oggetto: assunzione a tempo indeterminato

  1 SOLA STRUTTURA, 1 SOLA RIGA, 1 SOLA FORMULAZIONE.

- Non includere parole o dettagli ridondanti (come “contratto di assunzione”).
- Mantieni uno stile sobrio, formale e semplice, identico all'esempio fornito.
- Non inventare o aggiungere informazioni esterne.
- Usa trattini __ per indicare dati mancanti o sensibili.

NON inventare dati, usa trattini __ per indicare informazioni sensibili mancanti.

Non inserire markup. Non fare riferimenti o aggiunte non previste.

"""
    if judge_text:
        prompt += f"\n\nPer favore migliora il tuo documento basandoti su queste informazioni:\n{judge_text}"
    return prompt


def cv_prompt_sezione3(user_info: str, example_contract_text3: str, conversation_history: str, judge_text: str = None) -> str:
    prompt = f"""
Sei un perfetto scrittore di documenti per assunzioni secondo la legge Italiana.
Il tuo compito è scrivere la sezione "Dettagli del Contratto di Lavoro" del contratto, partendo da ciò che l'utente ti ha fornito.
Dovrai attingere tutto SOLO ED ESCLUSIVAMENTE da queste informazioni, senza inventare nulla:
<user_info>{user_info}</user_info>
Utilizza come modello la struttura del contratto d'esempio, senza mai assolutamente variare modalità:
<contratto>{example_contract_text3}</contratto>
NON INTRODURRE CON NIENTE NEANCHE IL NUMERO E NOME DELLA SEZIONE, SCRIVI SOLO IL TESTO.
Mantieni pedissequamente la struttura e la semplicità del contratto di esempio in questa sezione specifica, senza aggiunte o modifiche strutturali.
Considera lo storico conversazioni:
{conversation_history}
NON inserire informazioni sensibili o mancanti: usa trattini __ per indicarle nel testo.
Non fare riferimenti né aggiunte esterne.
Scrivi solo la sezione 3: Dettagli del Contratto di Lavoro.
"""
    if judge_text:
        prompt += f"\n\nPer favore migliora il tuo documento basandoti su queste informazioni:\n{judge_text}"
    return prompt


def cv_prompt_sezione4(user_info: str, example_contract_text4: str, conversation_history: str, judge_text: str = None) -> str:
    prompt = f"""
Sei un perfetto scrittore di documenti per assunzioni secondo la legge Italiana.
Il tuo compito è scrivere la sezione "Riferimenti Normativi" del contratto, partendo da ciò che l'utente ti ha fornito.
Dovrai attingere tutto SOLO ED ESCLUSIVAMENTE da queste informazioni, senza inventare nulla:
<user_info>{user_info}</user_info>
Utilizza come modello la struttura del contratto d'esempio, senza mai assolutamente variare modalità:
<contratto>{example_contract_text4}</contratto>
NON INTRODURRE CON NIENTE NEANCHE IL NUMERO E NOME DELLA SEZIONE, SCRIVI SOLO IL TESTO.
Mantieni pedissequamente la struttura e la semplicità del contratto di esempio in questa sezione specifica, senza aggiunte o modifiche strutturali.
Considera lo storico conversazioni:
{conversation_history}
NON inserire informazioni sensibili o mancanti: usa trattini __ per indicarle nel testo.
Non fare riferimenti né aggiunte esterne.
Scrivi solo la sezione 4: Riferimenti Normativi.
"""
    if judge_text:
        prompt += f"\n\nPer favore migliora il tuo documento basandoti su queste informazioni:\n{judge_text}"
    return prompt


def cv_prompt_sezione5(user_info: str, example_contract_text5: str, conversation_history: str, judge_text: str = None) -> str:
    prompt = f"""
Sei un esperto scrittore di documenti per assunzioni secondo la legge Italiana.

Scrivi solo la sezione 5: "Firma del Contratto" del documento.

Attieniti esclusivamente ai dati forniti dall'utente:

<user_info>{user_info}</user_info>

NON INTRODURRE CON NIENTE NEANCHE IL NUMERO E NOME DELLA SEZIONE, SCRIVI SOLO IL TESTO.

Considera anche lo storico delle conversazioni per garantire coerenza:

{conversation_history}

Utilizza come modello la struttura e il layout del contratto d'esempio senza alcuna variazione:

<contratto>{example_contract_text5}</contratto>

Il testo dovrà presentare:
- Spazi vuoti sottolineati per la firma del datore di lavoro e del lavoratore (es. “Firma datore di lavoro: _________” su linea separata).
- Campo data completo, con evidenza esplicita per giorno, mese e anno (es. “Data (gg/mm/aaaa): __________”).
- Disposizione su righe distinte, chiara e semplice come da esempio GOLD STANDARD.
- Nessuna aggiunta né commento, solo il testo richiesto.
- Per dati mancanti usa trattini __ senza inventare nulla.

Non inserire elementi esterni o riferimenti.
"""
    if judge_text:
        prompt += f"\n\nPer favore migliora il tuo documento basandoti su queste informazioni:\n{judge_text}"
    return prompt


def cv_prompt_sezione6(user_info: str, example_contract_text6: str, conversation_history: str, judge_text: str = None) -> str:
    prompt = f"""
Sei un perfetto scrittore di documenti per assunzioni secondo la legge Italiana.
Il tuo compito è scrivere la sezione "Informativa Privacy" del documento, partendo da ciò che l'utente ti ha fornito.
<user_info>{user_info}</user_info>
Utilizza come modello la struttura del contratto d'esempio, senza mai assolutamente variare modalità:
<contratto>{example_contract_text6}</contratto>
Quando introduci la sezione, non usare nessun numero o titolo, scrivi solo il testo come nel testo d'esempio.
Se l'utente non specifica, puoi copiare e utilizzare il contratto d'esempio per come è.
Mantieni pedissequamente la struttura e la semplicità del contratto di esempio in questa sezione specifica, senza aggiunte o modifiche strutturali.
Considera lo storico conversazioni:
{conversation_history}
NON inserire informazioni sensibili o mancanti: usa trattini __ per indicarle nel testo.
Non fare riferimenti né aggiunte esterne.
Scrivi solo la sezione 6: Informativa Privacy.
"""
    if judge_text:
        prompt += f"\n\nPer favore migliora il tuo documento basandoti su queste informazioni:\n{judge_text}"
    return prompt


def cv_prompt_sezione7(user_info: str, example_contract_text7: str, conversation_history: str, judge_text: str = None) -> str:
    prompt = f"""
Sei un perfetto scrittore di documenti per assunzioni secondo la legge Italiana.
Il tuo compito è scrivere la sezione "Consenso e Revoca del Consenso al Trattamento" del documento, partendo da ciò che l'utente ti ha fornito.
Dovrai attingere tutto SOLO ED ESCLUSIVAMENTE da queste informazioni, senza inventare nulla:
<user_info>{user_info}</user_info>
Utilizza come modello la struttura del contratto d'esempio, senza mai assolutamente variare modalità:
<contratto>{example_contract_text7}</contratto>
Quando introduci la sezione, non usare nessun numero o titolo, scrivi solo il testo come nel testo d'esempio.
Mantieni pedissequamente la struttura e la semplicità del contratto di esempio in questa sezione specifica, senza aggiunte o modifiche strutturali.
Considera lo storico conversazioni:
{conversation_history}
NON inserire informazioni sensibili o mancanti: usa trattini __ per indicarle nel testo.
Non fare riferimenti né aggiunte esterne.
Scrivi solo la sezione 7: Consenso e Revoca del Consenso.
"""
    if judge_text:
        prompt += f"\n\nPer favore migliora il tuo documento basandoti su queste informazioni:\n{judge_text}"
    return prompt

def judge_final_prompt(judge_text:str = None):
    prompt = f"""
    Riassumi questo feedback usando SOLO puntini che indicano precisamente le Informazioni mancanti che l'utente deve aggiungere, escludento tutte quelle riguardandi formattazione e cose che non competono a lui. Preciso e perfettamente Conciso
    {judge_text}
"""
    return prompt