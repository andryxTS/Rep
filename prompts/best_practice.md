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
* **No Cambi di Stato (`cd`):** Quando fornisci comandi shell (es. per rinominare o spostare file) all'interno del tag `<shell>`, **NON usare mai** il comando `cd` per cambiare cartella. La pratica migliore, più robusta e raccomandata, è eseguire i comandi direttamente partendo dalla root. Specifica sempre i percorsi relativi in modo esplicito (es. usa `ren "src\flussi\vecchio_nome" "nuovo_nome"` anziché fare `cd` nella directory).

### 🔄 Operazioni Sequenziali sui File (File System + Editing)
* **Blocchi XML Multipli:** Se un task richiede passaggi strettamente sequenziali in cui una fase dipende dall'esito di una precedente (es: prima copiare/rinominare un file tramite `<shell>` e poi modificarlo tramite `<snippet>`), **NON** inserire tutte le istruzioni in un unico blocco `<changes>`. Fornisci l'output dividendo i passaggi in **più blocchi XML separati** (`<changes>...</changes>`). Lo script parser li eseguirà nell'ordine esatto in cui compaiono nel testo, assicurando che le operazioni a file system siano completate prima di tentare la patch del codice.

### 📂 Spostamento, Copia e Ridenominazione File (Shell vs Riscrittura)
* **Prevenire Riscritture Inutili:** Quando ti viene richiesto di rinominare una rotta, spostare una cartella o duplicare un file, **NON USARE MAI** il tag `<file>` per riscriverne interamente il contenuto nel nuovo percorso. Le riscritture complete (Full Rewrite) sono lente e ad alto rischio di introdurre errori.
* **Usa piuttost la Shell:** Utilizza i comandi del terminale Windows (`ren`, `move`, `copy`) all'interno del tag `<shell>` per gestire queste operazioni a livello di file system in modo immediato e sicuro a "rischio zero". Se il file necessita anche di modifiche interne (es. aggiornamento import) dopo lo spostamento, usa un blocco `<changes>` successivo per applicare le singole patch tramite `<snippet>`.

### 🗄️ Limiti Variabili SQL in Cloudflare D1 (Batching)
* **Prevenire `SQLITE_ERROR: too many SQL variables`**: Quando devi inserire massivamente multipli record in una tabella D1 usando Drizzle ORM, **NON USARE MAI** l'inserimento multi-valore passandogli direttamente l'array di oggetti (`await db.insert(table).values(array)`). SQLite ha limiti rigorosi per le variabili in una singola query. Invece, cicla i dati e crea un array di statement individuali e inviali usando **`db.batch(array_di_statements)`**, chunkando l'array in sezioni da 100 per non eccedere le limitazioni per-batch imposte da Cloudflare.

