# splitterAgent 📑✂️

> **Modulo di ispezione, analisi cognitiva e suddivisione modulare deterministica di libri PDF in capitoli ed indici indipendenti.**

---

## 🎯 Obiettivo del Modulo

Il modulo **`splitterAgent`** rappresenta la prima fase della pipeline `pdf2md_ITA`. Il suo scopo è prendere in ingresso interi tomi accademici o manuali in formato PDF (sia digitali nativi sia scansionati) e suddividerli in file PDF autonomi ad alta qualità, isolando:

1. **`0_indice_generale.pdf`**: Il Sommario / Indice Generale del libro.
2. **`0_indice_analitico.pdf`**: L'Indice Analitico / Index dei termini (se presente a fine testo).
3. **`1_<nome_capitolo>.pdf`, `2_<nome_capitolo>.pdf`, ...**: I singoli capitoli di studio effettivi.

### 🚫 Esclusione Rigorosa del Materiale Non Didattico
Per massimizzare l'efficienza dello studio ed evitare computazione GPU inutile nelle fasi successive, il modulo esclude rigorosamente:
- Copertine, frontespizi e note di copyright/colophon.
- Dediche, ringraziamenti e biografie degli autori.
- Prefazioni e introduzioni non strutturate come capitolo.
- **Tutte le sezioni di Bibliografia / References / Letture Consigliate:**
  - *Pagine intere di bibliografia:* escluse automaticamente dal range di pagine del capitolo.
  - *Bibliografia a fondo capitolo:* rimossa visivamente tramite redazione grafica deterministica (PyMuPDF) direttamente nell'ultima pagina utile del capitolo.

---

## 🏗️ Architettura a 3 Livelli (Framework DOE)

Il modulo implementa il framework **DOE (Directive, Orchestration, Execution)**:

```
                      ┌────────────────────────────────────────┐
                      │  LIVELLO 1: DIRETTIVA (Markdown SOP)   │
                      │  directives/split_book_pdf.md          │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │  LIVELLO 2: ORCHESTRAZIONE (Agente AI) │
                      │  Analisi TOC, testo e rendering visivo │
                      │  Generazione chapters_map.json         │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │  LIVELLO 3: ESECUZIONE (PyMuPDF)       │
                      │  inspect_pdf.py & split_pdf.py         │
                      └────────────────────────────────────────┘
```

### Livello 1: Direttiva (`directives/split_book_pdf.md`)
Definisce la Procedura Operativa Standard (SOP): regole di inclusione/esclusione, convenzioni di denominazione dei file, calcolo degli offset tra pagine stampate e pagine fisiche del PDF, e policy di pulizia dei file intermedi.

### Livello 2: Orchestrazione (Agente AI)
L'Agente AI legge la direttiva ed esegue l'analisi cognitiva sui dati estratti:
- Interpreta i metadati e i segnalibri (TOC).
- In caso di PDF scansionati o senza segnalibri strutturati, ispeziona visivamente i rendering delle pagine (`.tmp/<libro>/page_images/page_*.png`) e i dump di testo (`pages_text.json`).
- Calcola gli intervalli di pagina fisici esatti `[start_page, end_page]` (1-indexed) e crea il file di configurazione `chapters_map.json`.

### Livello 3: Esecuzione Deterministica (`execution/`)
Script Python basati su **PyMuPDF (`fitz`)**, veloci, affidabili e senza perdita di qualità vettoriale:
- **`execution/inspect_pdf.py`**: Ispezione metadati, estrazione testo e rendering PNG delle pagine indice/iniziali.
- **`execution/split_pdf.py`**: Taglio fisico dei PDF secondo `chapters_map.json` con applicazione della redazione grafica anti-bibliografia.

---

## 📄 Formato del Piano di Taglio (`chapters_map.json`)

Il cuore dell'interoperabilità tra l'Agente e gli script di esecuzione è il file `chapters_map.json`:

```json
{
  "book_name": "titolo_libro",
  "source_pdf": "input/titolo_libro.pdf",
  "total_pages": 320,
  "indices": {
    "indice_generale": {
      "filename": "0_indice_generale.pdf",
      "pages": [7, 8, 9]
    },
    "indice_analitico": {
      "filename": "0_indice_analitico.pdf",
      "pages": [312, 313, 314, 315]
    }
  },
  "chapters": [
    {
      "index": 1,
      "title": "Introduzione ai Sistemi",
      "filename": "1_Introduzione_ai_Sistemi.pdf",
      "start_page": 15,
      "end_page": 42
    },
    {
      "index": 2,
      "title": "Filtri Digitali",
      "filename": "2_Filtri_Digitali.pdf",
      "start_page": 43,
      "end_page": 78
    }
  ]
}
```

> [!NOTE]
> Se l'indice analitico non è presente nel documento, il campo viene valorizzato come `"indice_analitico": null`.

---

## 📂 Organizzazione File del Modulo

```
splitterAgent/
├── README.md                     # Questa documentazione
├── gemini.md                     # Definizione del ruolo e delle istruzioni dell'Agente
├── requirements.txt              # Dipendenza PyMuPDF (pymupdf>=1.23.0)
├── directives/
│   └── split_book_pdf.md         # SOP e direttiva operativa di Livello 1
├── execution/
│   ├── inspect_pdf.py            # Script di ispezione metadati, testo e rendering PNG
│   └── split_pdf.py              # Script deterministico di taglio e redazione PDF
├── input/                        # Cartella contenente i PDF originali completi
├── output/                       # Deliverable finale suddiviso per libro
│   └── <nome_libro>/
│       ├── 0_indice_generale.pdf
│       ├── 0_indice_analitico.pdf
│       ├── 1_<nome_capitolo>.pdf
│       ├── 2_<nome_capitolo>.pdf
│       └── chapters_map.json
└── .tmp/                         # Cartella temporanea (cancellata al termine dello split)
    └── <nome_libro>/
        ├── pages_text.json
        ├── page_images/
        └── chapters_map.json
```

---

## 🛠️ Come Utilizzare il Modulo

### 1. Installazione Dipendenze
```bash
pip install -r requirements.txt
```

### 2. Ispezione del PDF
Posiziona il libro in `input/<nome_libro>.pdf` ed esegui:
```bash
python execution/inspect_pdf.py --input "input/<nome_libro>.pdf"
```
Questo genererà in `.tmp/<nome_libro>/` i metadati, il testo estratto e le immagini delle pagine di indice.

### 3. Generazione/Revisione della Mappa dei Capitoli
L'Agente AI (o l'utente in modalità manuale) crea il file `.tmp/<nome_libro>/chapters_map.json` verificando i numeri di pagina effettivi e le esclusioni.

### 4. Esecuzione del Taglio
Esegui lo split deterministico:
```bash
python execution/split_pdf.py --map ".tmp/<nome_libro>/chapters_map.json"
```

I PDF finali saranno generati e organizzati in `output/<nome_libro>/`, pronti per la successiva fase di estrazione su **Kaggle**.
