# SOP: Traduzione e Ripristino di Libri Scientifici da MinerU (JSON-First)

## Obiettivo

Tradurre in italiano accademico standard qualsiasi libro o testo scientifico estratto tramite **MinerU** presente in `input/`, salvando il deliverable definitivo in `output/` con:
1. **Preservazione assoluta** di tutte le formule LaTeX (`$$...$$` e `$..$`), blocchi di codice, acronimi e percorsi delle immagini `![](images/...)`.
2. **Doppia dicitura per la terminologia tecnica**: Termine italiano seguito dall'originale inglese tra parentesi alla prima occorrenza in una sezione/capitolo (es. *banda passante (passband)*, *ritardo di gruppo (group delay)*).
3. **Elaborazione JSON-First**: Estrazione strutturata da `_content_list_v2.json` con eliminazione alla radice di header di pagina e numeri di pagina.
4. **Deliverable pulito**: Nella cartella di ogni capitolo `output/<Nome_Libro>/<Capitolo>/` risiedono **esclusivamente** `<Capitolo>.md` e la cartella `images/`.

---

## Flusso Operativo a 3 Livelli

```
[input/<Libro>/<Capitolo>/hybrid_auto/] 
       │
       ▼
1. execution/preprocess_minerU.py  ──► Parsing _content_list_v2.json, esclusione header/numeri, chunking in .tmp/
       │
       ▼
2. Agente LLM (Orchestrazione)    ──► Traduzione semantica dei chunk + ricucitura concetti interrotti
       │
       ▼
3. execution/assemble_chapter.py   ──► Scrittura diretta in output/<Libro>/<Capitolo>/<Capitolo>.md
       │
       ▼
4. execution/validate_translation.py ──► Validazione parità LaTeX, link immagini su disco e blocchi codice
```

---

## Guida Dettagliata agli Step

### Step 1: Pre-elaborazione Deterministica (JSON-First)
Esegui lo script di pre-elaborazione indicando il percorso del capitolo in `input/`:
```bash
python execution/preprocess_minerU.py --chapter "input/Applied_Digital_Signal_Processing_Theory_and_Practice/11_Design_of_IIR_filters"
```
Lo script:
- Legge `_content_list_v2.json` (o `_content_list.json` come fallback).
- Scarta `page_header`, `page_number` e `page_aside_text`.
- Ricompone i paragrafi (`paragraph`) con le relative formule inline `$formula$`.
- Normalizza i titoli di sezione (`title`).
- Mantiene intatti `equation_interline` e `code`.
- Genera i file di chunk semantici in `.tmp/<Capitolo>/chunk_XXX.md`.
- Prepara la cartella `output/<Nome_Libro>/<Capitolo>/` copiandovi la cartella `images/`.

### Step 2: Traduzione Semantica dell'Agente LLM
L'Agente elabora ciascun chunk sequenzialmente in `.tmp/<Capitolo>/chunk_XXX.md`:

1. **Riconnessione delle Frasi**: Se un paragrafo è interrotto da una figura o equazione, assicura che il testo tradotto mantenga continuità logica e sintattica.
2. **Convenzione Terminologica**:
   - Prima occorrenza: `termine italiano (*english term*)`.
   - Occorrenze successive: `termine italiano` o acronimo consolidato.
   - Non tradurre: formule LaTeX, nomi di funzioni software (es. `filtfilt`, `buttord`), nomi di variabili o codice sorgente.
3. **Salvataggio**: Salva l'output tradotto in `.tmp/<Capitolo>/chunk_XXX_ita.md`.

### Step 3: Ricomposizione Finale
Esegui lo script di assemblaggio:
```bash
python execution/assemble_chapter.py --chapter "11_Design_of_IIR_filters" --book "Applied_Digital_Signal_Processing_Theory_and_Practice"
```
Lo script:
- Unisce i chunk tradotti ordinatamente.
- Scrive il file finale `output/<Nome_Libro>/<Capitolo>/<Capitolo>.md`.

### Step 4: Validazione Formale e di Integrità
Esegui la validazione:
```bash
python execution/validate_translation.py --file "output/Applied_Digital_Signal_Processing_Theory_and_Practice/11_Design_of_IIR_filters/11_Design_of_IIR_filters.md" --original "input/Applied_Digital_Signal_Processing_Theory_and_Practice/11_Design_of_IIR_filters/hybrid_auto/11_Design_of_IIR_filters.md"
```
Verifiche effettuate:
- Parità delimitatori display math (`$$`) e inline math (`$`).
- Esistenza e raggiungibilità di tutti i percorsi immagini `![](images/...)` su disco in `output/<Libro>/<Capitolo>/images/`.
- Chiusura corretta di tutti i blocchi ```` ``` ````.
- Confronto conteggio equazioni/immagini rispetto all'originale.
