**Contesto:**
Ho una app e voglio apportare alcune modifiche.

**Input:**
In allegato a questo messaggio trovi due file:
1. `repomix-output.txt`: L'intero codebase del progetto.
2. Questo file `PROMPT.md` con le istruzioni.

**Task:**
Ti chiederò di effettuare alcune modifiche al mio codebase. Per adesso farai un'analisi e aspetterei il mio feedback. In una seconda fase futura procederai con il coding.

**PROCEDURA**
{procedura_analisi}

**BEST PRACTICE**
* Best-practice: il lavoro dovrà essere eseguito secondo le best-practice per il framework in questione (ad esempio uso Image invece che img, valori di fallback, separazione logica/layout, ecc.).
* Practice del mio repo: Eccezione alla regola precedente: adattati all'approccio che vedi utilizzato nel mio repo (se ad esempio il mio repo utilizza qualcosa che non è esattamente tra le best-practice, adattati comunque all'approccio del mio repo, previa approvazione mia, ricordati di richiedermi il feedback).
* Quando scrivi codice non mettere commenti tipo "NUOVO: .." o "<-- aggiunto qui!, "qui novità", "nuova funzione", ecc. Tratta il codice e i commenti come ìl nuovo codice di produzione, che quindi permarrà magari negli anni a venire, ciò che ora è nuovo non lo sarà in futuro, inutile mettere commenti del genere; sappiamo noi in fase di modifica ciò che è nuovo e Git è più che sufficiente a farcelo notare.
* Quando modifichi un componente nel mio codice attieniti a ciò che devi per forza modificare, cerca di mantenerti fedele su tutto il resto; per tua natura ogni tanto tendi a cambiare gli stili, i contrasti, i colori, stai attento, perché se viene richiesta una modifica logica, la parte di stile deve rimanere tale e le classi, i colori, le spaziature, ecc. devono essere riportati nei componenti modificati in modo fedele all'originale.
* Dati dinamici: Se trovi collegamenti a CMS (es. Sanity), mantieni l'approccio, evita contenuti hardcoded (eccetto fallback).
* Installazione pacchetti Node.js: di default usa `pnpm`, NON usare `npm`. Usa npm solo se dall'analisi del mio codice ti accorgi che inequivocabilmente usato npm per quell'app.
* Se vedi che ci sono database collegati ricordati di includermi i comandi per rendere funzionanti le nuove modifiche (es: generate e migrate).
* Segui le altre best-practice incluse di seguito, servono a scongiurare e prevenire errori e perdite di tempo. Fai questi controlli in sordina, avvisami e proponimi soluzioni solo se noti delle evidenti criticità:

**SYSTEM PROMPT - BEST PRACTICES**
*(Le seguenti regole sono estratte dal file `prompts/best_practice.md`. Se durante il lavoro affronti e risolvi un problema molto comune o insidioso che andrebbe prevenuto globalmente in futuro, potrai proporre una regola aggiuntiva a questo file usando il tag `<best_practice_append>` in fase di esecuzione XML).*
{best_practice}

**MODIFICHE RICHIESTE:**
{user_input}

Ora procedi come ti ho indicato, aspetto le tue domande prima di darti istruzioni specifiche su come effettuare il coding vero e proprio.