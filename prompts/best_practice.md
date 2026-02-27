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

### ☁️ Librerie Incompatibili in Cloudflare Workers
*   **Googleapis (gaxios):** La libreria ufficiale `googleapis` (e il client auth) va spesso in crash in ambiente Cloudflare/Edge a causa di un bug nel parsing degli header di `gaxios` ("Cannot read properties of null (reading 'has')"). Evita di usarla per semplici chiamate REST. Sostituisci l'integrazione generando il JWT manualmente tramite `node:crypto` ed esegui la chiamata usando l'API nativa `fetch()`.

### Cloudflare-env.d.ts Controllo
*  Se noti che per le esigenze del progetto (es: presenza database D1 e/o bucket R2), ci dovrebbe essere un file src/cloudflare-env.d.ts contenente quelle poche (ma essenziali) righe di codice a riguardo, e non vedi tra i file elencati questo file: la cosa più probabile è che sia stato escluso dal .repomixignore o in modo indiretto del .gitignore. In quel caso, quando poi sfornerai il codice, avvisami con un commento nella parte <shell> che deve controllare le seguenti cose:
*  Che esista effettivamente il file src/cloudflare-env.d.ts.
*  Che nei file .gitignore e .repomixignore sia escluso /cloudflare-env.d.ts (nella root, file enorme che si genera da solo con la build) ma che sia incluso src/cloudflare-env.d.ts, semplicemente mettendo in entrambi i file questa direttiva `/cloudflare-env.d.ts` cancellando l'eventuale direttiva `cloudflare-env.d.ts` che li escluderebbe entrambi.
*  Dopo il primo avviso fatto in questo modo (commento nella parte <shell> durante la fase di coding) non ricordarmi più di questa cosa, avrò già provveduto a sistemare.

### ☁️ Inizializzazione Client in Cloudflare Workers
* **No Top-Level Env:** Evita di inizializzare client di terze parti (Resend, AWS SDK, OpenAI) a livello globale nel file usando `process.env`. Nelle piattaforme serverless come Cloudflare, le variabili d'ambiente potrebbero non essere popolate al caricamento del modulo. Inizializza sempre i client all'interno della funzione (Server Action o Route Handler) recuperando i segreti tramite `getCloudflareContext().env`.

### 🛡️ Tipizzazione Variabili d'Ambiente (Cloudflare)
* **Sincronizzazione CloudflareEnv:** Ogni volta che aggiungi un segreto su Cloudflare (tramite `wrangler secret put`) o una variabile nel `wrangler.jsonc` che intendi leggere tramite `getCloudflareContext().env`, devi aggiornare obbligatoriamente l'interfaccia in `src/cloudflare-env.d.ts`. Senza questo passaggio, TypeScript bloccherà la build di Next.js segnalando che la proprietà non esiste sul tipo `CloudflareEnv`.

### 🛠️ Resilienza alle Dipendenze Esterne (Zero-Config Tolerance)
* **Build Resilience (Providers):** Quando integri SDK di terze parti (Auth, Analytics, CRM) tramite "Providers" nel `RootLayout`, verifica sempre l'esistenza della chiave (`NEXT_PUBLIC_...`) prima di renderizzare il componente. Se la chiave manca o è una stringa vuota, renderizza i `children` senza il provider per evitare crash durante la fase di build (Static Site Generation).
* **Middleware & Action Safety:** Nel `middleware.ts` o nelle Server Actions, esegui un controllo preventivo sulla presenza delle Secret Key prima di invocare metodi di protezione o API esterne. Questo garantisce che l'app rimanga avviabile e navigabile nelle sue rotte pubbliche (es. Landing Pages) anche se l'infrastruttura esterna non è ancora stata configurata.
* **Fallback Content:** Assicurati che le componenti UI che dipendono da dati esterni mostrino uno stato di fallback o un messaggio informativo invece di crashare l'intera pagina se il servizio non è inizializzato.

### ☁️ Cloudflare Runtime Context & Static Build
* **Dynamic Opt-out:** Se una pagina (Server Component) o una rotta API (GET) interagisce con il database D1, KV o R2 tramite `getCloudflareContext()`, Next.js fallirà la build tentando di pre-renderizzarla staticamente. Devi obbligatoriamente aggiungere `export const dynamic = "force-dynamic"` nel file della pagina o della rotta per forzare il rendering a runtime, dove il contesto di Cloudflare è disponibile.