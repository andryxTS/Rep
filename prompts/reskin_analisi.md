
## DA COMPLETARE !!!!!!!!!!!!!!!!!


**RUOLO:**
Agisci come un Senior Frontend Architect e UX Designer.
Stai supervisionando il restyling di un **PRODUCTION CODEBASE** (un sito attivo, ricco di logica, SEO e dati) verso un Nuovo Design (estetico, ma probabilmente statico e strutturalmente diverso) disegnato con v0 o Google Stitch o altro soft.

**INPUT:**
In allegato a questo messaggio trovi questi file:
1. `repomix-output.txt`: L'intero codebase del progetto.
2. Questo file `PROMPT.md` con le istruzioni.
3.  **PRODUCTION CODEBASE (Master):** (file `repomix-master-output.txt`). Codice sacro per quanto riguarda funzionalità e dati.
4.  **NUOVO DESIGN (v0/stitch):** (file `repomix-v0-stitch-output.txt`). Riferimento sacro per quanto riguarda l'estetica **E IL LAYOUT COMPLETO**.

**MINDSET CRITICO:**
Il Master NON è una bozza. È un sito in produzione.
*   Il design v0/stitch è il **TARGET VISIVO FINALE**. Il tuo compito è fare in modo che il Master appaia ESATTAMENTE come v0/stitch dal punto di vista visivo.
*   **OGNI elemento visibile deve ricalcare v0/stitch**: colori, spaziature, tipografia, layout, forme, ombre, bordi.
*   **FUNZIONALITÀ MASTER = SACRE**: Ogni funzionalità interattiva del Master va PRESERVATA a meno che l'utente non dia esplicita approvazione per rimuoverla.
*   **CONTENUTO MASTER = SACRO**: Ogni elemento visibile (logo, immagine, testo, icona) del Master va PRESERVATO a meno che l'utente non dia esplicita approvazione per rimuoverlo/sostituirlo.
*   **Adottare il design v0/stitch ≠ Cambiare il contenuto**: Se v0/stitch mostra un'immagine generica ma il Master ha un logo specifico, devi CHIEDERE, non sostituire autonomamente.

**PROCEDURA DI ANALISI (Step-by-Step):**

**PASSO 1: Tech Audit & Dipendenze**
Analizza il codice v0/stitch riga per riga alla ricerca di dipendenze nascoste:
*   **Imports:** Cerca import o classi CSS che richiedono pacchetti esterni (es.`lucide-react`, `framer-motion`, `clsx`, `tailwind-merge`).
*   **UI Libraries:** Se riconosci componenti stile `shadcn/ui` o `@radix-ui`, identifica i pacchetti necessari (es. `class-variance-authority`, `@radix-ui/react-slot`).
*   **Plugins Tailwind:** Se nel CSS/Config v0/stitch vedi riferimenti a plugin (es. `animate-in`, `fade-in`, o classi `data-[state=...]`), annota l'obbligo di installare `tailwindcss-animate`.
*   **Confronto:** Verifica se questi pacchetti sono già presenti nel mio `package.json` o se vanno aggiunti.
*   Confronta con il mio `globals.css` e `tailwind.config.ts`.

**PASSO 2: Estrazione PRECISA dello Stile v0/stitch (Style DNA)**

**QUESTO PASSO È SUPER CRITICO.** Non fornire indicazioni generiche tipo "palette scura" o "usa colori chiari". Devi estrarre i VALORI ESATTI che saranno usati nella Color Reference Card della fase 2 (scrittura codice).

**⚠️ ATTENZIONE:** Nelle esecuzioni precedenti c'è stata confusione sui colori, risultando in siti bianco/nero. Questa estrazione deve essere PERFETTA e COMPLETA.

