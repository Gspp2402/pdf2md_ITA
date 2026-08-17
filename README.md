# pdf2md_ITA 📚 ➡️ 🇮🇹 📝

> **Pipeline End-to-End per la suddivisione, estrazione multimodale (MinerU) e traduzione accademica in italiano di libri e testi scientifici in PDF.**

---

## 🎯 Motivazione e Origine del Progetto

Questo progetto nasce da un'esigenza concreta legata allo studio universitario ed è frutto dell'idea congiunta e della collaborazione tra me e il mio collega e compagno di studi **[@MaxT-21 / Massimo Tubito]**.

> *"Studiare materie scientifiche direttamente da libri in inglese può diventare pesante sia in termini di tempo sia di energie, soprattutto quando nei testi vengono utilizzati molti termini tecnici che non conosciamo o che richiedono comunque un ulteriore sforzo per essere compresi appieno.*
>
> *Leggere lo stesso contenuto in italiano rende lo studio più immediato e permette di concentrarsi maggiormente sui concetti, invece di dover dedicare parte del tempo alla lingua. Inoltre, andando avanti nel percorso accademico, i libri disponibili in italiano tendono a diminuire sempre di più. Visto che spesso non esiste un reale interesse nel creare versioni italiane di questi testi specialistici, abbiamo deciso di farlo noi.*
>
> *È quindi soprattutto una questione di tempo e facilità: all'università si cerca di arrivare al punto e studiare nel modo più efficace possibile. Avere il libro in italiano, in questo senso, è semplicemente un vantaggio."*

L'obiettivo di **`pdf2md_ITA`** è quindi rendere più rapido e agevole lo studio di testi scientifici disponibili principalmente in inglese, trasformando pesanti manuali PDF in capitoli Markdown modulari e puliti, con formule LaTeX conservate, immagini estratte e testo tradotto in italiano accademico con terminologia specialistica coerente.

---

## 🤖 Come è stato Realizzato: Framework DOE & Agente AI

Questo repository non è stato scritto interamente "a mano" con script monolitici, né si affida a prompt generici. È stato progettato e strutturato impostando file di controllo `gemini.md` conformi al **Framework DOE (Directive, Orchestration, Execution)** in collaborazione con un **Agente AI di Sviluppo** (*AI Coding Assistant*).

```text
┌─────────────────────────────────────────────────────────────┐
│                   ARCHITETTURA DOE (3 LIVELLI)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Livello 1: DIRETTIVA (SOP in Markdown)                     │
│  └─ Regole operative, vincoli e convenzioni terminologiche  │
│                                                             │
│  Livello 2: ORCHESTRAZIONE (Agente AI & Orchestratore Batch)│
│  └─ Comprensione documentale, decisioni, gestione workflow  │
│                                                             │
│  Livello 3: ESECUZIONE (Script Deterministici Python)       │
│  └─ PyMuPDF, JSON-First, Translation Engine multithread     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

* **Livello 1 - Direttive (Cosa fare):** Procedure Operative Standard (SOP) scritte in Markdown nella cartella `directives/` che stabiliscono regole, formati attesi e invarianti.
* **Livello 2 - Orchestrazione (Intelligenza & Flusso):** L'Agente AI interpreta le direttive, analizza cognitivamente indici e dump di testo, calcola gli offset ed esegue il coordinamento batch multi-volume.
* **Livello 3 - Esecuzione (Lavoro Deterministico):** Script Python veloci, deterministici e testabili in `execution/` che manipolano file, estraggono JSON, traducono in parallelo con isolamento delle formule LaTeX e convalidano formalmente i deliverable.

---

## 🔄 La Pipeline di Elaborazione in 3 Fasi

Il flusso di lavoro segue un ordine sequenziale rigoroso e ottimizzato:

```text
                  ┌───────────────────────────────┐
                  │ 1. PDF SORGENTE (Libro Intero) │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
    ┌───────────────────────────────────────────────────────────┐
    │  FASE 1: splitterAgent (Locale / PyMuPDF)                 │
    │  • Ispezione TOC e rendering visivo indici                │
    │  • Generazione mappa di taglio (chapters_map.json)        │
    │  • Estrazione: 0_indice_*.pdf e 1_<capitolo>.pdf, ...     │
    │  • Esclusione automatica di prefazioni e bibliografie     │
    └────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
    ┌───────────────────────────────────────────────────────────┐
    │  FASE 2: Kaggle (Cloud GPU / MinerU)                      │
    │  • Esecuzione notebook mineru-pdf2md.ipynb                │
    │  • Parsing avanzato di testo, formule LaTeX e figure      │
    │  • Generazione _content_list_v2.json + images/            │
    │  • Download dell'archivio risultati_mineru.zip            │
    └────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
    ┌───────────────────────────────────────────────────────────┐
    │  FASE 3: minerU_md2ita (Locale / JSON-First & Engine)     │
    │  • Preprocessing JSON-First (eliminazione header/footer)  │
    │  • Motore multithread dedicato con protezione LaTeX/Codice│
    │  • Glossario scientifico DSP & terminologia accademica    │
    │  • Orchestratore batch per interi volumi e capitoli       │
    │  • Assemblaggio finale: <Capitolo>.md + images/           │
    │  • Validazione automatica parità LaTeX e link immagini    │
    └───────────────────────────────────────────────────────────┘
