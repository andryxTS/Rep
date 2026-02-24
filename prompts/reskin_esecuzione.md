
## DA COMPLETARE !!!!!

**Obiettivo:** Generare codice pronto per la produzione che faccia apparire il sito Master ESATTAMENTE come v0/stitch dal punto di vista visivo, preservando OGNI funzionalità interattiva e OGNI elemento di contenuto del Master a meno di approvazione esplicita contraria.

**RUOLO:**
Agisci come un Senior Full-Stack Developer specializzato in Next.js/React, con eccellente eye for design, attenzione maniacale ai dettagli visivi, e rispetto assoluto per le funzionalità e il contenuto esistente.

**CONTESTO:**
Procediamo con il merge basato sulle mie scelte per i conflitti: [INSERISCI TUE RISPOSTE QUI].
Hai anche:
- Style DNA ESATTO di v0/stitch dall'analisi precedente
- CHECKLIST COMPLETA file renderizzati dall'analisi precedente
- ELENCO COMPLETO conflitti e decisioni utente dall'analisi precedente

**⚠️ PROBLEMA CRITICO DA EVITARE:**
Nelle esecuzioni precedenti c'è stata una tendenza a:
- Estrarre correttamente i colori di v0/stitch in fase 1 (analisi)
- Ma poi usare colori generici (bg-white, bg-black, text-gray-900) in fase 2 (scrittura codice)
- Risultato: sito in bianco/nero invece dello schema colori di v0/stitch

**SOLUZIONE OBBLIGATORIA:**
Devi creare e consultare COSTANTEMENTE una "Color Reference Card" durante tutta la fase 2 (scrittura codice).

---

**DIRETTIVE SUPREME (PRIME DIRECTIVES):**

1.  **FUNZIONALITÀ = INTOCCABILI:**
    - OGNI funzionalità interattiva del Master va PRESERVATA
    - Se l'utente ha scelto "Opzione A - Preserva" → usa Strategia B (merge conservativo)
    - Se l'utente ha scelto "Opzione B - Adotta v0/stitch" → usa Strategia A (puoi rimuovere)
    - Se NON c'era conflitto segnalato → preserva tutto

2.  **CONTENUTO = INTOCCABILE:**
    - OGNI elemento visibile specifico (logo, immagine custom, icona, badge) va PRESERVATO
    - Non sostituire MAI un elemento specifico con placeholder generico senza approvazione
    - Non rimuovere MAI elementi visibili (breadcrumb, banner, etc.) senza approvazione

3.  **DATA SOURCE = SACRO:**
    - Se Master carica dati da CMS/API/Database, il nuovo codice DEVE fare lo stesso
    - Non convertire MAI dati dinamici in dati hardcoded
    - Se Master usa Sanity/Contentful/API → usa la stessa fonte
    - Se aggiungi nuovi elementi visibili che richiedono dati → crea campo CMS/Schema

4.  **LOGICA = SACRA:**
    - Non rimuovere MAI: `id`, `ref`, `onClick`, `onChange`, `onSubmit`, `useEffect`, `useState`, `useMemo`, `useCallback`, `href`, `action`, chiamate API
    - Non refactorare la logica
    - Ogni handler, hook e data flow deve rimanere identico

5.  **DATI = DINAMICI SEMPRE:**
    - Se il codice originale esegue `.map()`, il nuovo codice DEVE eseguire lo stesso `.map()`
    - Non sostituire mai liste dinamiche con elementi statici
    - Usa v0/stitch come "template" per il singolo item, poi applica il loop

6.  **STILE = COPIA ESATTA v0/stitch (CRITICO):**
    - USA **ESCLUSIVAMENTE** I COLORI ESATTI dallo Style DNA di v0/stitch fornito in fase 1 (analisi)
    - **MAI MAI MAI** usare colori generici come: `bg-white`, `bg-black`, `text-black`, `text-gray-900`, `bg-gray-100`
    - Se v0/stitch usa `bg-slate-950` → USA `bg-slate-950` (non bg-black, non bg-gray-900)
    - Se v0/stitch usa `text-slate-300` → USA `text-slate-300` (non text-gray-300, non text-white)
    - COPIA ESATTAMENTE: classi Tailwind, spacing, typography, border-radius, shadows

7.  **LAYOUT = ZERO ERRORI:**
    - OGNI sezione deve avere padding minimo `px-4`
    - OGNI container deve avere max-width
    - NESSUN contenuto appiccicato ai bordi

8.  **CONTRASTO = WCAG AA:**
    - OGNI combinazione testo/sfondo >= 4.5:1
    - MAI: nero su grigio scuro, rosso su grigio scuro, bianco su bianco

**REGOLE TECNICHE CRITICHE (Next.js/React):**

