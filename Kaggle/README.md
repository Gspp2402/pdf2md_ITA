# Kaggle: Estrazione Multimodale con MinerU 🚀⚡

> **Modulo per l'esecuzione batch di MinerU su GPU Cloud (Kaggle), convertendo i capitoli PDF in Markdown strutturato, formule LaTeX e immagini ritagliate.**

---

## 🎯 Obiettivo del Modulo

Il modulo **`Kaggle`** costituisce la seconda fase della pipeline `pdf2md_ITA`. 

L'estrazione avanzata di documenti scientifici tramite **MinerU** richiede l'esecuzione di complessi modelli di Computer Vision (layout analysis, OCR, formula recognition). L'utilizzo di un ambiente cloud gratuito con acceleratore GPU (es. **NVIDIA Tesla T4** o **P100** su Kaggle) permette di processare interi libri in pochi minuti, senza gravare sulle risorse hardware locali.

---

## 📓 Il Notebook: `mineru-pdf2md.ipynb`

Il notebook Jupyter [`mineru-pdf2md.ipynb`](file:///c:/Users/giuse/Documents/pdf2md_ITA/Kaggle/mineru-pdf2md.ipynb) è configurato per l'elaborazione batch automatica e robusta:

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUSSO NOTEBOOK KAGGLE                   │
├─────────────────────────────────────────────────────────────┤
│ 1. Installazione MinerU (`mineru[core]`)                    │
│ 2. Scansione Dataset Input PDF (`/kaggle/input/...`)        │
│ 3. Esclusione automatica file di servizio (`0_indice_*.pdf`)│
│ 4. Loop Batch: `mineru -p <input> -o <output> -m auto`      │
│ 5. Creazione archivio finale `risultati_mineru.zip`         │
│ 6. Link diretto per il download dei deliverable             │
└─────────────────────────────────────────────────────────────┘
```

### Caratteristiche Salienti dello Script:
1. **Filtro File Indici:** Salta in automatico tutti i file che iniziano per `0_` (`0_indice_generale.pdf`, `0_indice_analitico.pdf`), concentrando la potenza di calcolo solo sui capitoli effettivi.
2. **Preservazione della Struttura:** Mantiene l'alberatura delle cartelle per autore/libro.
3. **Idempotenza:** Verifica l'eventuale presenza di capitoli già convertiti evitando duplicazioni computazionali.
4. **Output Completo:** Per ciascun capitolo viene generata la cartella contenente:
   - File markdown grezzo: `<Capitolo>.md`
   - File strutturato JSON-First: `_content_list_v2.json` (o `_content_list.json`)
   - Cartella grafica con tutte le figure e diagrammi ritagliati: `images/`
5. **Esportazione One-Click:** Compressione di tutti i risultati in `risultati_mineru.zip` per un download immediato.

---

## 🛠️ Guida Operativa Passo-Passo su Kaggle

### 1. Preparazione del Dataset su Kaggle
1. Accedi al tuo account su [kaggle.com](https://www.kaggle.com).
2. Vai su **Datasets** ➡️ **New Dataset**.
3. Carica la cartella contenente i capitoli PDF generati da `splitterAgent` (ad es. `output/<Nome_Libro>/`).
4. Assegna un titolo al dataset (es. `libri-pdf-input`) e salvalo come *Private*.

### 2. Creazione ed Esecuzione del Notebook
1. Vai su **Code** ➡️ **New Notebook**.
2. Nel menu in alto a destra, clicca su **File** ➡️ **Import Notebook** e carica [`mineru-pdf2md.ipynb`](file:///c:/Users/giuse/Documents/pdf2md_ITA/Kaggle/mineru-pdf2md.ipynb).
3. Nel pannello delle impostazioni a destra (*Notebook Options*):
   - **Accelerator:** Seleziona `GPU T4 x2` oppure `GPU P100`.
   - **Internet:** Abilita `Internet On` (necessario per installare `mineru[core]`).
4. Nel pannello **Input**, clicca su **Add Input** e aggiungi il Dataset con i PDF creato al punto 1.
5. Verifica che il percorso nel notebook `INPUT_DIR` corrisponda al percorso del dataset (es. `/kaggle/input/<nome-tuo-dataset>/...`).
6. Clicca su **Run All** (o esegui le celle in sequenza).

### 3. Download dei Risultati
1. Al termine dell'esecuzione, l'ultima cella mostrerà il link per scaricare `risultati_mineru.zip`.
2. In alternativa, nel pannello di destra alla voce **Output**, seleziona `risultati_mineru.zip` e clicca sui tre puntini ➡️ **Download**.
3. Estrai l'archivio scaricato nella cartella `input/` del modulo locale [`minerU_md2ita`](file:///c:/Users/giuse/Documents/pdf2md_ITA/minerU_md2ita/README.md).
