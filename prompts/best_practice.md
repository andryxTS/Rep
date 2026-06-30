File: `prompts/best_practice.md`
All'interno del codebase `Rep`

## REGOLE PER QUESTO FILE DELLE BEST-PRACTICE
*   Questo file contiene il frutto della conoscenza empirica ottenuta tramite fix di errori e bug, il suo scopo è prevenirli in futuro, per farlo è da mantenere aggiornata inserendo soluzioni a problemi che si sono riscontrati e potrebbero tornare utili in futuro.
*   **Attenzione! Queste sono istruzioni scritte dall'AI coder per l'AI coder**: vanno tenute **stringate e minimali, quasi criptiche**, non serve dare grandi spiegazioni perché:
1. L'AI coder sa già il perché e il per come, gli basta un promemoria.
2. La finestra contestuale è limitata, più dilunghiamo qui, più compromettiamo la qualità del lavoro dell'AI coder.
*   Nell'aggiornare questo file bisogna essere GENERICI: non menzionare mai cose specifiche del progetto su cui si sta lavorando, anche perché la natura delle app su cui si andrà a lavorare può variare anche di molto.
*   All'AI coder viene dato un comando (best_practice_append) per aggiungere qui nuove regole. Questo va bene solo se si tratta di cose nuove; ma se le regole possono essere integrate in uno dei paragrafetti esistenti è meglio chiedere all'utente umano di fare una sostituzione con Snippet, sapendo che questo file sta in un altro codebase (`Rep`) con url relativo: **`prompts/best_practice.md`**, perciò è da fare un XML a parte che l'utente dovrà applicare nel progetto `Rep`.

### ☁️ Regole specifiche per OpenNext Cloudflare
*   **No Runtime Edge:** Non usare `export const runtime = 'edge'`. OpenNext pacchettizza già tutto per Workers, dichiararlo esplicitamente fa fallire il bundler.
*   **Tipizzazione Bindings:** Dichiara sempre i binding (D1, KV, R2) estratti da `getCloudflareContext().env` in un file globale `src/cloudflare-env.d.ts` estendendo `CloudflareEnv`.
  