### **REGOLA A: 'use client' Directive**
**Quando è OBBLIGATORIA:**
- Se il componente usa: `useState`, `useEffect`, `useRef`, event handlers (`onClick`, `onChange`, `onError`, etc.)
- Se il componente usa: browser APIs (`window`, `document`, `localStorage`, etc.)

**Errore CRITICO di serializzazione da evitare:**
Regola d'oro della serializzazione: Ogni volta che generi codice per un componente (Next.js), verifica se stai passando funzioni (event handlers), hook o state all'interno del TSX.
Analisi dei Props: Se il componente include attributi che iniziano con on (es. onClick, onChange, onError, onSubmit), deve essere obbligatoriamente un Client Component.
Verifica Direttiva: In presenza di tali attributi, verifica se c'è 'use client' in cima al file.
Logica di separazione: Non aggiungere 'use client' a pagine nativamente Server component; se il componente è complesso e prevalentemente server-side: estrai l'elemento interattivo in un piccolo file separato (es. InteractiveImage.tsx) marcato come client, mantenendo il resto come Server Component, ma quando possibile mantieni il componente completamente server component e cambia approccio per evitare elementi client.

**Se il file è già Server Component e vuoi mantenerlo tale:**
- NON aggiungere event handlers inline
- Usa pattern statici o sposta l'interattività in un Client Component separato

### **REGOLA B: Image Component (Next.js)**
**SEMPRE controllare cosa usa il Master:**
1. Analizza i file esistenti del Master
2. Se Master usa `import Image from 'next/image'` → USA `Image`
3. Se Master usa tag `<img>` → usa `<img>` (ma è raro in Next.js moderno)

**Pattern corretto Image Next.js:**
```tsx
import Image from 'next/image'

// ✅ CORRETTO
<Image 
  src="/path/to/image.jpg"
  alt="Description"
  width={1920}
  height={1080}
  className="..."
/>

// ❌ SBAGLIATO (solo se Master usa Image)
<img src="/path/to/image.jpg" alt="..." />
```

### **REGOLA C: Data Consistency (CMS/API)**
**SEMPRE mantenere la stessa fonte dati del Master:**

**Scenario 1 - Master usa CMS (Sanity/Contentful):**
```tsx
// ❌ SBAGLIATO - Hardcoding dopo che Master caricava da CMS
<Image src="/images/hero.jpg" alt="Hero" />

// ✅ CORRETTO - Mantieni caricamento da CMS + fallback
<Image 
  src={data.heroImage?.url || '/images/fallback-hero.jpg'} 
  alt={data.heroImage?.alt || 'Hero Image'}
/>
```

**Scenario 2 - Master usa API:**
```tsx
// ❌ SBAGLIATO - Sostituire fetch con dati statici
const team = [
  { name: 'John', role: 'CEO' }, // hardcoded
]

// ✅ CORRETTO - Mantieni fetch
const team = await fetchTeamMembers() // da API
```

**Se aggiungi nuovo campo visibile che Master non ha:**
- Devi estendere lo Schema CMS/Database
- Fornisci esempio di come aggiungere il campo
- Usa fallback statico solo temporaneamente

### **REGOLA D: Approvazione Modifiche Contenuto**
**Richiede decisione utente (già nel questionario fase 1 (analisi)):**
- Rimuovere elemento visibile (logo, badge, breadcrumb)
- Sostituire elemento specifico con elemento generico
- Cambiare aspect ratio o dimensioni drasticamente
- Convertire dati dinamici in hardcoded

**Se utente NON ha dato approvazione esplicita → NON modificare**

---

**PROCEDURA OPERATIVA OBBLIGATORIA:**

### **PASSO 0: COLOR REFERENCE CARD (OBBLIGATORIO - FARE SUBITO)**

**PRIMA di scrivere qualsiasi codice, crea questa reference card che consulterai COSTANTEMENTE:**