### ☁️ Cloudflare R2 & Crash Miniflare (false == true)
* **No Node.js Buffer:** Quando carichi file su Cloudflare R2 tramite `env.BUCKET.put()`, **NON USARE MAI** `Buffer.from(...)`. In ambiente di sviluppo (Miniflare/workerd), passare un oggetto Buffer nativo di Node.js manda in crash irreparabile il motore C++ sottostante restituendo l'errore fatale `failed: false == true`.
* **Soluzione:** Usa sempre API standard del Web. Se hai una stringa passala direttamente. Se hai un Base64, convertilo usando `atob()` e mappalo in un `Uint8Array` passandogli poi `.buffer` (l'ArrayBuffer nativo).

### ☁️ Resilienza LLM e Task Lunghi in Cloudflare Workers (Timeout & JSON)
Nelle architetture Serverless, le chiamate agli LLM sono soggette a limiti rigidi e comportamenti imprevedibili. Segui sempre questo triplo scudo difensivo:
1. **Niente `waitUntil` per AI/LLM (Il limite dei 30s):** Non delegare MAI operazioni LLM di lunga durata a `ctx.waitUntil()`. In Cloudflare Workers, i task in background "sganciati" dalla richiesta principale vengono terminati in circa 30 secondi ("waitUntil tasks did not complete within the allowed time"). **Soluzione:** Esegui sempre il task in modo **sincrono** (usando `await` prima di restituire la `NextResponse` o tramite Server Actions). Mantenendo la connessione HTTP aperta col client, Cloudflare concede fino a 100 secondi di esecuzione.
2. **Chunking Generativo (Il limite dei 100s):** Anche con la connessione aperta, se chiedi a un LLM di generare moli di dati enormi (es. "Scrivi 50 titoli JSON complessi"), sfonderai il limite dei 100 secondi e il processo verrà "assassinato" senza lanciare errori in console (il client vedrà solo un caricamento infinito o un errore 504). **Soluzione:** Usa il **Batching**. Spezza la richiesta in cicli più piccoli (es. 3 cicli da 15 elementi) usando un ciclo `for` nell'orchestratore, concatenando i risultati e passando all'LLM l'elenco di quanto già generato per evitare ripetizioni.
3. **Estrazione Array Ricorsiva (Il problema del JSON wrappato):** Non fidarti **MAI** del fatto che l'LLM restituisca un array JSON puro (`[...]`) alla radice della risposta, anche se esplicitamente intimato nel prompt. Spesso l'LLM incarterà l'array in un oggetto (es. `{ "risultati": [...] }` o `{ "titoli": { "lista": [...] } }`). Non usare un banale `Array.isArray(res.data)` come validazione. Implementa sempre un **estrattore ricorsivo** che scavi dinamicamente in tutti i livelli dell'oggetto finché non trova e restituisce l'array bersaglio.

### 🤖 Modelli LLM e Consapevolezza Temporale
* **Modelli Obsoleti:** Sii consapevole di essere in un'epoca molto successiva al tuo cut-off di training. I modelli che ricordi come "attuali" (es. gpt-4o-mini, gemini-1.5) sono DEPRECATI. Quelli che consideri "sperimentali" o futuri, o semplicemente non conosci, sono ora lo standard.
* **Azione:** Non inserire MAI modelli che tu conosci nel codice, perché sicuramente sono obsoleti, **chiedi sempre all'utente** prima di hardcodare, solo lui ti saprà dire quali modelli al momento sono allo stato dell'arte.

### ⚡ Ottimizzazione Performance (Effetto Zero-Latency / App Nativa)
Per garantire transizioni istantanee e azzerare il lag di navigazione in Next.js + Cloudflare Workers, l'AI DEVE applicare proattivamente i seguenti pattern:
* **Auth Istantanea (Supabase):** NON usare MAI `await supabase.auth.getUser()` nel `middleware.ts`, nei `layout.tsx`, `page.tsx`, **nelle Server Actions** o nei **Route Handlers**. Il suo peso crittografico sfora i limiti CPU (10ms) di Cloudflare Workers causando crash 503. Usa SEMPRE `await supabase.auth.getSession()` per leggere il cookie locale. Riserva `getUser()` SOLO per azioni critiche (es. cambio password).
* **Cache in-memory per Permessi (RBAC):** Le funzioni di autorizzazione (es. `checkAdmin()`) che interrogano il database (es. D1) DEVONO:
  1. Essere avvolte in `cache()` di React (per deduplicare le chiamate nel singolo render).
  2. Implementare internamente una `Map` globale in memoria con scadenza (es. 60s). Poiché i Cloudflare Workers riutilizzano l'Isolate V8, questo azzera i tempi di query DB nei successivi cambi di rotta.
* **Pattern SWR Custom (Zero-Latency):** Per eliminare il lag di navigazione (RSC waterfall) causato da fetch/mutazioni bloccanti nei Server Components:
  1. **Server Actions:** Implementa cache in RAM globale (TTL 60s) per le query DB.
  2. **page.tsx (Server):** Mantienilo leggerissimo. Esegui *solo* chiamate alle azioni cached (0ms) e passale come `initialData`. Mai eseguire task lenti qui.
  3. **Client Component:** Estrai l'intera UI interattiva qui. Inizializza lo stato con `initialData` per un rendering istantaneo, e usa `useEffect` al mount per lanciare mutazioni lente o fetch di dati freschi in background, aggiornando lo stato in modo silente.
* **Prefetch Aggressivo Mirato:** Sui componenti `<Link>` che portano a rotte interne all'app, forza la prop `prefetch={true}` (poiché in Next.js 15 le rotte dinamiche non effettuano il prefetch di default). 
  * **Comportamento AI:** Applica sempre il `prefetch={true}` nel **nuovo codice** che scrivi. Se modifichi file già esistenti per altri motivi, controlla e sistema i Link al loro interno. **NON** fare scansioni globali dell'intero codebase alla ricerca di Link da sistemare se non esplicitamente richiesto.
  * **Eccezione Banda:** NON forzare il prefetch per le pagine di servizio o a basso traffico (es. `/privacy`, `/terms`, `/cookies`), lascia che Next.js faccia il prefetch leggero di default solo all'hover per risparmiare risorse.
* **Parallelizzazione Assoluta (`Promise.all`):** Nei Server Components (`page.tsx` o `layout.tsx`), NON scrivere MAI chiamate asincrone sequenziali per dati indipendenti (es. `const a = await getA(); const b = await getB();`). Questo moltiplica la latenza, rende il prefetch inutile e causa lag al primo caricamento (quando la cache in RAM è ancora vuota). Raggruppa sempre tutte le Promise, inclusa la traduzione dei dizionari, in un unico `await Promise.all([...])`.
* **Eliminazione dei `loading.tsx`:** Quando si usa l'architettura SWR combinata al Prefetch Aggressivo per simulare un'app nativa, i file `loading.tsx` diventano dannosi. Costringono il router di Next.js a renderizzare uno stato di fallback intermedio (causando sfarfallii visivi o finti blocchi).
* **Background Actions & RSC Crash Prevention:** Qualsiasi Server Action innescata automaticamente dal client (es. `setInterval`, auto-save) DEVE essere incapsulata in un `try/catch` silente lato client. Un 503 del Worker farà tentare a Next.js il parsing dell'HTML di errore come RSC, distruggendo l'intera UI (White Screen). Inoltre, NON usare MAI `revalidatePath()` all'interno di queste azioni di background cicliche (esaurisce la CPU).

### 🔐 Gestione Identità e Sincronizzazione Auth/DB
* **Nome Regola:** Auth Backend-Driven per prevenzione Split-Brain.
* **Descrizione:** Nelle architetture in cui Supabase gestisce le identità e D1/Postgres locale conserva l'anagrafica utente, non permettere MAI aggiornamenti diretti client-side (es. Email o Password) tramite i metodi `supabase.auth.updateUser()`. Un disallineamento di rete tra la mutazione client e la sincronizzazione DB causa account orfani.
* **Soluzione:** Utilizza sempre una Server Action che interroga l'API di Admin Supabase tramite la `SUPABASE_SERVICE_ROLE_KEY`. Gestisci la mutazione su Supabase e su D1 all'interno di un blocco try/catch pseudo-transazionale, predisponendo il rollback manuale della modifica Supabase se il DB locale fallisce l'aggiornamento.