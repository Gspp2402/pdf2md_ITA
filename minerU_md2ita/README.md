# minerU_md2ita 🇮🇹🔬

> **Modulo di traduzione accademica automatizzata JSON-First, engine di traduzione multithread con protezione LaTeX/Code, ricucitura semantica e validazione deterministica.**

---

## 🎯 Obiettivo del Modulo

Il modulo **`minerU_md2ita`** costituisce la terza e conclusiva fase della pipeline `pdf2md_ITA`.

Partendo dai deliverable multimodali estratti da **MinerU** su Kaggle (strutturati in file JSON, testo markdown, formule LaTeX e immagini ritagliate), il modulo esegue una traduzione scientifica ad altissima fedeltà in lingua italiana accademica standard.

### 🌟 Caratteristiche Chiave del Traduttore Aggiornato:
1. **Architettura JSON-First:** Parsing diretto da `_content_list_v2.json` / `_content_list.json` con eliminazione a monte di numeri di pagina, intestazioni correnti (*running headers*) e frammenti spuri di layout.
2. **Motore di Traduzione Dedicato (`translate_engine.py`):**
   - **Sistema di Placeholders Avanzato:** Protegge e isola ermeticamente formule LaTeX display (`$$...$$`), formule inline (`$...$`), blocchi di codice (```` ```...``` ````), inline code (`` `...` ``) e sintassi delle immagini (`![...](images/...)`).
   - **Dizionario Tecnico Accademico (`polish_dsp_terminology`):** Normalizza automaticamente la terminologia scientifica e specialistica (es. *passa-basso*, *ritardo di gruppo*, *lineare tempo-invariante (LTI)*, *trasformata di Fourier discreta (DFT)*, ecc.).
   - **Esecuzione Concorrente Multithread:** Traduzione parallela dei chunk (`ThreadPoolExecutor`) con gestione automatica del rate limit, retry esponenziale e codifica UTF-8.
3. **Orchestratore Batch per Interi Volumi (`batch_translate_all.py`):** Traduzione automatizzata sequenziale o parallela di tutti i capitoli e di tutti i libri presenti nel dataset, con reportistica statistica finale sui tempi e validazione.
4. **Assemblaggio e Validazione Automatica di Integrità:** Verifica deterministica della parità dei delimitatori LaTeX, integrità dei blocchi di codice ed esistenza reale su disco di tutti i file grafici richiamati in `images/`.
5. **Supporto Nomi File Estesi su Windows:** Integrazione della gestione dei percorsi lunghi (`win_long_path`) per garantire totale compatibilità ed evitare errori `[WinError 3]`.

---

## 🏗️ Architettura a 3 Livelli (Framework DOE)