```
═══════════════════════════════════════════════════════════
🎨 COLOR REFERENCE CARD v0/stitch - CONSULTARE PER OGNI FILE
═══════════════════════════════════════════════════════════
Questa è la UNICA fonte di verità per i colori.
VIETATO usare colori non in questa lista.

BACKGROUND COLORS (da Style DNA v0/stitch):
┌─────────────────────────────────────────────────────────┐
│ Background principale: [INSERISCI DA fase 1 (analisi)]           │
│ Background secondary: [INSERISCI DA fase 1 (analisi)]            │
│ Background cards: [INSERISCI DA fase 1 (analisi)]                │
│ Background input: [INSERISCI DA fase 1 (analisi)]                │
└─────────────────────────────────────────────────────────┘

TEXT COLORS (da Style DNA v0/stitch):
┌─────────────────────────────────────────────────────────┐
│ Testo principale: [INSERISCI DA fase 1 (analisi)]                │
│ Testo headings: [INSERISCI DA fase 1 (analisi)]                  │
│ Testo muted/secondary: [INSERISCI DA fase 1 (analisi)]           │
└─────────────────────────────────────────────────────────┘

ACCENT/PRIMARY COLORS (da Style DNA v0/stitch):
┌─────────────────────────────────────────────────────────┐
│ Primary: [INSERISCI DA fase 1 (analisi)]                         │
│ Primary hover: [INSERISCI DA fase 1 (analisi)]                   │
│ Secondary: [INSERISCI DA fase 1 (analisi)]                       │
└─────────────────────────────────────────────────────────┘

BORDERS (da Style DNA v0/stitch):
┌─────────────────────────────────────────────────────────┐
│ Border color: [INSERISCI DA fase 1 (analisi)]                    │
│ Border radius: [INSERISCI DA fase 1 (analisi)]                   │
└─────────────────────────────────────────────────────────┘

⚠️ COLORI VIETATI (NON usare MAI):
❌ bg-white, bg-black, bg-gray-*
❌ text-black, text-white (a meno che non sia ESATTAMENTE in v0/stitch)
❌ text-gray-*, bg-neutral-*
❌ Qualsiasi colore NON presente in questa card

✅ SE HAI DUBBI: Consulta questa card PRIMA di scrivere classi colore
═══════════════════════════════════════════════════════════
```

**IMPORTANTE:** Compila questa card SUBITO con i valori ESATTI dallo Style DNA v0/stitch della fase 1 (analisi), poi consultala PRIMA di scrivere ogni file.

---

### **PASSO 1: Setup Fondamenta**

**1.1 - tailwind.config.ts:**
```typescript
// Applica configurazione ESATTA da Style DNA v0/stitch
// USA I COLORI ESATTI dalla Color Reference Card
```

**1.2 - globals.css:**
```css
// Inserisci variabili CSS ESATTE (HSL) da Style DNA v0/stitch
// Verifica che corrispondano alla Color Reference Card
```

**1.3 - layout.tsx:**
```tsx
// Aggiorna font import per matchare v0/stitch
// CONTROLLA: problemi di margin/padding globali?
```

**1.4 - Schema/Types (se necessario):**
Se hai aggiunto nuovi campi visibili, genera:
- Schema Sanity/Contentful
- TypeScript interfaces
- Esempio di come popolare i dati

---

### **PASSO 2: Analisi Pattern Master (OBBLIGATORIO)**

**PRIMA di scrivere codice, analizza i pattern del Master:**

**A) Pattern Componenti:**
```
Controllo componenti Master:
✓ Usa 'use client' per interattività? [SÌ/NO/A volte]
✓ Usa Image da next/image? [SÌ/NO]
✓ Pattern import comuni: [lista]
```

**B) Pattern Data Fetching:**
```
Controllo data fetching Master:
✓ CMS usato: [Sanity/Contentful/Altro/Nessuno]
✓ API endpoints: [lista o "Nessuno"]
✓ Pattern per immagini: [CMS/Static/API]
```

**C) Pattern Error Handling:**
```
Controllo error handling Master:
✓ Usa try-catch? [SÌ/NO]
✓ Usa error boundaries? [SÌ/NO]
✓ Fallback per immagini: [Pattern usato]
```

**Output:** "Ho analizzato il Master e replicherò questi pattern: [lista]"

---

### **PASSO 3: Processo File dalla Checklist**

**Per OGNI file nella checklist fase 1 (analisi):**

#### **3.1 - Identifica Strategia**

Basandoti su:
- Corrispondenza v0/stitch
- Risposte utente ai conflitti
- Rischio stili globali

**STRATEGIA A** - Restyling Completo
- Corrispondenza completa + nessun conflitto
- Utente ha scelto "Opzione B - Adotta v0/stitch"

**STRATEGIA B** - Merge Conservativo  
- Conflitto funzionalità + utente ha scelto "Opzione A - Preserva"
- Funzionalità complessa da preservare

**STRATEGIA C** - Wrapper Stilistico
- File orfano (NO corrispondenza v0/stitch)
- Rischio stili globali ALTO/MEDIO

#### **3.2 - Controlli Pre-Modifica (OBBLIGATORI - 6 CONTROLLI)**

**CONTROLLO 1 - Funzionalità:**
```
File: [nome]
Funzionalità da preservare: [lista o "Nessuna"]
Strategia: [A/B/C]
Rischio perdita funzionalità: [NESSUNO/BASSO/ALTO]
✓ CONFERMO: Sto preservando tutte le funzionalità approvate
```

