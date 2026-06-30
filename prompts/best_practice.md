File: `prompts/best_practice.md`
All'interno del codebase: `Rep`

## REGOLE PER QUESTO FILE DELLE BEST-PRACTICE
*   Questo file contiene il frutto della conoscenza empirica ottenuta tramite fix di errori e bug, il suo scopo è prevenirli in futuro, per farlo è da mantenere aggiornata inserendo soluzioni a problemi che si sono riscontrati e potrebbero tornare utili in futuro.
*   **Attenzione! Queste sono istruzioni scritte dall'AI coder per l'AI coder**: vanno tenute **stringate e minimali, quasi criptiche**, non serve dare grandi spiegazioni perché:
1. L'AI coder sa già il perché e il per come, gli basta un promemoria.
2. La finestra contestuale è limitata, più dilunghiamo qui, più compromettiamo la qualità del lavoro dell'AI coder.
*   Nell'aggiornare questo file bisogna essere GENERICI: non menzionare mai cose specifiche del progetto su cui si sta lavorando, anche perché la natura delle app su cui si andrà a lavorare può variare anche di molto.
*   All'AI coder viene dato un comando (best_practice_append) per aggiungere qui nuove regole. Questo va bene solo se si tratta di cose nuove; ma se le regole possono essere integrate in uno dei paragrafetti esistenti è meglio chiedere all'utente umano di fare una sostituzione con Snippet, sapendo che questo file sta in un altro codebase (`Rep`) con url relativo: **`prompts/best_practice.md`**, perciò è da fare un XML a parte che l'utente dovrà applicare nel progetto `Rep`.

### ☁️ Regole specifiche per OpenNext Cloudflare
*   **No Runtime Edge:** Non scrivere MAI `export const runtime = 'edge'`. OpenNext pacchettizza già tutto per Workers, dichiararlo fa fallire il bundler di `@opennextjs/cloudflare`.
*   **Tipizzazione Bindings:** Dichiara sempre i binding (D1, KV, R2) in `src/cloudflare-env.d.ts` usando l'esatta sintassi: `declare global { interface CloudflareEnv { NOME_BINDING: D1Database } }`.
  
### 🗄️ Database & Drizzle ORM (SQLite / D1)
*   **Limiti ALTER TABLE SQLite:** Per nuove colonne in tabelle esistenti, NON USARE MAI default dinamici come `.default(sql(CURRENT_TIMESTAMP))`. La migrazione fallirà. Gestisci il timestamp programmaticamente da TS.
*   **Eliminazione a cascata e vincoli (ON DELETE):** Cloudflare D1 fa fallire l' `ON DELETE CASCADE` sollevando `D1_ERROR: FOREIGN KEY constraint failed`. Elimina sempre esplicitamente i record figli (`await db.delete(children).where(...)`) prima di eliminare il record padre.
*   **Limiti Variabili SQL (Batching):** Prevenire `SQLITE_ERROR: too many SQL variables` in D1. NON usare mai l'inserimento multi-valore passandogli direttamente l'array (`await db.insert(table).values(array)`). Cicla i dati inviandoli con `db.batch(array_di_statements)` a chunk di 100.
*   **Sincronizzazione ID:** Nelle Foreign Key verso Primary Key mutabili (es. temp ID -> auth ID), dichiara esplicitamente l'update: `.references(() => users.id, { onDelete: "cascade", onUpdate: "cascade" })`. Previene `SQLITE_CONSTRAINT_FOREIGNKEY`.

### 🛡️ TypeScript & Gestione Dati
*   **Risposte JSON (Strict Mode):** Cast esplicito su `await res.json()` (es. `as any` o interfaccia) per prevenire l'errore `Object is of type unknown`.
*   **Strict Null Checks:** Passando dati tra API, usa SEMPRE fallback sicuri (es. `const data = res.data || "";`) o optional chaining (`obj?.property`).

### 🔐 Clerk (Autenticazione)
*   **Middleware Options:** Non passare opzioni di routing come `{ afterSignOutUrl: "/" }` in `clerkMiddleware()`. Fallisce il type-checking ("No overload matches this call"). Usa invece il file `.env` (es. `NEXT_PUBLIC_CLERK_AFTER_SIGN_OUT_URL=/`).

### 🛠️ Misure Correttive e Troubleshooting pre-build
**Segnala e proponi immediata correzione se:**
*   Cartelle come `scripts/` o `tests/` non sono escluse nell'array `"exclude"` del `tsconfig.json`.
*   In `next.config.ts` manca l'impostazione `eslint: { ignoreDuringBuilds: true }`.
*   Il `.gitignore` esclude cartelle vitali (`/drizzle`, `/public`, estensione `*.md`). Ignora solo file temporanei AI (`PROMPT.md`, `repomix-output.txt`).

