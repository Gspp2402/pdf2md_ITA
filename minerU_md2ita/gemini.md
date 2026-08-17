# Istruzioni Agente

Operi all'interno di un'architettura a 3 livelli che separa le responsabilità per massimizzare l'affidabilità. Gli LLM sono probabilistici, mentre la maggior parte delle logiche operative e di parsing è deterministica e richiede coerenza. Questo sistema risolve il problema.

## Architettura a 3 Livelli

**Livello 1: Direttiva (Cosa fare)**

- SOP scritte in Markdown, collocate in `directives/` (es. `translate_minerU_book.md`).
- Definiscono gli obiettivi, la convenzione terminologica bilingue, i formati attesi, i tool/script da eseguire e la gestione dei casi limite.
- Istruzioni chiare in linguaggio naturale.

**Livello 2: Orchestrazione (Decisioni)**

- Il tuo lavoro: routing intelligente e traduzione semantica ad alta fedeltà.
- Leggi le direttive, chiami gli strumenti deterministici di esecuzione in `execution/`, gestisci gli errori, traduci i blocchi semantici garantendo la continuità logico-concettuale, e aggiorni le direttive con ciò che impari.
- Sei il collante tra intenzione ed esecuzione deterministica.

**Livello 3: Esecuzione (Fare il lavoro)**

- Script Python deterministici in `execution/` operanti con approccio **JSON-First**:
  - `preprocess_minerU.py`: legge direttamente il file `_content_list_v2.json` (o `_content_list.json`) di MinerU, scarta automaticamente `page_header`, `page_number` e `page_aside_text`, isola formule e codice, compone i paragrafi e crea i chunk in `.tmp/`.
  - `assemble_chapter.py`: concatena i chunk tradotti e scrive direttamente in `output/<Nome_Libro>/<Capitolo>/<Capitolo>.md`.
  - `validate_translation.py`: verifica la parità dei delimitatori LaTeX (`$$`, `$`), l'esistenza delle immagini su disco e la chiusura corretta dei blocchi di codice.
- Affidabili, testabili, veloci. Nessun compito ripetitivo svolto manualmente.

---

## Principi Operativi

**1. Controlla prima i tool esistenti**
Prima di scrivere un nuovo script, controlla `execution/` secondo la tua direttiva (`directives/`).

**2. Elaborazione JSON-First da MinerU**
- L'estrazione da MinerU fornisce file strutturati `_content_list_v2.json`. Utilizza sempre questi JSON come sorgente primaria invece del markdown grezzo per eliminare alla radice running header, numeri di pagina e artefatti di layout.

**3. Traduzione Scientifica Accademica e Invarianti**
- **Doppia Dicitura**: Alla prima occorrenza di un concetto tecnico in una sezione/capitolo, usa la traduzione italiana accademica standard seguita dal termine originale inglese tra parentesi (es. *banda passante (passband)*, *ritardo di gruppo (group delay)*, *valori singolari (singular values)*). Nelle occorrenze successive mantieni la dicitura italiana consolidata o l'acronimo.
- **Invarianza Assoluta**: Non tradurre MAI:
  - Formule matematiche LaTeX inline (`$...$`) e display (`$$...$$`). Simboli, pedici e apici matematici rimangono intatti (es. $H_{\mathrm{c}}(s)$, $z^{-1}$, $\Omega_0$).
  - Blocchi di codice sorgente (es. ```matlab, ```python, ```c) e comandi terminale.
  - Nomi di funzioni, routine e librerie software (es. `buttord`, `filtfilt`, `numpy`, `scipy`).
  - Acronimi tecnici standard internazionali (es. IIR, FIR, DFT, DTFT, FFT, LTI, SNR, dB, CPU).
  - Nomi propri di autori e algoritmi (es. Butterworth, Chebyshev, Taylor, Fourier).
  - Percorsi dei tag immagine `![](images/...)`.

**4. Risoluzione delle Interruzioni di Concetto (Continuity Healing)**
- Nel caso in cui un paragrafo sia interrotto da una figura o un'equazione, l'Agente deve assicurare che la traduzione in italiano ricomponga un discorso fluido, privo di frammenti orfani, raccordando le frasi prima e dopo l'elemento inserito.

**5. Auto-correzione e Aggiornamento Continuo**
- Quando una validazione (`validate_translation.py`) segnala avvisi o errori, correggi immediatamente il testo o lo script e ripeti la validazione.
- Le direttive sono documenti vivi: aggiorna le SOP in `directives/` quando scopri nuovi casi limite.

---

## Organizzazione File e Regola Deliverable

**Regola di Pulizia del Deliverable:**
In `output/<Nome_Libro>/<Capitolo>/` devono essere presenti **esclusivamente**:
1. Il file markdown tradotto: `<Capitolo>.md` (stesso nome del capitolo originale).
2. La cartella `images/` contenente le immagini necessarie per quel capitolo.
Nessun file JSON, PDF, temporaneo o accessorio deve essere presente nella cartella del capitolo in `output/`.

**Struttura directory:**

- `input/` - Cartelle dei libri originali estratti da MinerU (es. `input/<Nome_Libro>/<Capitolo>/hybrid_auto/`)
- `output/` - Cartelle di output finali pulite (es. `output/<Nome_Libro>/<Capitolo>/` con solo `<Capitolo>.md` e `images/`)
- `directives/` - SOP operative in Markdown (es. `translate_minerU_book.md`)
- `execution/` - Script Python deterministici (`preprocess_minerU.py`, `assemble_chapter.py`, `validate_translation.py`)
- `.tmp/` - File intermedi e chunk temporanei di lavorazione (ignorati e cancellabili)

---

## Riepilogo

Ti posizioni tra intenzione umana (direttive) ed esecuzione deterministica JSON-First (script Python). Leggi le istruzioni, pre-elabori i documenti MinerU via JSON, traduci i blocchi semantici garantendo continuità e rigore scientifico, assembli il capitolo finale in `output/` e validi formalmente ogni equazione ed elemento grafico.

Sii pragmatico. Sii affidabile. Auto-correggiti.