**CONTROLLO 2 - Contenuto:**
```
File: [nome]
Elementi visibili specifici Master: [logo, immagini, icone, badge]
Elementi v0/stitch: [lista]
Modifiche pianificate: [cosa cambia]
Approvazione utente: [SÌ per conflitto #N / NON necessaria / NON OTTENUTA]
✓ CONFERMO: Non sto rimuovendo contenuto senza approvazione
```

**CONTROLLO 3 - Data Source:**
```
File: [nome]
Master carica dati da: [CMS/API/Props/Hardcoded]
Piano nuovo codice: [come gestirò i dati]
✓ CONFERMO: Mantengo stessa fonte dati (no conversione dinamico→statico)
```

**CONTROLLO 4 - Pattern Tecnici:**
```
File: [nome]
Ha interattività? [SÌ/NO]
Serve 'use client'? [SÌ/NO]
Immagini con Image o img? [Image/img secondo pattern Master]
✓ CONFERMO: Rispetto pattern tecnici del Master
```

**CONTROLLO 5 - Colori v0/stitch (NUOVE REGOLE STRINGENTI):**
```
File: [nome]

CONSULTAZIONE COLOR REFERENCE CARD:
Background che userò: [COPIA ESATTA dalla Card - es. "bg-slate-950"]
Testo headings che userò: [COPIA ESATTA dalla Card - es. "text-white"]
Testo body che userò: [COPIA ESATTA dalla Card - es. "text-slate-300"]
Accent/Primary che userò: [COPIA ESATTA dalla Card - es. "bg-blue-600"]
Borders che userò: [COPIA ESATTA dalla Card - es. "border-slate-700"]

VERIFICA ANTI-ERRORE:
❌ Sto usando bg-white? [SÌ/NO - se SÌ FERMATI e usa colore da Card]
❌ Sto usando bg-black? [SÌ/NO - se SÌ FERMATI e usa colore da Card]
❌ Sto usando text-black? [SÌ/NO - se SÌ FERMATI e usa colore da Card]
❌ Sto usando text-gray-*? [SÌ/NO - se SÌ FERMATI e usa colore da Card]

✓ CONFERMO: Sto usando SOLO colori dalla Color Reference Card
```

**CONTROLLO 6 - Layout:**
```
File: [nome]
Padding: [classi - min px-4]
Container: [max-width]
Contrasto: [OTTIMO/BUONO/SUFFICIENTE]
✓ CONFERMO: Nessun contenuto appiccicato ai bordi
```

**Se UNO dei controlli fallisce → FERMATI e rivedi**

#### **3.3 - Scrivi Codice con Header Obbligatorio**

```tsx
/**
 * ═══════════════════════════════════════════════════════
 * RESTYLING v0/stitch - [NOME COMPONENTE]
 * ═══════════════════════════════════════════════════════
 * Strategia: [A/B/C] - [descrizione]
 * 
 * COLORI v0/stitch USATI (da Color Reference Card):
 * - Background: [classe esatta]
 * - Testo headings: [classe esatta]
 * - Testo body: [classe esatta]
 * - Primary: [classe esatta]
 * - Borders: [classe esatta]
 * 
 * LAYOUT v0/stitch:
 * - Container: [max-width]
 * - Padding: [py-* px-*]
 * - Grid/Flex: [struttura]
 * 
 * PRESERVATO DA MASTER:
 * - Funzionalità: [lista o "Nessuna interattività"]
 * - Data source: [CMS/API/Props]
 * - Pattern tecnici: [Image, 'use client', etc.]
 * 
 * CONTROLLI PRE-MODIFICA: ✓✓✓✓✓✓ (6/6)
 * ═══════════════════════════════════════════════════════
 */
```

#### **3.4 - Post-Scrittura: Verifica Colori (NUOVO - OBBLIGATORIO)**

**DOPO aver scritto il codice del file, fai questa verifica:**

```
POST-SCRITTURA VERIFICA COLORI - File: [nome]

Scansiono il codice che ho scritto per verificare i colori...

BACKGROUND trovati nel codice:
- [lista tutte le classi bg-* usate]
✓ Verifico che siano tutte nella Color Reference Card: [SÌ/NO]

TEXT trovati nel codice:
- [lista tutte le classi text-* usate]
✓ Verifico che siano tutte nella Color Reference Card: [SÌ/NO]

COLORI VIETATI trovati:
- bg-white: [Trovato/Non trovato]
- bg-black: [Trovato/Non trovato]
- text-black: [Trovato/Non trovato]
- text-gray-*: [Trovato/Non trovato]

SE ho trovato colori vietati → RISCRIVERE il file usando Color Reference Card
SE tutti i colori sono dalla Card → OK, procedo al prossimo file
```

---

### **STRATEGIA A: Restyling Completo - DETTAGLIATO**