### ☁️ Librerie e Inizializzazione in Cloudflare Workers
*   **Googleapis (gaxios):** La libreria ufficiale crasha su Edge ("Cannot read properties of null (reading 'has')"). Evitala. Genera il JWT con `node:crypto` ed esegui la chiamata con `fetch()` nativa.
*   **Cloudflare-env.d.ts Controllo:** Assicurati che `src/cloudflare-env.d.ts` esista (file che estrae `Cloudflare.Env` e `NodeJS.ProcessEnv`) e sia tracciato. Nei `.gitignore` e `.repomixignore` usa la direttiva root `/cloudflare-env.d.ts` per escludere solo il file autogenerato gigante. Avvisa di ciò nel tag `<shell>` solo alla prima esecuzione.
*   **No Top-Level Env:** Evita inizializzazione client globali (Resend, AWS, OpenAI) via `process.env`. Inizializzali nelle funzioni estraendo `getCloudflareContext().env`.
*   **Sincronizzazione CloudflareEnv:** Aggiorna OBBLIGATORIAMENTE `src/cloudflare-env.d.ts` ogni volta che aggiungi un segreto con `wrangler secret put` o nel `wrangler.jsonc`. TS bloccherà la build altrimenti.
*   **Lettura Variabili (Cloudflare vs Local):** Usa SEMPRE il fallback locale (altrimenti l'oggetto env non preleva dal `.env.local` standard): `const secret = (getCloudflareContext().env as any)?.MIA_CHIAVE || process.env.MIA_CHIAVE;`.
*   **Dynamic Opt-out:** Pagine/Route che usano D1, KV, R2 via `getCloudflareContext()` falliscono staticamente. Aggiungi OBBLIGATORIAMENTE `export const dynamic = "force-dynamic"`.
*   **Crash Miniflare R2 (false == true):** MAI usare `Buffer.from(...)` in upload R2 (`env.BUCKET.put()`). Manda in crash C++ (Miniflare/workerd). Usa API Web: `atob()` e `Uint8Array` passandogli `.buffer`.

### 🛠️ Resilienza alle Dipendenze Esterne (Zero-Config Tolerance)
*   **Build Resilience (Providers):** Nel `RootLayout`, verifica la presenza delle chiavi (`NEXT_PUBLIC_...`). Se manca, renderizza `children` senza provider per prevenire crash in build.
*   **Middleware & Action Safety:** Esegui controlli preventivi sulle Secret Key prima di invocare metodi. Usa Fallback Content nell'UI invece di crashare la pagina se i dati esterni falliscono.

### 🦜🔗 LangChain & Prompt Engineering
*   **Escaping Parentesi Graffe:** Raddoppia SEMPRE le parentesi graffe letterali (`{{` e `}}`) negli esempi JSON del prompt per evitare l'errore LangChain `Single '}' in template`.

### ☁️ Configurazione Wrangler per OpenNext
*   **Conflitto `pages_build_output_dir`:** Distribuendo come Worker con direttiva `"assets"`, NON inserire MAI `"pages_build_output_dir"`. Causa blocco CLI: "It looks like you've run a Workers-specific command in a Pages project".
*   **Prevenzione SQLITE_BUSY:** In `next.config.ts`, incapsula SEMPRE `initOpenNextCloudflareForDev()` dentro `if (process.env.NODE_ENV === "development") { ... }`.

### 💻 File System, Terminale e Operazioni Sequenziali
*   **Cursor:pointer:** Sempre presente su link e pulsanti interattivi.
*   **Eliminazione sicura:** Usa `<delete_file path="path/to/file_or_folder" />` (sposta nel cestino). Per cartelle enormi (`node_modules`, `.next`) usa la `<shell>`: `rd "nome_cartella" -Recurse -Force`.
*   **Terminale Integrato (Shell):** Ambiente PowerShell Windows. NO comandi Unix, NO cmd.exe, NO cambi di stato `cd`. Usa path relativi dalla root (es. `ren "src\vecchio" "nuovo"`).
*   **Spostamento/Ridenominazione:** MAI usare il Full Rewrite `<file>` per spostare file. Usa la shell (ren, move, copy) nel tag `<shell>`. Se serve patchare, usa uno `<snippet>` nel blocco successivo.
*   **Operazioni Sequenziali:** Dividi in più blocchi XML separati (`<changes>...</changes>`) i task dipendenti l'uno dall'altro (es. rinomina via shell e poi patch).

### ☁️ Resilienza LLM e Task Lunghi in Cloudflare Workers
*   **Niente `waitUntil` per AI/LLM:** In Cloudflare Workers termina in 30s ("waitUntil tasks did not complete..."). Usa esecuzioni asincrone sincrone con await aperto verso client (fino a 100s).
*   **Chunking Generativo (Batching):** Moli di dati enormi superano i 100s. Spezza in cicli for minori (es. 3 cicli) passando il background generato per non ripetere.
*   **Estrazione Array Ricorsiva:** L'LLM restituisce spesso il JSON wrappato (`{ "risultati": [...] }`). NON fidarti di `Array.isArray(res.data)`. Implementa SEMPRE estrattori ricorsivi in profondità.
*   **Modelli Obsoleti:** I modelli (gpt-4o-mini, gemini-1.5) sono DEPRECATI rispetto al tuo cutoff. Chiedi SEMPRE all'utente prima di hardcodare il modello.