```
[input/<Libro>/<Capitolo>/] 
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│ 1. preprocess_minerU.py (Livello 3 - Deterministico)             │
│    Legge _content_list_v2.json, rimuove scorie OCR e header/footer│
│    Predispone output/<Libro>/<Capitolo>/images/ e chunk in .tmp/ │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. translate_engine.py / batch_translate_all.py (Livello 2 & 3)  │
│    Isolamento placeholder (LaTeX, Code, Img)                     │
│    Traduzione multithread EN -> IT con rate limiting & retry     │
│    Applicazione glossario scientifico polish_dsp_terminology     │
│    Ripristino accurato dei placeholder                           │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. assemble_chapter.py (Livello 3 - Deterministico)              │
│    Ricomposizione ordinata dei chunk tradotti                    │
│    Salvataggio deliverable: output/<Libro>/<Capitolo>/<Capitolo>.md│
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. validate_translation.py (Livello 3 - Deterministico)          │
│    Verifica parità LaTeX ($$, $), link immagini e blocchi codice │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Regole di Traduzione e Invarianti Protette

### 1. Invarianti Assolute (Zero Modifiche)
- **Formule Matematiche LaTeX:** Nessuna alterazione a simboli, pedici, apici, matrici o delimitatori (es. $H_{\mathrm{c}}(s)$, $z^{-1}$, $\Omega_0$).
- **Blocchi di Codice:** Codice sorgente Python, MATLAB, C, VHDL/Verilog e comandi terminale.
- **Funzioni e Librerie Software:** Nomi di funzioni come `buttord`, `filtfilt`, `numpy`, `scipy`.
- **Acronimi Internazionali:** IIR, FIR, DFT, DTFT, FFT, LTI, SNR, dB, CPU, FPGA.
- **Percorsi Immagine:** Link intatti alle cartelle `images/`.

### 2. Standardizzazione della Terminologia Scientifica
Il motore applica sostituzioni contestuali intelligenti:
- *passband* ➡️ `passa-banda`
- *stopband* ➡️ `arresta-banda`
- *lowpass* ➡️ `passa-basso`
- *highpass* ➡️ `passa-alto`
- *allpass* ➡️ `passa-tutto`
- *group delay* ➡️ `ritardo di gruppo`
- *discrete-time Fourier transform* ➡️ `trasformata di Fourier a tempo discreto (DTFT)`
- *linear time-invariant* ➡️ `lineare tempo-invariante (LTI)`

---

## 📂 Organizzazione File del Modulo

```
minerU_md2ita/
├── README.md                     # Questa documentazione
├── gemini.md                     # Istruzioni e ruoli dell'Agente per la traduzione
├── directives/
│   └── translate_minerU_book.md  # SOP e direttiva operativa di Livello 1
├── execution/
│   ├── preprocess_minerU.py      # Preprocessing JSON-First e generazione chunk
│   ├── translate_engine.py       # Motore di traduzione multithread con protezione LaTeX
│   ├── batch_translate_all.py    # Orchestratore batch per interi libri e capitoli
│   ├── assemble_chapter.py       # Assemblaggio ordinato dei chunk tradotti
│   └── validate_translation.py   # Validazione automatica parità LaTeX e immagini
├── input/                        # Risultati estratti da Kaggle (MinerU)
│   └── <Nome_Libro>/
│       └── <Capitolo>/
│           ├── _content_list_v2.json
│           ├── <Capitolo>.md
│           └── images/
├── output/                       # Deliverable finale pulito
│   └── <Nome_Libro>/
│       └── <Capitolo>/
│           ├── <Capitolo>.md     # File Markdown tradotto e validato in italiano
│           └── images/           # Figure e grafici del capitolo
└── .tmp/                         # Cartella temporanea di chunking (.tmp/<Libro>/<Capitolo>/)
```

---

## 🛠️ Come Utilizzare il Modulo

### Opzione A: Traduzione di un Singolo Capitolo

1. **Pre-elaborazione JSON-First:**
   ```bash
   python execution/preprocess_minerU.py --chapter "input/<Nome_Libro>/<Capitolo>"
   ```

2. **Traduzione automatica, assemblaggio e validazione:**
   ```bash
   python execution/translate_engine.py --chapter "<Capitolo>" --book "<Nome_Libro>" --workers 6
   ```

3. **(Opzionale) Validazione manuale aggiuntiva:**
   ```bash
   python execution/validate_translation.py --file "output/<Nome_Libro>/<Capitolo>/<Capitolo>.md"
   ```

---

### Opzione B: Traduzione Batch di Interi Libri

Per processare automaticamente in sequenza tutti i capitoli di tutti i libri pre-elaborati in `.tmp/`:

```bash
python execution/batch_translate_all.py --workers 8
```

È possibile limitare il numero di capitoli per una prova rapida:
```bash
python execution/batch_translate_all.py --workers 8 --max-chapters 2
```

Al termine del processo verrà stampato a terminale un riepilogo con:
- Numero totale di capitoli processati.
- Capitoli validati con successo.
- Eventuali avvisi o capitoli da revisionare.
- Tempo totale di elaborazione.
