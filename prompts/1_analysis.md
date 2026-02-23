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
* Chiedimi il feedback riguardo alle scelte da fare presentandomele come elenco numerato con più opzioni (es. A, B, C...).
* Aspetta il mio feedback e le nuove istruzioni operative su come proseguire con il lavoro di coding vero e proprio.

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
{best_practice}

**MODIFICHE RICHIESTE:**
{user_input}

Ora procedi come ti ho indicato, aspetto le tue domande prima di darti istruzioni specifiche su come effettuare il coding vero e proprio.