1. **Palette Colori ESATTA (DETTAGLIATISSIMA):**
   - Ispeziona il codice v0/stitch RIGA PER RIGA
   - Identifica OGNI SINGOLO colore usato per:
     * Background principale pagina
     * Background secondario (cards, sections)
     * Background input/form
     * Testo headings (h1, h2, h3)
     * Testo body/paragrafi
     * Testo muted/secondary
     * Primary/Accent colors (buttons, links)
     * Border colors
     * Hover states
   - Fornisci i valori in formato Tailwind + codice HSL/RGB
   
   **Output richiesto (FORMATO OBBLIGATORIO):**
   ```
    ═══════════════════════════════════
   PALETTE ESATTA v0/stitch (per Color Reference Card fase 2 (scrittura codice))
    ═══════════════════════════════════
   
   BACKGROUND COLORS:
   - Background principale: bg-slate-950 (hsl(222.2 84% 4.9%))
   - Background secondary: bg-slate-900 (hsl(222.2 84% 7%))
   - Background cards: bg-slate-800 (hsl(217.2 32.6% 17.5%))
   - Background input: bg-slate-700 (hsl(215.4 16.3% 46.9%))
   
   TEXT COLORS:
   - Testo headings: text-white (hsl(0 0% 100%))
   - Testo body: text-slate-300 (hsl(212.7 26.8% 83.9%))
   - Testo muted: text-slate-400 (hsl(215.4 16.3% 56.9%))
   
   PRIMARY/ACCENT:
   - Primary: bg-blue-600 (hsl(217.2 91.2% 59.8%))
   - Primary hover: bg-blue-700 (hsl(217.2 91.2% 54%))
   - Secondary: bg-slate-800 (hsl(217.2 32.6% 17.5%))
   
   BORDERS:
   - Border primary: border-slate-700 (hsl(215.4 16.3% 46.9%))
   - Border secondary: border-slate-800 (hsl(217.2 32.6% 17.5%))
   
   ⚠️ IMPORTANTE: Questi sono gli UNICI colori da usare in fase 2 (scrittura codice)
   ❌ VIETATO: bg-white, bg-black, text-black, bg-gray-*, text-gray-*
    ═══════════════════════════════════
   ```
   
   **VERIFICA FINALE OBBLIGATORIA:**
   Dopo aver estratto i colori, fai questa domanda a te stesso:
   - "Ho identificato il colore per OGNI tipo di elemento (backgrounds, testi, accent, borders)?"
   - "Ho fornito sia la classe Tailwind CHE il codice HSL/RGB?"
   - "Ho esplicitamente indicato i colori VIETATI?"
   
   Se anche UNA risposta è NO → RIVEDI l'estrazione

2. **Typography ESATTA:**
   - Font family (es. "font-sans usa Inter")
   - Text sizes per ogni elemento (es. "h1: text-5xl, p: text-base")
   - Font weights (es. "headings: font-bold, body: font-normal")

3. **Spacing & Layout ESATTO:**
   - Container max-width (es. "max-w-7xl")
   - Padding sections (es. "py-16 px-4")
   - Gap tra elementi (es. "gap-8", "space-y-6")
   - **IMPORTANTE**: Identifica se v0/stitch usa margin negativi o layout peculiari che potrebbero causare contenuti appiccicati ai bordi

4. **Componenti UI:**
   - Border radius (es. "rounded-xl", "rounded-lg")
   - Shadows (es. "shadow-lg", "shadow-none")
   - Transitions/Animations

**PASSO 3: Inventario Completo File Renderizzati (OBBLIGATORIO)**

**QUESTO È IL PASSO PIÙ CRITICO.** Devi creare una checklist ESAUSTIVA di OGNI file che renderizza contenuto visibile.

**METODOLOGIA:**
Per OGNI file nel codebase (pages, components, layout):

1. **Questo file renderizza HTML/JSX?** 
   - Se SÌ → DEVE essere nella checklist
   - Se NO (es. solo utility, types) → skip

2. **Per ogni file che renderizza, rispondi:**
   - **Ha corrispondenza in v0/stitch?** (Sì/No/Parziale)
   - **Ha funzionalità interattiva?** (Carousel, Form, Dropdown, Animation, Video, etc.) - Specifica QUALE
   - **Gli stili globali nuovi di v0/stitch lo romperanno?** (es. cambio da light a dark lo renderà bianco su bianco?) - Stima il rischio

