# SOP: Suddivisione Libro PDF in Capitoli e Indici

## Obiettivo
Prendere in input uno o più file PDF (libri/documenti sia con testo digitale che scansionati), individuare con precisione:
1. Le pagine del **Sommario / Indice Generale** ed estrarle in `0_indice_generale.pdf`.
2. Le pagine dell'eventuale **Indice Analitico** ed estrarle in `0_indice_analitico.pdf`.
3. I singoli **Capitoli** (escludendo prefazione, biografia dell'autore, ringraziamenti, colophon iniziale, e sezioni di references/bibliografia) ed estrarli in `1_<nome_capitolo>.pdf`, `2_<nome_capitolo>.pdf`, ecc.

---

## Flusso Operativo Passo-Passo

### 1. Ricerca Input
- Esaminare i file PDF presenti nella cartella `input/` o considerare il file specificato dall'utente.
- Identificare il nome base del libro (es. `input/mio_libro.pdf` -> `mio_libro`).

### 2. Ispezione Deterministica (Livello 3)
Eseguire lo script di ispezione:
```bash
python execution/inspect_pdf.py --input "input/<nome_file>.pdf"
```
Questo script genera in `.tmp/<nome_libro>/`:
- `meta.json`: Metadati del documento, numero totale di pagine, e segnalibri nativi/TOC (se presenti nel PDF).
- `pages_text.json`: Estratto del testo di tutte le pagine (o delle prime 50 e ultime 50 pagine per libri molto voluminosi).
- `page_images/`: Rendering ad alta definizione (PNG) delle prime 30 pagine e ultime 20 pagine per consentire l'analisi visiva delle pagine scansionate o impaginate graficamente.

### 3. Analisi Cognitiva dell'Agente (Livello 2)
L'agente (tu) analizza i dati estratti:
- **Indice Generale (Sommario):**
  - Cerca termini chiave come "Sommario", "Indice", "Table of Contents", "Contents".
  - Se il PDF è nativo/testuale, legge `pages_text.json`.
  - Se il PDF è scansionato o privo di testo, visiona le immagini in `.tmp/<nome_libro>/page_images/page_*.png`.
  - Determina le pagine fisiche esatte (1-indexed) che contengono l'indice generale.
- **Indice Analitico:**
  - Controlla le ultime pagine del documento cercando "Indice analitico", "Indice dei nomi", "Indice per argomenti", "Index".
  - Determina le pagine fisiche esatte dell'indice analitico (se presente).
- **Mappatura dei Capitoli:**
  - Legge i titoli dei capitoli e i numeri di pagina indicati nel sommario.
  - Calcola l'eventuale offset tra la numerazione stampata sulla pagina (araba/romana) e il numero di pagina fisica del PDF (es. la pagina stampata 1 potrebbe corrispondere alla pagina fisica 15 del PDF).
  - **Filtro Esclusioni:** Esclude prefazioni ("Prefazione", "Foreword"), informazioni sull'autore ("L'autore", "Note biografiche"), ringraziamenti, introduzioni non capitolo, colophon, e qualsiasi sezione di **Bibliografia / References / Riferimenti bibliografici / Further Reading / Letture consigliate** (non costituiscono materiale dedicato allo studio).
  - **Filtro Inclusioni:** Include tutti i capitoli effettivi, conclusioni/epilogo e appendici esplicite.
  - Calcola il range esatto di pagine fisiche `[start_page, end_page]` per ciascun capitolo (1-indexed, estremi inclusi).

### 4. Generazione del Piano di Taglio (`chapters_map.json`)
L'agente scrive il file strutturato `.tmp/<nome_libro>/chapters_map.json` nel seguente formato:

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
      "title": "Introduzione ai Sistemi Complessi",
      "filename": "1_Introduzione_ai_Sistemi_Complessi.pdf",
      "start_page": 15,
      "end_page": 42
    },
    {
      "index": 2,
      "title": "Architetture Distribuite",
      "filename": "2_Architetture_Distribuite.pdf",
      "start_page": 43,
      "end_page": 78
    }
  ]
}
```

*Nota: Se l'indice analitico non è presente nel libro, impostare `"indice_analitico": null`.*

### 5. Modalità di Esecuzione (Automatica vs Manuale)
- **Modalità Automatica:** L'agente genera `chapters_map.json` e procede immediatamente con lo splitting.
- **Modalità Manuale / Revisione:** L'agente mostra il riepilogo all'utente o attende modifiche a `chapters_map.json`.
- **Riesecuzione:** L'utente può modificare direttamente `chapters_map.json` ed eseguire lo script di split per ottenere un taglio personalizzato.

### 6. Esecuzione del Taglio Deterministico (Livello 3)
Eseguire lo script di split:
```bash
python execution/split_pdf.py --map ".tmp/<nome_libro>/chapters_map.json"
```
Lo script salva i PDF finali e una copia di `chapters_map.json` in `output/<nome_libro>/`.

### 7. Verifica dei Risultati
- Verificare che tutti i file PDF siano stati generati nella cartella `output/<nome_libro>/`.
- Verificare che nessun capitolo si sovrapponga in modo errato o perda pagine.
- Mostrare all'utente l'elenco dei file generati con i relativi range di pagina.

### 8. Pulizia dei File Temporanei (.tmp/)
- Una volta che tutti i file PDF sono stati estratti e verificati con successo nella cartella `output/<nome_libro>/`, eliminare la cartella temporanea `.tmp/<nome_libro>/` (o l'intera directory `.tmp/` se il batch è concluso).
- Preservare esclusivamente i deliverable finali in `output/<nome_libro>/`.

---

## Casi Limite e Best Practices Apprese

1. **Spaziature nei Nomi File (Windows Path Compatibility):**
   - Rimuovere sempre gli spazi finali e iniziali (`stem.strip()`) per evitare errori `[WinError 3]` durante la creazione di directory su Windows.
2. **PDF senza segnalibri TOC nativi strutturati:**
   - Se il PDF ha segnalibri generici (es. solo nomi di file parziali o un unico nodo radice), l'Agente esegue l'analisi cognitiva direttamente su `pages_text.json` per rintracciare i pattern di inizio capitolo ("Chapter 1", "1. Introduction", ecc.).
3. **Assenza dell'Indice Analitico:**
   - Se il documento non contiene un indice analitico finale, impostare `"indice_analitico": null` nel JSON.
4. **Esclusione e Redazione Bibliografie / References Integrate:**
   - In quanto materiale non destinato allo studio primario, qualsiasi bibliografia, lista di fonti, letture consigliate o references va rimossa.
   - **Pagine intere di bibliografia:** Quando occupano una o più pagine finali complete (es. pag. 385), vengono escluse dall'intervallo `[start_page, end_page]` nel JSON (es. impostando `end_page: 384`).
   - **Bibliografia a fondo pagina (PyMuPDF Redaction):** Se l'intestazione (*"References"*, *"Bibliography"*, *"Bibliografia"*, *"Further Reading"*, ecc.) compare nella parte inferiore dell'ultima pagina utile (es. a metà di pag. 384), `execution/split_pdf.py` applica la redazione visiva deterministica con riempimento bianco da quel titolo a fondo pagina.
   - **Controllo e Override:** Il meccanismo è attivo per default e può essere sovrascritto nel file `chapters_map.json` impostando `"redact_trailing_references": false`.