**Quando:** Corrispondenza completa, nessun conflitto, ~80% dei casi

**Esempio Completo:**

```tsx
/**
 * ═══════════════════════════════════════════════════════
 * RESTYLING v0/stitch - Hero Section
 * ═══════════════════════════════════════════════════════
 * Strategia: A - Restyling Completo
 * 
 * COLORI v0/stitch USATI (da Color Reference Card):
 * - Background: bg-slate-950
 * - Testo headings: text-white
 * - Testo body: text-slate-300
 * - Cards: bg-slate-900
 * - Borders: border-slate-800
 * 
 * LAYOUT v0/stitch:
 * - Container: max-w-7xl mx-auto
 * - Padding: py-20 px-6
 * - Grid: grid gap-12
 * 
 * PRESERVATO DA MASTER:
 * - Funzionalità: useState per selected item, onClick handlers
 * - Data source: Props da parent component
 * - Pattern tecnici: 'use client' per interattività
 * 
 * CONTROLLI PRE-MODIFICA: ✓✓✓✓✓✓ (6/6)
 * ═══════════════════════════════════════════════════════
 */

'use client' // ✓ CONTROLLO 4: Serve per useState e onClick

import { useState } from 'react'

interface Props {
  title: string
  items: Array<{ id: string; name: string; description: string }>
}

export default function Hero({ title, items }: Props) {
  const [selected, setSelected] = useState<string | null>(null)
  
  // ✓ CONTROLLO 5: Tutti i colori da Color Reference Card
  return (
    <section className="bg-slate-950 py-20 px-6"> {/* bg-slate-950 da Card */}
      <div className="max-w-7xl mx-auto grid gap-12">
        
        <h1 className="text-5xl font-bold text-white"> {/* text-white da Card */}
          {title}
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {items.map(item => (
            <button
              key={item.id}
              onClick={() => setSelected(item.id)}
              className="bg-slate-900 p-6 rounded-xl hover:bg-slate-800 transition-colors text-left border border-slate-800" {/* Tutti da Card */}
            >
              <h3 className="text-xl font-semibold text-white mb-2">
                {item.name}
              </h3>
              <p className="text-slate-300 leading-relaxed"> {/* text-slate-300 da Card */}
                {item.description}
              </p>
            </button>
          ))}
        </div>
        
        {selected && (
          <div className="mt-8 p-6 bg-slate-800 rounded-lg border border-slate-700"> {/* Colori da Card */}
            <p className="text-white">Selected item: {selected}</p>
          </div>
        )}
      </div>
    </section>
  )
}
```

**Post-Scrittura Verifica:**
```
✓ Background: bg-slate-950, bg-slate-900, bg-slate-800 - TUTTI dalla Card
✓ Text: text-white, text-slate-300 - TUTTI dalla Card
✓ Borders: border-slate-800, border-slate-700 - TUTTI dalla Card
✓ Nessun colore vietato trovato
→ File OK, procedo
```

**Checklist Strategia A:**
- [ ] Header obbligatorio presente?
- [ ] 'use client' se necessario?
- [ ] Struttura HTML da v0/stitch?
- [ ] Colori dalla Color Reference Card VERIFICATI?
- [ ] Loop/map preservati?
- [ ] Handler preservati?
- [ ] Hook preservati?
- [ ] Data source preservata?
- [ ] Padding min px-4?
- [ ] Container max-width?

---

### **STRATEGIA B: Merge Conservativo - DETTAGLIATO**

**Quando:** Utente ha scelto "Opzione A - Preserva Funzionalità", ~10% dei casi

**Esempio Completo - Carousel:**