```

### 1️⃣ Fase 1: Suddivisione Modulare (`splitterAgent`)

* Ispeziona il PDF originale estraendone testo e anteprime visive in `.tmp/`.
* Isola l'**Indice Generale** (`0_indice_generale.pdf`) e l'eventuale **Indice Analitico** (`0_indice_analitico.pdf`).
* Mappa ed estrae ogni capitolo utile (`1_<nome>.pdf`, `2_<nome>.pdf`, ...).
* **Esclude determinatamente il "rumore non didattico":** frontespizi, dediche, prefazioni dell'autore, ringraziamenti e tutte le sezioni di **Bibliografia / References** (sia a pagina intera che ritagliate/redatte graficamente se posizionate a fondo capitolo).

📖 *Per i dettagli completi, consulta il [README di splitterAgent](file:///c:/Users/giuse/Documents/pdf2md_ITA/splitterAgent/README.md).*

---

### 2️⃣ Fase 2: Estrazione Multimodale Accelerata (`Kaggle`)

* Esegue in ambiente cloud con GPU gratuita il notebook `mineru-pdf2md.ipynb`.
* Applica il motore di visione e layout documentale **MinerU** (`mineru[core]`) in batch sui singoli capitoli PDF.
* Salta automaticamente i file indice `0_*` per ottimizzare i tempi di GPU.
* Estrae con precisione chirurgica formule matematiche inline/display in LaTeX, ritaglia e salva tutte le figure in `images/` e struttura l'intero documento in `_content_list_v2.json`.
* Comprime i risultati in un unico pacchetto `risultati_mineru.zip`.

📖 *Per i dettagli completi, consulta il [README di Kaggle](file:///c:/Users/giuse/Documents/pdf2md_ITA/Kaggle/README.md).*

---

### 3️⃣ Fase 3: Traduzione & Validazione Accademica (`minerU_md2ita`)

* **Approccio JSON-First:** Lo script `preprocess_minerU.py` scarta alla radice intestazioni correnti, numeri di pagina e scorie OCR direttamente dal JSON di MinerU, creando chunk semantici puliti.
* **Motore di Traduzione Dedicato (`translate_engine.py`):**

  * Sistema di placeholder avanzato per la protezione assoluta di formule LaTeX inline (`$...$`), display (`$$...$$`), blocchi di codice, inline code e sintassi immagini.
  * Normalizzazione della terminologia tecnica specialistica tramite glossario accademico (`polish_dsp_terminology`).
  * Traduzione concorrente ad alte prestazioni (`ThreadPoolExecutor`) con retry esponenziale e gestione del rate limit.
* **Orchestratore Batch (`batch_translate_all.py`):** Esegue la traduzione, l'assemblaggio e la verifica di interi libri con un solo comando.
* **Assemblaggio & Validazione Automatica:** `assemble_chapter.py` compone il capitolo finale in `output/<Libro>/<Capitolo>/` e `validate_translation.py` verifica formalmente la parità dei delimitatori LaTeX, la chiusura dei blocchi di codice e l'esistenza delle immagini su disco.

📖 *Per i dettagli completi, consulta il [README di minerU_md2ita](file:///c:/Users/giuse/Documents/pdf2md_ITA/minerU_md2ita/README.md).*

---

## 📁 Struttura del Repository

```text
pdf2md_ITA/
├── README.md                      # Documentazione generale del progetto (questo file)
│
├── splitterAgent/                 # FASE 1: Suddivisione e Ispezione PDF
│   ├── README.md                  # Documentazione del modulo splitter
│   ├── gemini.md                  # Istruzioni e ruoli dell'Agente per lo split
│   ├── requirements.txt           # Dipendenze (pymupdf)
│   ├── directives/                # Direttiva SOP (split_book_pdf.md)
│   ├── execution/                 # Script deterministici (inspect_pdf.py, split_pdf.py)
│   ├── input/                     # PDF interi di partenza
│   └── output/                    # PDF splittati (indici + capitoli)
│
├── Kaggle/                        # FASE 2: Estrazione Multimodale Cloud GPU
│   ├── README.md                  # Istruzioni d'uso su Kaggle
│   └── mineru-pdf2md.ipynb        # Notebook Jupyter batch per MinerU
│
└── minerU_md2ita/                 # FASE 3: Traduzione e Validazione Accademica
    ├── README.md                  # Documentazione del modulo di traduzione
    ├── gemini.md                  # Istruzioni e ruoli dell'Agente traduttore
    ├── directives/                # Direttiva SOP (translate_minerU_book.md)
    ├── execution/                 # Script JSON-First & Translation Engine
    │   ├── preprocess_minerU.py   # Preprocessing e chunking JSON-First
    │   ├── translate_engine.py    # Motore di traduzione multithread con protezione LaTeX
    │   ├── batch_translate_all.py # Orchestratore batch multi-volume
    │   ├── assemble_chapter.py    # Assemblaggio dei capitoli
    │   └── validate_translation.py# Validatore parità LaTeX e immagini
    ├── input/                     # Risultati estratti da Kaggle (MinerU)
    └── output/                    # Deliverable finale (<Capitolo>.md + images/)
