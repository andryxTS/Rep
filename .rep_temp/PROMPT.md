**Contesto:**
Ho una app e voglio apportare alcune modifiche.

**Input:**
In allegato a questo messaggio trovi due file:
1. `repomix-output.txt`: L'intero codebase del progetto.
2. Questo file `PROMPT.md` con le istruzioni.

**Task:**
Ti chiederò di effettuare alcune modifiche al mio codebase. Per adesso farai un'analisi e aspetterei il mio feedback. In una seconda fase futura procederai con il coding.

**PROCEDURA**
* Analizza il codebase, capendo: architettura, approccio, stile, flusso dei dati.
* Poni attenzione sulle dipendenze, sulle librerie utilizzate e sui modi in cui vengono prelevati e renderizzati i dati.
* Leggi le modifiche che ti propongo, pensa ad un piano su come applicarle; ci saranno probabilmente da prendere delle decisioni: voglio essere coinvolto in queste decisioni.
* Chiedimi il feedback riguardo alle scelte da fare presentandomele come elenco numerato con più opzioni (es. A, B, C...). TUTTAVIA: se una delle opzioni è chiaramente una best-practice o la scelta raccomandata/consigliata, decidi in autonomia per quell'opzione. Se tutti i bivi decisionali rientrano in questo caso, non chiedermi nulla e invitami semplicemente a fornirti le istruzioni per la parte esecutiva.
* Aspetta il mio feedback (se necessario) e le nuove istruzioni operative su come proseguire con il lavoro di coding vero e proprio.


**BEST PRACTICE**
* Best-practice: il lavoro dovrà essere eseguito secondo le best-practice per il framework in questione (ad esempio uso Image invece che img, valori di fallback, separazione logica/layout, ecc.).
* Practice del mio repo: Eccezione alla regola precedente: adattati all'approccio che vedi utilizzato nel mio repo (se ad esempio il mio repo utilizza qualcosa che non è esattamente tra le best-practice, adattati comunque all'approccio del mio repo, previa approvazione mia, ricordati di richiedermi il feedback).
* Dati dinamici: Se trovi collegamenti a CMS (es. Sanity), mantieni l'approccio, evita contenuti hardcoded (eccetto fallback).
* initialValue: se aggiungi campi a Sanity, includi sempre un initialValue.
* Installazione pacchetti Node.js: di default usa `pnpm`, NON usare `npm`. Usa npm solo se dall'analisi del mio codice ti accorgi che inequivocabilmente usato npm per quell'app.
* Se vedi che ci sono database collegati ricordati di includermi i comandi per rendere funzionanti le nuove modifiche (es: generate e migrate).
* Segui le altre best-practice incluse di seguito, servono a scongiurare e prevenire errori e perdite di tempo. Fai questi controlli in sordina, avvisami e proponimi soluzioni solo se noti delle evidenti criticità:

**SYSTEM PROMPT - BEST PRACTICES**
*(Le seguenti regole sono estratte dal file `prompts/best_practice.md`. Se durante il lavoro affronti e risolvi un problema molto comune o insidioso che andrebbe prevenuto globalmente in futuro, potrai proporre una regola aggiuntiva a questo file usando il tag `<best_practice_append>` in fase di esecuzione XML).*
### ☁️ Regole specifiche per OpenNext Cloudflare
*   **No Runtime Edge:** Non scrivere *mai* `export const runtime = 'edge'` nei file (es. Route Handlers o Pagine). OpenNext pacchettizza già tutto per i Workers; dichiararlo esplicitamente fa fallire il bundler di `@opennextjs/cloudflare`.
*   **Tipizzazione Bindings:** Per usare i binding di Cloudflare (D1, KV, R2) estratti da `getCloudflareContext().env`, devi sempre dichiararli in un file globale (es. `src/cloudflare-env.d.ts`) estendendo l'interfaccia: `declare global { interface CloudflareEnv { NOME_BINDING: D1Database } }`.
  
### 🗄️ Database & Drizzle ORM (SQLite / D1)
*   **Limiti ALTER TABLE SQLite:** Quando aggiungi una **nuova colonna** a una tabella *già esistente* in SQLite/D1, **NON USARE MAI** un valore di default dinamico come `.default(sql`(CURRENT_TIMESTAMP)`)`. SQLite non lo supporta tramite `ALTER TABLE ADD COLUMN` e la migrazione fallirà. Gestisci l'aggiornamento del timestamp programmaticamente dal codice TypeScript.

### 🛡️ TypeScript & Gestione Dati
*   **Risposte JSON (Strict Mode):** Quando usi `await res.json()`, il tipo inferito è spesso `unknown`. Effettua sempre un cast esplicito (es. `(await res.json()) as any` oppure con un'interfaccia dedicata) per evitare l'errore `Object is of type unknown`.
*   **Fallback Obbligatori (Strict Null Checks):** Quando passi dati tra funzioni o API esterne, usa *sempre* fallback sicuri (es. `const data = res.data || "";`) o l'optional chaining (`obj?.property`) per proteggere il codice da valori `null` o `undefined` imprevisti.

### 🔐 Clerk (Autenticazione)
*   **Middleware Options:** Nelle versioni recenti di Clerk per Next.js App Router, non passare opzioni di routing come `{ afterSignOutUrl: "/" }` all'interno di `clerkMiddleware()`. Fallisce il type-checking ("No overload matches this call"). Usa invece le variabili d'ambiente nel file `.env` (es. `NEXT_PUBLIC_CLERK_AFTER_SIGN_OUT_URL=/`).

### 🛠️ Misure Correttive e Troubleshooting pre-build
**L'AI deve segnalare e proporre una correzione immediata se nota che:**
*   C'è una cartella come `scripts/` o `tests/` nel progetto ma **non è stata esclusa** nell'array `"exclude"` del `tsconfig.json` (causa fallimento della build per type-checking troppo espansivo).
*   In `next.config.ts` manca l'impostazione `eslint: { ignoreDuringBuilds: true }` (i warning di stile come `any` o variabili non usate bloccano il deploy di Next.js).
* **Controllo .gitignore:** Verifica sempre che il `.gitignore` non stia escludendo file vitali per il progetto. Le cartelle `/drizzle` (migrazioni SQL), `/public` (asset statici) e l'estensione `*.md` (documentazione e file di sistema come questo) **DEVONO** essere tracciate su Git. Se noti queste esclusioni, avvisa immediatamente l'utente e proponi la correzione. Escludi solo file temporanei specifici dell'AI (es. `PROMPT.md`, `repomix-output.txt`).

**MODIFICHE RICHIESTE:**
Modifica alla parte dello script che individua snippet patch non riusciti e crea il prompt per l'llm.
Dev'essere modificata così: non bisogna invitare l'LLM ad essere più preciso o a non usare gli snippets, ma bisogna, dopo aver elencato i file le cui patch non hanno funzionato, dargli il contenuto di quei file, che probabilmente è cambiato e lui non lo sa.

Ora procedi come ti ho indicato, aspetto le tue domande prima di darti istruzioni specifiche su come effettuare il coding vero e proprio.