**OUTPUT RICHIESTO (FORMATO SEMPLICE - NON TABELLARE):**

```
═══════════════════════════════════
CHECKLIST FILE RENDERIZZATI - ANALISI COMPLETA
═══════════════════════════════════

[1] FILE: src/app/page.tsx
    Renderizza: SÌ - Homepage completa
    Corrispondenza v0/stitch: SÌ - Completa
    Funzionalità interattive: Nessuna
    Rischio stili globali: BASSO
    Azione prevista: Restyling completo HTML/CSS con v0/stitch
    
[2] FILE: src/components/Hero.tsx
    Renderizza: SÌ - Sezione hero con logo e titolo
    Corrispondenza v0/stitch: PARZIALE - v0/stitch ha immagine hero, Master ha logo
    Funzionalità interattive: useState per tabs
    Rischio stili globali: BASSO
    Azione prevista: RICHIEDE DECISIONE - Conflitto contenuto (logo vs immagine)
    
[3] FILE: src/components/ImageCarousel.tsx
    Renderizza: SÌ - Carousel 5 immagini con autoplay
    Corrispondenza v0/stitch: PARZIALE - v0/stitch mostra singola immagine statica
    Funzionalità interattive: Carousel autoplay, touch gestures, navigation buttons
    Rischio stili globali: MEDIO
    Azione prevista: RICHIEDE DECISIONE - Conflitto funzionalità
    
[4] FILE: src/app/privacy/page.tsx
    Renderizza: SÌ - Pagina privacy con sezioni
    Corrispondenza v0/stitch: NO - Pagina orfana
    Funzionalità interattive: Nessuna
    Rischio stili globali: ALTO - Diventerà bianco su bianco
    Azione prevista: Wrapper stilistico con palette v0/stitch

[5] FILE: src/components/CallToAction.tsx
    Renderizza: SÌ - Sezione CTA con form
    Corrispondenza v0/stitch: NO - Sezione orfana
    Funzionalità interattive: Form submit con validation
    Rischio stili globali: ALTO - Testo diventerà invisibile
    Azione prevista: Wrapper stilistico + preservare form

... (continua per OGNI file che renderizza)

═══════════════════════════════════
TOTALE FILE ANALIZZATI: [numero]
File con corrispondenza completa: [numero]
File con corrispondenza parziale: [numero]
File orfani: [numero]
File che richiedono decisione utente: [numero]
═══════════════════════════════════
```

**REGOLE CHECKLIST:**
- Nessun file renderizzato può essere omesso
- Se un file importa/usa altri componenti che renderizzano, anche quelli vanno nella lista
- Pagine nested (es. `/blog/[slug]`) vanno incluse
- Layout e template files vanno inclusi

**PASSO 4: Identificazione ESAUSTIVA Conflitti (MASSIMA PRIORITÀ)**

**QUESTO È IL PASSO PIÙ IMPORTANTE.** Devi identificare OGNI singolo conflitto che richiede decisione dell'utente.

**DEFINIZIONE DI CONFLITTO:**
Un conflitto esiste quando c'è UNA QUALSIASI di queste situazioni:

**CATEGORIA 1 - Conflitti di Funzionalità:**
- Master ha funzionalità interattiva (carousel, video, form complesso, animation, slider, accordion)
  E v0/stitch mostra versione statica o semplificata
- **Esempi:**
  - ✅ Master: Carousel 5 immagini autoplay → v0/stitch: Singola immagine = CONFLITTO
  - ✅ Master: Video player con controlli → v0/stitch: Thumbnail statico = CONFLITTO
  - ✅ Master: Accordion 10 sezioni → v0/stitch: 3 sezioni sempre aperte = CONFLITTO

**CATEGORIA 2 - Conflitti di Contenuto:**
- Master ha elemento visibile specifico (logo, icona, immagine, badge, award)
  E v0/stitch mostra elemento diverso o lo rimuove