### 🗄️ Database & Drizzle ORM (SQLite / D1)
*   **Limiti ALTER TABLE SQLite:** Per le nuove colonne in tabelle esistenti, NON USARE default dinamici come `.default(sql(CURRENT_TIMESTAMP))` (SQLite non lo supporta via `ALTER TABLE`). Gestisci il timestamp da codice TS.
*   **Eliminazione a cascata e vincoli (ON DELETE):** Il DB D1 (stateless) fa spesso fallire `ON DELETE CASCADE`. Elimina sempre esplicitamente i record figli prima di eliminare il record padre.
*   **Limiti Variabili SQL (Batching):** Mai insert massivi di array diretti in D1 (`SQLITE_ERROR: too many SQL variables`). Usa `db.batch()` processando i dati in chunk da max 100 record.
*   **Sincronizzazione ID:** Nelle PK mutabili (es. ID temporanei che diventano definitivi all'auth), usa SEMPRE `.references(() => ref.id, { onDelete: "cascade", onUpdate: "cascade" })` per prevenire errori di foreign key.

### 🛡️ TypeScript & Gestione Dati
*   **Risposte JSON:** Cast esplicito (`as any` o interfaccia) su `await res.json()` per evitare l'inferenza a `unknown`.
*   **Strict Null Checks:** Passando dati tra funzioni/API, usa sempre fallback sicuri (`|| ""`) o optional chaining (`?.`) per prevenire crash da `null`/`undefined`.

### 🔐 Clerk & Autenticazione
*   **Middleware Options:** Non passare opzioni di routing (es. `{ afterSignOutUrl: "/" }`) in `clerkMiddleware()` (causa errore TS). Usa le variabili d'ambiente in `.env`.
*   **Auth Backend-Driven (Split-Brain):** Mai aggiornare dati auth sensibili dal client (es. `supabase.auth.updateUser()`). Usa Server Actions + `SUPABASE_SERVICE_ROLE_KEY` per mutare Supabase e DB locale in un `try/catch` pseudo-transazionale (rollback manuale su Supabase se D1 fallisce).

### 🛠️ Misure Correttive e Troubleshooting pre-build
**Segnala e correggi immediatamente se:**
*   `tsconfig.json` non esclude cartelle come `scripts/` o `tests/` (blocca la build).
*   In `next.config.ts` manca `eslint: { ignoreDuringBuilds: true }`.
*   `.gitignore` esclude cartelle vitali (`/drizzle`, `/public`, `*.md`). Ignora solo file AI (es. `PROMPT.md`, `repomix-output.txt`).

### ☁️ Cloudflare Workers: Compatibilità e Inizializzazione
*   **Librerie Incompatibili (googleapis):** `gaxios` crasha su Edge. Sostituisci l'integrazione generando JWT manualmente (`node:crypto`) usando API nativa `fetch()`.
*   **Cloudflare-env.d.ts Controllo:** Assicurati che `src/cloudflare-env.d.ts` esista e sia tracciato. Nei `.gitignore` e `.repomixignore` usa la direttiva `/cloudflare-env.d.ts` (escludendo solo la root) rimuovendo eventuali direttive generiche senza slash. Avvisa l'utente di questo check con un commento nel tag `<shell>` solo la prima volta, poi non ricordarglielo più.
*   **No Top-Level Env:** Mai inizializzare SDK (Resend, AWS, OpenAI) globalmente tramite `process.env`. Inizializza i client dentro la funzione via `getCloudflareContext().env`.
*   **Sincronizzazione CloudflareEnv:** Aggiorna sempre `src/cloudflare-env.d.ts` all'aggiunta di segreti/variabili, per non fallire la build TS.
*   **Lettura Variabili (Cloudflare vs Local):** Usa SEMPRE il fallback locale: `const secret = (getCloudflareContext().env as any)?.CHIAVE || process.env.CHIAVE`.
*   **Dynamic Opt-out:** Forza `export const dynamic = "force-dynamic"` nelle pagine/API che usano D1, KV o R2, per evitare errori di pre-rendering statico.
*   **Crash Miniflare R2:** MAI usare `Buffer.from(...)` per upload su R2. Usa le API standard Web (es. `Uint8Array`).

### 🛠️ Resilienza alle Dipendenze Esterne (Zero-Config)
*   **Build Resilience:** Nei layout, verifica l'esistenza delle chiavi SDK (`NEXT_PUBLIC_...`) prima di montare i Provider. Manca chiave = renderizza senza Provider (evita crash in SSG).
*   **Middleware/Action Safety:** Esegui un check preventivo sulle Secret Key prima di invocare logiche. Usa stati di fallback nell'UI se i dati esterni falliscono o non sono inizializzati.

### 🦜🔗 LangChain & Prompt Engineering
*   **Escaping Parentesi Graffe:** Raddoppia sempre le parentesi graffe letterali (`{{` e `}}`) nei template di prompt per evitare crash JSON in LangChain.

### ☁️ Configurazione Wrangler per OpenNext
*   **Conflitto Workers vs Pages:** NON inserire MAI `"pages_build_output_dir"` se usi `"assets"` e distribuisci come Worker. Blocca il deploy.
*   **SQLITE_BUSY in Build:** In `next.config.ts`, incapsula `initOpenNextCloudflareForDev()` in `if (process.env.NODE_ENV === "development")` per non lockare il DB in CI/CD.

### 💻 File System, Terminale e Operazioni AI
*   **Cursor:pointer:** Sempre presente su link e pulsanti interattivi.
*   **Eliminazione file:** `<delete_file path="..." />` (finisce nel cestino). Per dir enormi (node_modules), usa `<shell>`: `rd "nome_cartella" -Recurse -Force`.
*   **Terminale Integrato (Shell):** L'ambiente è PowerShell Windows. No comandi Unix. MAI usare `cd`, esegui comandi dalla root specificando i percorsi (es. `ren "src/file" "nuovo"`).
*   **Spostamento/Copia File:** Usa shell (ren, move) invece del Full Rewrite `<file>` per prevenire errori ed essere più rapido. Usa un successivo snippet se il file va anche patchato.
*   **Operazioni Sequenziali:** Se un task richiede passaggi dipendenti (es. move e poi edit), dividi l'output in blocchi separati `<changes>...</changes>`.

### ⚡ Ottimizzazione Performance (Zero-Latency / App Nativa)
*   **Auth Istantanea:** MAI `await supabase.auth.getUser()` in middleware/layout/actions (lento, genera 503). Usa `await supabase.auth.getSession()`.
*   **Cache in-memory (RBAC):** Wrappa le check admin in `cache()` React + usa `Map` globale in RAM con scadenza. Azzera latenza.
*   **SWR Custom:** Server Action con RAM Cache -> page.tsx passa `initialData` -> Client component renderizza istantaneamente e muta/fetch in background silente via `useEffect`.
*   **Prefetch Aggressivo:** Obbligo prop `prefetch={true}` nei `<Link>` di navigazione interna (eccetto privacy/terms).
*   **Parallelizzazione:** In Server Components raggruppa le chiamate in `Promise.all([...])`. MAI fare await asincroni in sequenza se indipendenti.
*   **No loading.tsx:** Se usi SWR e prefetch, i `loading.tsx` diventano dannosi causando finti sfarfallii RSC.
*   **Background Actions Safety:** Task ripetitivi (`setInterval`) che chiamano Server Actions DEVONO avere `try/catch` silenti lato client per evitare crash White-Screen su eventuali 503. MAI usare `revalidatePath()`.
*   **Sopravvivenza Task:** Usa `fetch()` nativa invece di Server Actions se fai `router.push()` subito dopo. Le chiamate HTTP sopravvivono al kill del Worker al cambio pagina.
*   **Limiti LLM Serverless:** Niente `waitUntil` (taglia a 30s). Task lunghi LLM vanno sincroni e chunkati a step (max 100s). Validare JSON ricorsivamente ignorando wrapper inutili generati dall'LLM.
*   **Modelli AI:** Non hardcodare modelli LLM noti (sono obsoleti). Chiedi sempre il modello attuale all'utente.

### 🔍 SEO Next.js App Router (Siti Pubblici)
*   **metadataBase, Canonical e OG:** Sempre `metadataBase: new URL(...)` tramite variabile d'ambiente. MAI canonical vuoto o `/`. 
*   **No WWW:** MAI hardcodare il prefisso `www.` in canonical, sitemap o metadataBase. Usa SEMPRE l'ENV (es. `process.env.NEXT_PUBLIC_APP_URL`) con fallback esplicito senza `www.`.
*   **Titoli e SERP:** Keyword principale prima del brand. Allinea `title.default` e `description` del `layout.tsx` col JSON-LD. Forzare `title: { absolute: "..." }` in home.
*   **JSON-LD:** Includi sempre `alternateName`, `image` (favicon/logo) e `priceRange`. Giorni della settimana in inglese.
*   **Resilienza SEO CMS:** Avvolgi le fetch al CMS nei metadata in `try/catch` con fallback hardcoded per salvare le keyword.
*   **Favicon:** File `icon.png` deve essere multiplo esatto di 48px. Usa l'approccio file-based per il cache-busting Next.js, no URL hardcodati nel layout.
*   **Prevenzione Cannibalizzazione:** Privacy, Terms e Cookies DEVONO avere `robots: { index: false }` ed essere assenti dalla sitemap (pericolo link juice nel footer).
*   **Sitemap e Robots:** Sitemap completa (incluse le statiche pillar). Usa date dinamiche (`new Date()`). In `robots.ts`, l'URL della sitemap DEVE essere dinamico via ENV.
*   **Duplicate Content:** Ricorda all'utente di configurare regole 301 su Cloudflare (WWW to root) per evitare versioni doppie del sito.

### 📧 Resend & Email Deliverability (Anti-Spam Strict)
*   **NO `mailto:`:** Evitalo se differisce dal `From` (Phishing flag).
*   **Plain Text e Struttura:** Invia sempre prop `text` (fallback) con HTML (sempre tag completi `<html><body>`).
*   **CamelCase:** Resend >v6 usa `replyTo`.
*   **Disclaimer e Sender:** Includi footer automatico. Il `From` deve avere il brand reale, non nomi generici ("Form contatti").