### ⚡ Ottimizzazione Performance (Effetto Zero-Latency)
*   **Auth Istantanea:** MAI usare `await supabase.auth.getUser()` in middleware, layout, azioni o route handler (sfora limiti CPU 10ms su Cloudflare, errore 503). Usa SOLO `await supabase.auth.getSession()`.
*   **Cache in-memory (RBAC):** Funzioni di autorizzazione (es. `checkAdmin()`) DB-dependent DEVONO essere in `cache()` React e implementare una `Map` globale in memoria RAM V8 (scadenza 60s).
*   **Pattern SWR Custom (Zero-Latency):** 1. Server Action (DB ram cache 60s). 2. page.tsx Server (passa initialData 0ms). 3. Client Component interattiva (inizializza stato e lancia `useEffect` mutazioni silenti).
*   **Prefetch Aggressivo Mirato:** Applica SEMPRE `prefetch={true}` sui `<Link>` di navigazione interna (NO scansioni globali, fallo nel nuovo codice; omettilo per pagine legali).
*   **Parallelizzazione Assoluta:** MAI scrivere chiamate asincrone sequenziali in `page.tsx`/`layout.tsx`. Usa SEMPRE un unico `await Promise.all([...])`.
*   **Eliminazione `loading.tsx`:** In architetture prefetch SWR, causano sfarfallii e finti blocchi. Non usarli.
*   **Background Actions (RSC Crash):** Auto-save e `setInterval` DEVONO essere in `try/catch` silenti lato client per evitare che il parsing HTML di un errore 503 distrugga l'UI (White Screen). MAI usare `revalidatePath()` qui.

### 🔐 Gestione Identità e Sopravvivenza Task
*   **Auth Backend-Driven (Split-Brain):** MAI aggiornare dati identità (Email/Password) via `supabase.auth.updateUser()` lato client. Usa Server Action via `SUPABASE_SERVICE_ROLE_KEY` in blocco `try/catch` pseudo-transazionale su Supabase e DB locale (rollback se fallisce DB).
*   **Sopravvivenza Task (Fire-and-Forget):** Se lanci un task asincrono + `router.push()`, React annulla l'azione e Cloudflare uccide il worker. Usa SEMPRE chiamata nativa `fetch()` verso Route API/Webhook (connessione HTTP sopravvive).

### 🔍 SEO Next.js App Router (Solo Siti Pubblici)
*   **MetadataBase e Canonical:** Usa SEMPRE `metadataBase: new URL(...)` via env. MAI usare stringhe vuote o `canonical: '/'`.
*   **No WWW:** MAI assumere/hardcodare `www.` in canonical, sitemap, metadataBase, JSON-LD, o robots.ts. Usa SEMPRE ENV (es. `process.env.NEXT_PUBLIC_APP_URL`) con fallback esplicito *senza* `www.`.
*   **Titoli e SERP:** Keyword precede il brand. Allinea `title.default` e `description` del `layout.tsx` col JSON-LD. Aggiungi `title: { absolute: "..." }` nella home per evitare titoli doppi.
*   **JSON-LD (Schema.org):** Usa sempre `alternateName`, `image` (favicon/logo), `priceRange`. I giorni (`dayOfWeek`) SEMPRE IN INGLESE. Safe-check per crash (es. `hours?.split('-')`).
*   **Resilienza CMS (Anti-Cliente):** Avvolgi le fetch CMS nei metadata in `try/catch` con fallback SEO hardcoded per salvare le keyword.
*   **Duplicate Content / Cannibalizzazione:** Pagine Terms, Privacy, Cookies DEVONO avere `robots: { index: false }` ed essere rimosse dalla sitemap. Avvisa l'utente di impostare redirect 301 su Cloudflare da WWW a root (ignora warning proxy DNS).
*   **Sitemap e Robots:** Sitemap esaustiva (include TUTTE le pillar statiche e non solo root/dinamiche). `lastModified: new Date()`. In `robots.ts` l'URL sitemap deve usare l'ENV (evita Cross-Domain errors in GSC).
*   **Favicon:** `icon.png` in `src/app/` (approccio file-based per cache busting), NON forzarla nel layout. Deve misurare un multiplo esatto di 48px.

### 📧 Resend & Email Deliverability (Anti-Spam Strict)
1. **NO `mailto:`**: Mai usarlo se email del link e `replyTo` differiscono dal `From` (Phishing flag). Usa `<span>`.
2. **Plain Text**: Invia SEMPRE prop `text` come fallback.
3. **Struttura**: L'HTML DEVE essere pagina completa: `<!DOCTYPE html><html><body>...</body></html>`.
4. **CamelCase**: Resend SDK >v6 usa `replyTo`.
5. **Disclaimer e Sender Name**: Aggiungi footer ("Email generata da..."). Il `From` DEVE avere il nome del brand reale (non "Form contatti").