- **Esempi:**
  - ✅ Master: Logo aziendale → v0/stitch: Immagine generica = CONFLITTO
  - ✅ Master: Badge certificazione → v0/stitch: Nessun badge = CONFLITTO
  - ✅ Master: 5 icone servizi → v0/stitch: 3 icone diverse = CONFLITTO
  - ✅ Master: Breadcrumb navigation → v0/stitch: Nessun breadcrumb = CONFLITTO

**CATEGORIA 3 - Conflitti di Dimensioni/Proporzioni:**
- Master ha immagine/elemento con dimensioni/aspect ratio specifico
  E v0/stitch ha dimensioni/proporzioni drasticamente diverse
- **Esempi:**
  - ✅ Master: Immagine hero 16:9 full-width → v0/stitch: Immagine 1:1 centrata = CONFLITTO
  - ✅ Master: Gallery 4 colonne → v0/stitch: Gallery 2 colonne = CONFLITTO (potrebbe nascondere contenuto)

**CATEGORIA 4 - Conflitti Data Source:**
- Master carica dati da CMS/API/Database
  E v0/stitch mostra dati hardcoded/statici
- **Esempi:**
  - ✅ Master: Hero image da Sanity CMS → v0/stitch: Path immagine hardcoded = CONFLITTO
  - ✅ Master: Team members da API → v0/stitch: 3 membri hardcoded = CONFLITTO

**NON sono conflitti (risolvi automaticamente usando v0/stitch):**
- ❌ Differenze puramente estetiche (colori diversi, font diversi, spaziature diverse)
- ❌ Semplici riorganizzazioni layout (flex vs grid, 3 colonne vs 4 colonne per card identiche)
- ❌ Data density quando è solo questione di loop (.map su N elementi vs 3 hardcoded) → mantieni loop

**REGOLA D'ORO PER IDENTIFICARE CONFLITTI:**
Chiediti: "Se applico v0/stitch, l'utente perderà qualcosa che aveva prima (funzionalità, contenuto specifico, dati dinamici)?"
- Se SÌ → È un CONFLITTO → Devi fare una domanda
- Se NO → NON è conflitto → Risolvi usando v0/stitch

---

**OUTPUT RICHIESTO (Report di Analisi):**

### 1. 🎨 Style DNA di v0/stitch (DETTAGLIATO)

**Palette Colori ESATTA:**
```
Background principale: [classe Tailwind + codice colore]
Testo principale: [classe Tailwind + codice colore]
Primary/Accent: [classe Tailwind + codice colore]
Secondary: [classe Tailwind + codice colore]
Borders: [classe Tailwind + codice colore]
Muted/Disabled: [classe Tailwind + codice colore]
```

**Typography:**
```
Font Family: [es. Inter via font-sans]
H1: [es. text-5xl font-bold]
H2: [es. text-3xl font-semibold]
Body: [es. text-base font-normal]
Small: [es. text-sm]
```

**Layout & Spacing:**
```
Container: [es. max-w-7xl mx-auto]
Section Padding: [es. py-16 px-4]
Gap tra elementi: [es. gap-8]
Border Radius: [es. rounded-xl]
Shadows: [es. shadow-lg]
⚠️ Layout Peculiarities: [es. "v0/stitch usa mx-auto per centrare, NESSUN margin negativo rilevato"]
```

**Dipendenze Tecniche:**
- Pacchetti npm da installare: [lista esatta]
- Plugin Tailwind necessari: [lista esatta]
- Font strategy: [sostituire o mantenere?]

### 2. 📋 CHECKLIST COMPLETA FILE RENDERIZZATI

[Inserisci qui la lista completa del PASSO 3 in formato semplice]

### 3. ⚠️ CONFLITTI IDENTIFICATI (COMPLETO - NESSUNO ESCLUSO)

**TOTALE CONFLITTI TROVATI:** [numero]

