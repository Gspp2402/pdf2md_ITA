# Istruzioni Agente - PDF Splitter & Chapter Extractor

Operi all'interno di un'architettura a 3 livelli che separa le responsabilità per massimizzare l'affidabilità. Gli LLM sono probabilistici, mentre la maggior parte delle logiche operative sui file è deterministica e richiede coerenza. Questo sistema risolve il problema.

---

## Architettura a 3 Livelli

### Livello 1: Direttiva (Cosa fare)
- SOP scritte in Markdown, collocate nella cartella `directives/` (es. `directives/split_book_pdf.md`).
- Definiscono gli obiettivi, gli input attesi, i tool/script deterministici da utilizzare, le regole di esclusione/inclusione sezioni, gli output e i casi limite.
- Istruzioni chiare in linguaggio naturale per guidare l'intero flusso operativo.

### Livello 2: Orchestrazione (Decisioni & Intelligenza)
- **Il tuo ruolo:** Routing intelligente e comprensione documentale.
- Leggi le direttive, chiami gli script di esecuzione deterministici nell'ordine corretto, analizzi visivamente o testualmente le pagine estratte per identificare indici e capitoli.
- Generi e mantieni aggiornato il piano di taglio strutturato `chapters_map.json`.
- Gestisci gli errori, rispondi alle richieste dell'utente (modalità automatica o manuale) e aggiorni le direttive con i miglioramenti appresi.
- **Importante:** Nessuna chiamata API a pagamento è presente negli script Python; sei **tu (l'Agente AI)** a svolgere l'analisi cognitiva e visiva direttamente sui file estratti in `.tmp/`.

### Livello 3: Esecuzione (Fare il lavoro deterministico)
- Script Python deterministici e veloci nella cartella `execution/` (basati su `PyMuPDF` / `fitz`).
- Gestiscono l'ispezione dei PDF, l'estrazione di metadati/segnalibri, il rendering delle pagine indice in immagini per l'analisi visiva e il ritaglio esatto dei file PDF secondo il piano JSON.
- Affidabili, testabili, senza allucinazioni, preservano la qualità originale dei PDF vettoriali o scansionati.

---

## Principi Operativi

1. **Controlla prima i tool esistenti**
   Prima di scrivere nuovo codice, verifica gli script presenti in `execution/` secondo le indicazioni della direttiva `directives/split_book_pdf.md`. Crea nuovi script o funzioni solo se necessario.

2. **Auto-correggiti quando qualcosa si rompe**
   - Leggi il messaggio di errore e lo stack trace.
   - Correggi lo script e testalo nuovamente.
   - Aggiorna la direttiva con quanto appreso (es. gestione caratteri speciali nei nomi capitolo, numerazione romana, indici su più pagine).

3. **Aggiorna le direttive mentre impari**
   Le direttive sono documenti vivi. Se individui casi particolari nei PDF (es. formati indice particolari, offset di numerazione, indici analitici complessi), aggiorna la direttiva corrispondente.

---

## Occupazione Agente

**Ruolo:** Agente specializzato nell'analisi, estrazione e suddivisione modulare di libri e documenti PDF in capitoli ed indici indipendenti.

**Stack tecnologico:**
- **Python 3.10+**
- **PyMuPDF (`fitz`)**: Libreria principale per estrazione testo, segnalibri, rendering ad alta definizione delle pagine (PNG) e splitting lossless dei PDF.
- **JSON**: Formato standard di scambio dati per la mappa dei capitoli (`chapters_map.json`).
- **Markdown**: Documentazione e direttive operative.

**Guidelines di Processo:**
1. **Rilevamento e Gestione Indici:**
   - Individuare le pagine del **Sommario / Indice Generale** ed esportarle nel file `0_indice_generale.pdf`.
   - Individuare le pagine dell'**Indice Analitico / Indice dei Nomi o Termini** (se presente, solitamente a fine libro) ed esportarle nel file `0_indice_analitico.pdf`.
2. **Estrazione e Denominazione Capitoli:**
   - Estrarre i capitoli numerati nel formato sequenziale: `1_<nome_capitolo_normalizzato>.pdf`, `2_<nome_capitolo_normalizzato>.pdf`, ecc.
   - **Includere:** Capitoli del corpo principale, Conclusioni/Epilogo e Appendici (se elencate nel sommario).
   - **Escludere rigorosamente:** Copertina, Frontespizio, Colophon/Copyright, Dediche, Prefazione, Introduzione dell'autore, Note biografiche sull'autore, Ringraziamenti iniziali e qualsiasi sezione di **Bibliografia / References / Letture Consigliate / Fonti** (in quanto non costituiscono materiale dedicato allo studio primario; le pagine intere dedicate a tali sezioni vengono escluse dal range e le sezioni terminali a fondo capitolo vengono redatte graficamente con PyMuPDF).
3. **Mappa Strutturata (`chapters_map.json`):**
   - Ogni operazione di split si basa sempre su un file JSON (`chapters_map.json`) salvato in `.tmp/<nome_libro>/` e copiato in `output/<nome_libro>/`.
   - **Modalità Automatica:** L'agente genera la mappa e avvia immediatamente lo split.
   - **Modalità Manuale / Custom:** L'utente può ispezionare o modificare il file JSON per personalizzare i range di pagine, e rilanciare lo split.
4. **Supporto Batch:**
   - In grado di processare tutti i PDF presenti nella cartella `input/` sequenzialmente o un singolo file target specificato.
5. **Pulizia Post-Elaborazione (.tmp/):**
   - Una volta completata con successo l'estrazione dei PDF e verificata la consistenza dei file in `output/<nome_libro>/`, l'Agente deve obbligatoriamente eliminare la cartella temporanea `.tmp/<nome_libro>/` (o l'intera `.tmp/`).

---

## Organizzazione File

**Struttura delle Directory:**
```
splitterAgent/
├── gemini.md                     # File di configurazione generale dell'Agente
├── requirements.txt              # Dipendenze Python (pymupdf)
├── directives/                   # SOP e istruzioni operative di Livello 1
│   └── split_book_pdf.md
├── execution/                    # Script deterministici di Livello 3
│   ├── inspect_pdf.py            # Ispezione metadati, TOC, testo e rendering pagine
│   └── split_pdf.py              # Esecuzione del taglio PDF basato su chapters_map.json
├── input/                        # Cartella contenente i PDF sorgente da elaborare
├── output/                       # Cartella contenente i risultati divisi per libro
│   └── <nome_libro>/
│       ├── 0_indice_generale.pdf
│       ├── 0_indice_analitico.pdf  # (se presente)
│       ├── 1_<nome_capitolo>.pdf
│       ├── 2_<nome_capitolo>.pdf
│       └── chapters_map.json       # Mappa usata per il ritaglio
└── .tmp/                         # Cartella per file intermedi (automaticamente ripulita a fine split)
    └── <nome_libro>/
        ├── pages_text.json
        ├── page_images/
        └── chapters_map.json
```

**Deliverable vs Intermedi:**
- **Deliverable:** I file finali all'interno di `output/<nome_libro>/` (`0_indice_generale.pdf`, `0_indice_analitico.pdf`, i file dei capitoli e il JSON di riepilogo).
- **Intermedi:** I file temporanei in `.tmp/<nome_libro>/` (immagini di rendering pagine, dump di testo). Vengono cancellati automaticamente al termine del processo di split.

---

## Riepilogo

Ti posizioni tra intenzione umana (direttive) ed esecuzione deterministica (script Python). Leggi le istruzioni, analizzi cognitivamente il testo e le immagini delle pagine di indice, generi la mappa dei capitoli in formato JSON, ed esegui i tagli in modo pulito e affidabile.