```tsx
/**
 * ═══════════════════════════════════════════════════════
 * RESTYLING v0/stitch - Image Carousel
 * ═══════════════════════════════════════════════════════
 * Strategia: B - Merge Conservativo
 * 
 * COLORI v0/stitch USATI (da Color Reference Card):
 * - Background: bg-slate-950
 * - Testo: text-white
 * - Buttons: bg-white/10, hover:bg-white/20
 * - Borders: rounded-xl
 * 
 * PRESERVATO DA MASTER:
 * - Funzionalità: Carousel autoplay, swipe gestures, navigation
 * - Data source: Props array di immagini
 * - Pattern tecnici: 'use client', useEffect, useRef
 * 
 * DECISIONE UTENTE: Conflitto #2 - Opzione A (Preserva carousel)
 * 
 * CONTROLLI PRE-MODIFICA: ✓✓✓✓✓✓ (6/6)
 * ═══════════════════════════════════════════════════════
 */

'use client'

import { useState, useRef, useEffect } from 'react'
import Image from 'next/image'

interface CarouselImage {
  url: string
  alt: string
  width: number
  height: number
}

interface Props {
  images: CarouselImage[]
}

export default function ImageCarousel({ images }: Props) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isAutoplay, setIsAutoplay] = useState(true)
  const containerRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    if (!isAutoplay) return
    const interval = setInterval(() => {
      setCurrentIndex(i => (i + 1) % images.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [isAutoplay, images.length])
  
  // ✓ CONTROLLO 5: Colori da Color Reference Card
  return (
    <div className="relative w-full bg-slate-950 rounded-xl overflow-hidden"> {/* bg-slate-950 da Card */}
      <div 
        ref={containerRef}
        className="flex transition-transform duration-300"
        style={{ transform: `translateX(-${currentIndex * 100}%)` }}
      >
        {images.map((img, i) => (
          <div key={i} className="min-w-full flex-shrink-0">
            <Image 
              src={img.url}
              alt={img.alt}
              width={img.width}
              height={img.height}
              className="w-full h-auto object-cover"
              priority={i === 0}
            />
          </div>
        ))}
      </div>
      
      <button
        onClick={() => setCurrentIndex(i => (i - 1 + images.length) % images.length)}
        className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/10 hover:bg-white/20 text-white p-3 rounded-full backdrop-blur-sm transition-colors" {/* Colori da Card */}
        aria-label="Previous image"
      >
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      
      <button
        onClick={() => setCurrentIndex(i => (i + 1) % images.length)}
        className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/10 hover:bg-white/20 text-white p-3 rounded-full backdrop-blur-sm transition-colors"
        aria-label="Next image"
      >
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
      
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
        {images.map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrentIndex(i)}
            className={`w-2 h-2 rounded-full transition-all ${
              i === currentIndex 
                ? 'bg-white w-8'  {/* text-white da Card */}
                : 'bg-white/50 hover:bg-white/70'
            }`}
            aria-label={`Go to image ${i + 1}`}
          />
        ))}
      </div>
    </div>
  )
}
```

**Checklist Strategia B:**
- [ ] Header con decisione utente citata?
- [ ] Struttura HTML identica a Master?
- [ ] SOLO classi CSS modificate?
- [ ] Colori dalla Color Reference Card VERIFICATI?
- [ ] Tutti handler intatti?
- [ ] Tutti ref intatti?
- [ ] Tutti hook intatti?
- [ ] Image vs img corretto secondo Master?
- [ ] 'use client' se necessario?

---

### **STRATEGIA C: Wrapper Stilistico - DETTAGLIATO**

**Quando:** File orfano, rischio stili globali ALTO/MEDIO, ~10% dei casi

**Esempio Completo - Sezione Orfana con Form:**

```tsx
/**
 * ═══════════════════════════════════════════════════════
 * RESTYLING v0/stitch - Call To Action (Sezione Orfana)
 * ═══════════════════════════════════════════════════════
 * Strategia: C - Wrapper Stilistico
 * 
 * COLORI v0/stitch USATI (da Color Reference Card):
 * - Background: bg-slate-900
 * - Testo headings: text-white
 * - Testo body: text-slate-300
 * - Input: bg-slate-800, border-slate-700
 * - Primary button: bg-blue-600, hover:bg-blue-700
 * 
 * PRESERVATO DA MASTER:
 * - Funzionalità: Form submit con validation, API call
 * - Data source: Form state locale
 * - Pattern tecnici: 'use client' per form handling
 * 
 * RISCHIO PRE-FIX: ALTO - Sezione non in v0/stitch, diventava invisibile
 * 
 * CONTROLLI PRE-MODIFICA: ✓✓✓✓✓✓ (6/6)
 * ═══════════════════════════════════════════════════════
 */

'use client'

import { useState } from 'react'

export default function CallToAction() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      const response = await fetch('/api/newsletter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      
      if (!response.ok) throw new Error('Subscription failed')
      
      setSuccess(true)
      setEmail('')
    } catch (err) {
      setError('Failed to subscribe. Please try again.')
    } finally {
      setLoading(false)
    }
  }
  
  // ✓ CONTROLLO 5: Tutti i colori da Color Reference Card
  return (
    <section className="bg-slate-900 py-16 px-6"> {/* bg-slate-900 da Card */}
      <div className="max-w-4xl mx-auto text-center">
        
        <h2 className="text-3xl font-bold text-white mb-4"> {/* text-white da Card */}
          Ready to Get Started?
        </h2>
        
        <p className="text-slate-300 text-lg mb-8 leading-relaxed"> {/* text-slate-300 da Card */}
          Join thousands of satisfied customers and transform your business today.
        </p>
        
        {!success ? (
          <form onSubmit={handleSubmit} className="max-w-md mx-auto">
            <div className="flex flex-col sm:flex-row gap-4">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
                className="flex-1 px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" {/* Tutti da Card */}
              />
              <button
                type="submit"
                disabled={loading}
                className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white font-semibold rounded-lg transition-colors disabled:cursor-not-allowed" {/* bg-blue-600 da Card */}
              >
                {loading ? 'Subscribing...' : 'Sign Up'}
              </button>
            </div>
            
            {error && (
              <p className="mt-4 text-red-400 text-sm"> {/* Errore usa red-400 per contrasto */}
                {error}
              </p>
            )}
          </form>
        ) : (
          <div className="max-w-md mx-auto p-6 bg-slate-800 border border-slate-700 rounded-lg"> {/* Colori da Card */}
            <p className="text-green-400 font-semibold"> {/* Success usa green-400 per contrasto */}
              ✓ Successfully subscribed! Check your email.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
```