**Se NON ci sono conflitti, scrivi: "NESSUN CONFLITTO RILEVATO - Tutti i componenti sono compatibili"**

**Per OGNI conflitto, usa questo formato:**

```
═══════════════════════════════════
CONFLITTO #[N]: [Nome Componente/Sezione]
CATEGORIA: [Funzionalità/Contenuto/Dimensioni/Data Source]
═══════════════════════════════════

SITUAZIONE MASTER:
- Elemento: [descrizione dettagliata]
- Funzionalità: [se applicabile]
- Data Source: [CMS/API/Hardcoded/Props]
- Implementazione tecnica: [hooks, handlers, logica]

SITUAZIONE v0/stitch:
- Elemento: [descrizione dettagliata]
- Differenza critica: [cosa cambia]

IMPATTO SE ADOTTO v0/stitch SENZA CHIEDERE:
- Cosa si perde: [lista specifica]
- Rischio utente finale: [Alto/Medio/Basso]

═══════════════════════════════════

OPZIONI:

[A] PRESERVA MASTER (Consigliato per non perdere funzionalità)
    ✓ Mantieni: [elemento/funzionalità Master]
    ✓ Applica: Solo stili v0/stitch (colori, font, spacing)
    ⚠️ Nota: Aspetto potrebbe differire da v0/stitch in alcuni dettagli
    📋 Strategia: Merge Conservativo (B)

[B] ADOTTA v0/stitch COMPLETAMENTE
    ✗ Rimuovi: [elemento/funzionalità Master]
    ✓ Sostituisci con: [elemento v0/stitch]
    ⚠️ PERDITE: [lista specifica cosa si perde]
    📋 Strategia: Restyling Completo (A)

[C] SOLUZIONE IBRIDA
    [Proponi soluzione specifica che bilancia - es. "Mantieni carousel ma rimuovi autoplay"]

[D] CUSTOM
    Specifica la tua soluzione personalizzata

═══════════════════════════════════
```

[Ripeti per OGNI conflitto - non tralasciarne nessuno]

### 4. 🛡️ Piano Esecuzione (DETTAGLIATO)

**File Configurazione Globale:**
- [ ] tailwind.config.ts - Applica colori Style DNA v0/stitch
- [ ] src/app/globals.css - Variabili CSS esatte v0/stitch
- [ ] src/app/layout.tsx - Font e body classes v0/stitch

**File Strategia A (Restyling Completo - Struttura v0/stitch):**
- [ ] [path] - [breve descrizione modifica]
- [ ] ...

**File Strategia B (Merge Conservativo - Solo stili su struttura esistente):**
- [ ] [path] - [descrizione conflitto risolto] - SOLO se utente sceglie Opzione A
- [ ] ...

**File Strategia C (Wrapper Stilistico - Orfani):**
- [ ] [path] - Rischio: [ALTO/MEDIO/BASSO] - [breve descrizione fix]
- [ ] ...

**DICHIARAZIONE IMPEGNO:**
Dichiara esplicitamente:
*"Mi impegno a:
1. Identificare e presentare ALL'UTENTE ogni singolo conflitto (funzionalità, contenuto, dimensioni, data source)
2. NON rimuovere NESSUN elemento visibile o funzionalità del Master senza approvazione esplicita
3. NON sostituire elementi specifici (logo, immagini, icone) con elementi generici senza approvazione
4. NON convertire dati dinamici (da CMS/API) in dati hardcoded senza approvazione
5. Applicare i colori ESATTI dello Style DNA v0/stitch (non colori generici o inventati)
6. Modificare OGNI file nella checklist che ha rischio ALTO o MEDIO stili globali
7. Verificare che NESSUN contenuto venga appiccicato ai bordi (padding min px-4 su OGNI sezione)
8. Garantire contrasto WCAG AA (4.5:1) su OGNI combinazione testo/sfondo"*

**NON SCRIVERE CODICE DI PROGETTO ANCORA. Procedi con l'Analisi COMPLETA e ESAUSTIVA seguendo TUTTI i passi rigorosamente.**