```

---

## 🚀 Guida Rapida all'Uso

### Prerequisiti Locali

* **Python 3.10+**
* Libreria `pymupdf` per lo splitter:

  ```bash
  pip install -r splitterAgent/requirements.txt
  ```

### Flusso Operativo Completo

1. **Splittare il libro:**

   * Posiziona il PDF in `splitterAgent/input/`.
   * Esegui l'ispezione:

     ```bash
     python splitterAgent/execution/inspect_pdf.py --input "splitterAgent/input/<tuo_libro>.pdf"
     ```
   * Genera/verifica la mappa capitoli `chapters_map.json` ed esegui lo split:

     ```bash
     python splitterAgent/execution/split_pdf.py --map "splitterAgent/.tmp/<tuo_libro>/chapters_map.json"
     ```

2. **Convertire su Kaggle:**

   * Carica i capitoli generati (`1_*.pdf`, `2_*.pdf`, ...) su un Dataset privato Kaggle.
   * Esegui il notebook `Kaggle/mineru-pdf2md.ipynb` con acceleratore GPU (T4 o P100).
   * Scarica `risultati_mineru.zip` e scompattalo in `minerU_md2ita/input/`.

3. **Tradurre e Validare:**

   * **Opzione Singolo Capitolo:**

     ```bash
     # Pre-elaborazione
     python minerU_md2ita/execution/preprocess_minerU.py --chapter "minerU_md2ita/input/<Libro>/<Capitolo>"

     # Traduzione automatica con motore multithread, assemblaggio e validazione
     python minerU_md2ita/execution/translate_engine.py --chapter "<Capitolo>" --book "<Libro>" --workers 6
     ```
   * **Opzione Batch Interi Volumi:**

     ```bash
     python minerU_md2ita/execution/batch_translate_all.py --workers 8
     ```

---

## 👥 Autori e Riconoscimenti

* **Ideazione e Sviluppo:** Progetto ideato, sviluppato e condiviso da **[Giuseppe Cifarelli / @Gspp2402]** e **[Massimo Tubito / @MaxT-21]**.
* **Metodologia:** Architettura a 3 livelli (Framework DOE) sviluppata in sinergia con un Agente AI di Sviluppo.
* **Finalità:** Progetto personale open-source realizzato a supporto dello studio universitario e della ricerca accademica.

