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

### ☁️ Limiti `waitUntil()` in Cloudflare Workers per Task Lunghi
* **Niente `waitUntil` per AI/LLM:** Non delegare operazioni di lunga durata (come l'analisi nativa audio/video o chiamate LLM complesse) alla funzione `ctx.waitUntil()`. In Cloudflare Workers, i task in background vengono terminati rigidamente in breve tempo (circa 30 secondi) dopo che la risposta HTTP principale è stata inviata al client ("waitUntil tasks did not complete within the allowed time").
* **Soluzione Sincrona:** Per aggirare questo limite ed evitare la terminazione precoce del worker, esegui sempre i task lunghi in modo **sincrono** (usando `await`) *prima* di restituire l'oggetto `NextResponse`, oppure innescali tramite Server Actions (`"use server"`). Mantenendo la connessione HTTP aperta con il client, Cloudflare concede un massimale di tempo di esecuzione notevolmente superiore (spesso oltre 100 secondi), garantendo la corretta esecuzione del nodo AI.

### 🦜🔗 LangChain & Prompt Engineering
*   **Escaping Parentesi Graffe (JSON in Prompt):** Quando si definiscono template di prompt che includono variabili dinamiche (es. `{input}`), tutte le parentesi graffe *letterali* destinate all'LLM (come negli esempi JSON o blocchi di codice) DEVONO essere raddoppiate (`{{` e `}}`). Se si scrive `{ "key": "val" }`, LangChain cercherà una variabile chiamata `"key": "val"` e fallirà con errore `Single '}' in template`.
    *   *Esempio:* `Esempio di output: {{ "risultato": "ok" }}`.

### ☁️ Configurazione Wrangler per OpenNext (Workers vs Pages)
* **Conflitto `pages_build_output_dir`:** Quando si configura un progetto OpenNext per essere distribuito come Cloudflare Worker sfruttando la nuova direttiva `"assets": { "directory": ".open-next/assets", "binding": "ASSETS" }`, NON inserire mai la direttiva legacy `"pages_build_output_dir"`. La presenza di quest'ultima confonde la CLI, facendole credere che si tratti di un progetto Cloudflare Pages. Questo causerà il blocco immediato del comando `wrangler deploy` in CI/CD con l'errore: "It looks like you've run a Workers-specific command in a Pages project".

### Cursor:pointer, su tutti i link e bottoni
Ricordati di mettere il cursor pointer su ogni link e pulsante o qualsiasi elemento che cliccato svolge un'azione.

### Eliminazione file e cartelle in locale
Per l'eliminazione di file e cartelle, attieniti a queste due regole:
1. **Eliminazione sicura (Cestino):** Usa SEMPRE il tag `<delete_file path="path/to/file_or_folder" />` per eliminare file o cartelle standard. Lo script li sposterà in modo sicuro nel cestino di sistema.
2. **Eliminazione definitiva (Cartelle enormi):** NON usare il tag `<delete_file>` per cartelle gigantesche o profondamente inalberate come `node_modules` o `.next`. Spostarle nel cestino su Windows è troppo lento. Per queste specifiche cartelle usa il tag `<shell>` fornendo il comando per l'eliminazione definitiva: `rd /s /q "nome_cartella"`.

### ☁️ Gestione Variabili d'Ambiente Cloudflare (Type-Checking & Build)
* **Separazione `cloudflare-env.d.ts`:** Il file `/cloudflare-env.d.ts` generato automaticamente da Wrangler nella root del progetto **deve sempre rimanere ignorato** in `.gitignore` e `.repomixignore` (per evitare continui conflitti su Git). Tuttavia, poiché TypeScript (es. durante la build di Next.js) effettua il type-checking *prima* che Wrangler generi questo file, si verificheranno errori bloccanti su `process.env` o `getCloudflareContext().env`. 
* **Soluzione Obbligatoria:** Crea (o mantieni) un file separato **`src/cloudflare-env.d.ts`** che estrae solo le interfacce essenziali (`Cloudflare.Env` e l'estensione di `NodeJS.ProcessEnv`). Questo file in `src/` **deve essere tracciato su Git**, garantendo che la build passi con successo in qualsiasi ambiente CI/CD senza dipendere dalla pre-generazione di Wrangler.

### 🗄️ Database & Drizzle ORM (SQLite / D1)
*   **Eliminazione a cascata e vincoli (ON DELETE):** In Cloudflare D1, la propagazione del `ON DELETE CASCADE` impostata in Drizzle spesso fallisce a causa della natura stateless delle connessioni (il DB solleverà `D1_ERROR: FOREIGN KEY constraint failed`). Quando crei logiche di cancellazione (Server Actions), effettua **sempre l'eliminazione esplicita** dei record figli (es. `await db.delete(children).where(...)`) **prima** di eliminare il record padre.
 
### 💻 Terminale Integrato e Comandi Shell (Windows CMD)
* **Sintassi Comandi:** L'ambiente locale utilizza il terminale integrato di VS Code su Windows basato sul **Prompt dei comandi classico (cmd.exe)**. Per le operazioni fornite nel tag `<shell>`, **NON** usare cmdlet di PowerShell (es. `Rename-Item`, `Remove-Item`) e **NON** usare comandi Unix (`cp`, `rm`, `mv`). Usa sempre i comandi DOS standard come `ren` (per rinominare), `copy`, `del`, `mkdir` o `rd /s /q`.

### 🔄 Operazioni Sequenziali sui File (File System + Editing)
* **Blocchi XML Multipli:** Se un task richiede passaggi strettamente sequenziali in cui una fase dipende dall'esito di una precedente (es: prima copiare/rinominare un file tramite `<shell>` e poi modificarlo tramite `<snippet>`), **NON** inserire tutte le istruzioni in un unico blocco `<changes>`. Fornisci l'output dividendo i passaggi in **più blocchi XML separati** (`<changes>...</changes>`). Lo script parser li eseguirà nell'ordine esatto in cui compaiono nel testo, assicurando che le operazioni a file system siano completate prima di tentare la patch del codice.

### 📂 Spostamento, Copia e Ridenominazione File (Shell vs Riscrittura)
* **Prevenire Riscritture Inutili:** Quando ti viene richiesto di rinominare una rotta, spostare una cartella o duplicare un file, **NON USARE MAI** il tag `<file>` per riscriverne interamente il contenuto nel nuovo percorso. Le riscritture complete (Full Rewrite) sono lente e ad alto rischio di introdurre errori.
* **Usa piuttost la Shell:** Utilizza i comandi del terminale Windows (`ren`, `move`, `copy`) all'interno del tag `<shell>` per gestire queste operazioni a livello di file system in modo immediato e sicuro a "rischio zero". Se il file necessita anche di modifiche interne (es. aggiornamento import) dopo lo spostamento, usa un blocco `<changes>` successivo per applicare le singole patch tramite `<snippet>`.

### 🗄️ Limiti Variabili SQL in Cloudflare D1 (Batching)
* **Prevenire `SQLITE_ERROR: too many SQL variables`**: Quando devi inserire massivamente multipli record in una tabella D1 usando Drizzle ORM, **NON USARE MAI** l'inserimento multi-valore passandogli direttamente l'array di oggetti (`await db.insert(table).values(array)`). SQLite ha limiti rigorosi per le variabili in una singola query. Invece, cicla i dati e crea un array di statement individuali e inviali usando **`db.batch(array_di_statements)`**, chunkando l'array in sezioni da 100 per non eccedere le limitazioni per-batch imposte da Cloudflare.