**Checklist Strategia C:**
- [ ] Header con rischio pre-fix indicato?
- [ ] Layout Master preservato?
- [ ] Wrapper con colori dalla Card?
- [ ] Container max-width presente?
- [ ] Padding min px-4?
- [ ] Contrasto >= 4.5:1 su tutti i testi?
- [ ] Form logic preservato?
- [ ] 'use client' se necessario?

---

### **PASSO 4: Quality Control PRE-Generazione**

**Completa questa checklist PRIMA di generare XML:**

```
═══════════════════════════════════════════
QUALITY CONTROL PRE-GENERAZIONE
═══════════════════════════════════════════

[A] COMPLETEZZA FILE:
    Totale file checklist fase 1 (analisi): [numero]
    File processati: [numero]
    ✓ CONFERMO: Ho processato OGNI file dalla checklist

[B] FUNZIONALITÀ:
    Conflitti funzionalità fase 1 (analisi): [numero]
    Risolti secondo scelta utente: [numero]
    ✓ CONFERMO: Zero rimozioni funzionalità non approvate

[C] CONTENUTO:
    Conflitti contenuto fase 1 (analisi): [numero]
    Risolti secondo scelta utente: [numero]
    ✓ CONFERMO: Zero sostituzioni contenuto non approvate

[D] DATA SOURCE:
    File con data CMS/API Master: [numero]
    Mantenuto source originale: [numero]
    Conversioni dinamico→statico: [numero o "ZERO"]
    ✓ CONFERMO: Zero conversioni non approvate

[E] PATTERN TECNICI:
    File con 'use client' necessario: [numero]
    File con 'use client' aggiunto: [numero]
    File con Image component: [numero]
    ✓ CONFERMO: Pattern Master replicati correttamente

[F] COLORI v0/stitch (CRITICO - NUOVO):
    File processati: [numero]
    File con verifica post-scrittura OK: [numero]
    
    COLORI VIETATI TROVATI:
    - bg-white: [Trovato in N file / Mai trovato]
    - bg-black: [Trovato in N file / Mai trovato]
    - text-black: [Trovato in N file / Mai trovato]
    - bg-gray-*/text-gray-*: [Trovato in N file / Mai trovato]
    
    COLORI DALLA COLOR REFERENCE CARD:
    - [Lista tutti i colori usati]
    
    ✓ CONFERMO: SOLO colori dalla Color Reference Card
    ✓ CONFERMO: ZERO colori vietati trovati
    
    ⚠️ SE ho trovato colori vietati → STOP E RIVEDO TUTTI I FILE

[G] LAYOUT:
    File con rischio contenuto appiccicato: [numero]
    File corretti con padding: [numero]
    ✓ CONFERMO: Zero contenuti appiccicati

[H] CONTRASTO:
    Combinazioni verificate: [stima]
    Combinazioni < 4.5:1: [numero o "ZERO"]
    ✓ CONFERMO: Tutti i contrasti sufficienti

═══════════════════════════════════════════
SE TUTTI ✓ → PROCEDO CON GENERAZIONE XML
SE ANCHE UNO ✗ → RIVEDO IL CODICE
SE ho trovato colori vietati → RISCRIVERE FILE con Color Card
═══════════════════════════════════════════
```

---

### **PASSO 5: Generazione XML**

**REGOLE DI FORMATTAZIONE XML (CRITICHE):**
1.  **STRUTTURA:** Tag radice `<changes>`.
2.  **WRAPPER:** Blocco Markdown unico con **4 backticks** (````xml).
3.  **CONTENUTO FILE:** Usa `<![CDATA[ ... ]]>`.
4.  **CODICE INTERNO:** Blocchi Markdown a **3 backticks** con linguaggio (es. ```tsx).
5.  **INDENTAZIONE:** Codice pulito, non minificato.
6.  **SINTASSI:** Attenzione agli apostrofi (`&apos;`).

**Esempio Esatto di Output XML:**

````xml
<changes>
  <!-- CONFIGURAZIONE -->
  <file path="tailwind.config.ts"><![CDATA[
```typescript
// Valori ESATTI da Style DNA v0/stitch e Color Reference Card
```
  ]]></file>

  <file path="src/app/globals.css"><![CDATA[
```css
/* Variabili HSL ESATTE da Style DNA v0/stitch */
```
  ]]></file>

  <!-- SCHEMA/TYPES (se necessario) -->
  <file path="sanity/schemas/heroSection.ts"><![CDATA[
```typescript
// Se hai aggiunto nuovi campi visibili
export default {
  name: 'heroSection',
  type: 'document',
  fields: [
    {
      name: 'heroImage',
      type: 'image',
      options: { hotspot: true }
    },
    // ...
  ]
}
```
  ]]></file>

  <!-- COMPONENTI -->
  <file path="[path]"><![CDATA[
```tsx
/**
 * ═══════════════════════════════════════════════════════
 * RESTYLING v0/stitch - [NOME]
 * ═══════════════════════════════════════════════════════
 * [Header completo obbligatorio con COLORI ESATTI dalla Card]
 */

[CODICE COMPLETO CON TUTTI I CONTROLLI RISPETTATI E COLORI DALLA CARD]
```
  ]]></file>
  
  <!-- Ripeti per OGNI file -->
</changes>
````

**REGOLE CODING OBBLIGATORIE:**
1. Header dettagliato in ogni file con COLORI ESATTI dichiarati
2. 'use client' dove necessario
3. Image vs img secondo pattern Master
4. Data source preservato
5. OGNI file dalla checklist incluso
6. Codice completo (no placeholder)
7. **SOLO colori dalla Color Reference Card**
8. Se aggiunto nuovo campo in uno schemaType di Sanity, includere un initialValue

---

### **SEZIONE FINALE (FUORI XML):**

**🛠️ AZIONI MANUALI CRITICHE**
Elenca comandi pnpm e qualsiasi altra azione manuale inevitabile (se necessari):

**1. Installazione Dipendenze:**
```bash
pnpm add [LISTA COMPLETA PACCHETTI]
```

**2. Setup CMS (se hai aggiunto campi):**
```bash
# Se usi Sanity
cd sanity && sanity deploy

# Istruzioni per popolare nuovi campi:
[Lista campi aggiunti e come popolarli]
```

**3. Verifica Visiva OBBLIGATORIA:**
- [ ] Aspetto corrisponde a v0/stitch (COLORI INCLUSI)
- [ ] Schema colori ESATTO di v0/stitch (NO bianco/nero)
- [ ] Nessun contenuto appiccicato
- [ ] Tutte le funzionalità funzionano
- [ ] Nessun errore console
- [ ] Contrasti leggibili
- [ ] Immagini caricano correttamente

**4. Report Modifiche:**
```
FILE MODIFICATI: [numero]
├─ Strategia A (Restyling Completo): [numero]
├─ Strategia B (Merge Conservativo): [numero]
└─ Strategia C (Wrapper Orfani): [numero]

DECISIONI UTENTE APPLICATE: [numero]
├─ Funzionalità preservate: [lista]
├─ Funzionalità rimosse (con approvazione): [lista o "NESSUNA"]
└─ Contenuto modificato (con approvazione): [lista o "NESSUNO"]

CAMPI CMS/SCHEMA AGGIUNTI: [numero]
└─ [Lista campi con file schema]

COLORI v0/stitch APPLICATI:
Background: [lista colori esatti usati]
Text: [lista colori esatti usati]
Primary/Accent: [lista colori esatti usati]
Borders: [lista colori esatti usati]
✓ Confermo: ZERO colori generici (white/black/gray-*) usati
```

---

**GENERA ORA IL CODICE COMPLETO.**

**REMINDER FINALE (11 PUNTI):**
1. ✓ Creato Color Reference Card SUBITO?
2. ✓ Consultato la Card PRIMA di ogni file?
3. ✓ Processato OGNI file dalla checklist?
4. ✓ Preservato OGNI funzionalità (o ho approvazione)?
5. ✓ Preservato OGNI contenuto specifico (o ho approvazione)?
6. ✓ Mantenuto stessa data source (CMS/API)?
7. ✓ 'use client' dove serve?
8. ✓ Image/img secondo pattern Master?
9. ✓ SOLO colori da Color Reference Card (NO bg-white/bg-black)?
10. ✓ Padding min px-4 ovunque?
11. ✓ Verifica post-scrittura colori per ogni file?

**SE 11/11 ✓ → GENERO XML**
**SE ho usato bg-white, bg-black, text-black, text-gray-* → STOP E RIVEDO**