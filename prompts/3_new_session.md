
**CONTESTO: NUOVA SESSIONE**
Sopra trovi il riassunto delle attività svolte nella sessione precedente, inclusa l'analisi architetturale e lo stato dell'arte.
In allegato trovi il file `repomix-output.txt` che contiene l'intero codebase aggiornato allo stato attuale.

**TASK**
1. Leggi il riassunto per allinearti sul contesto.
2. Analizza il codebase allegato per confermare i dettagli tecnici.
3. Attendi indicazioni su come proseguire il lavoro di modifica/debug.

**PROCEDURA E FORMATO**
Attieniti alle seguenti regole:
* Analizza il codebase, capendo: architettura, approccio, stile, flusso dei dati.
* Poni attenzione sulle dipendenze, sulle librerie utilizzate e sui modi in cui vengono prelevati e renderizzati i dati.
* Quando leggi le modifiche che ti propongo, pensa ad un piano su come applicarle; ci saranno forse da prendere delle decisioni: voglio essere coinvolto in queste decisioni.
* Quindi eventualmente chiedimi il feedback riguardo alle scelte da fare presentandomele come elenco numerato con più opzioni (es. A, B, C...).
* Aspetta il mio feedback e le nuove istruzioni operative su come proseguire con il lavoro di coding vero e proprio.

**BEST PRACTICE**
* Best-practice: il lavoro dovrà essere eseguito secondo le best-practice per il framework in questione (ad esempio uso Image invece che img, valori di fallback, separazione logica/layout, ecc.).
* Practice del mio repo: Eccezione alla regola precedente: adattati all'approccio che vedi utilizzato nel mio repo (se ad esempio il mio repo utilizza qualcosa che non è esattamente tra le best-practice, adattati comunque all'approccio del mio repo, previa approvazione mia, ricordati di richiedermi il feedback).
* Dati dinamici: Se trovi collegamenti a CMS (es. Sanity), mantieni l'approccio, evita contenuti hardcoded (eccetto fallback).
* initialValue: se aggiungi campi a Sanity, includi sempre un initialValue.
* Segui le altre best-practice incluse di seguito, servono a scongiurare e prevenire errori e perdite di tempo. Fai questi controlli in sordina, avvisami e proponimi soluzioni solo se noti delle evidenti criticità:

**SYSTEM PROMPT - BEST PRACTICES**
{best_practice}

## Fase ESECUTIVA
Quando entri nella fase esecutiva, di coding, ricordati che è MOLTO delicata, perché sei chiamato a modificare più file, perché è un'app in produzione, perché NON abbiamo a disposizione più tentativi, dev'essere one-shot e il tuo output verrà automaticamente convertito in modifiche al mio repo (i file verranno sovrascritti!).
Quindi quando entrerai in questa fase seguirai queste indicazioni:

### Procedura
* Analizza il mio feedback.
* Rivedi la tua analisi fatta in precedenza.
* Pianifica le operazioni che dovrai eseguire, cura ogni dettaglio.
* Scrivi questo piano in chiaro, prima di cominciare il lavoro di coding.
* VINCOLO DI ESISTENZA DEI PATH: Prima di generare un <file> o uno <snippet>, devi obbligatoriamente verificare che il path esista esattamente come elencato nella sezione 'Directory Structure' o all'interno dei tag <file path="..."> del file repomix-output.txt fornito. Non inventare percorsi basandoti su convenzioni (es. non assumere /components/ui/ se il file è in /components/). Se un file non esiste nel contesto, non tentare di modificarlo.
* Scrivi un piccolo riepilogo testuale con i file che dovrai modificare/aggiungere/eliminare [EDIT] / [NEW] / [DELETE]; per ognuno di questi, prima di scriverlo, verifica che il path e file esistano realmente, come suggerito al punto precedente.
* Scrivi il nuovo codice per le pagine modificate o nuove, PER INTERO (salvo uso snippets), nel formato XML specificato sotto, **modifica solo quanto necessario** e **mantieni intatto il resto, compresi i commenti, LA FEDELTÀ ESTREMA È RICHIESTA E CRUCIALE**).
* Dichiarazione Strategia: Nel tuo riepilogo testuale, per ogni file devi scrivere esplicitamente: "File: [nome], Righe stimate: [N], Strategia: [FULL REWRITE / SNIPPET]". Se scrivi "SNIPPET" per un file piccolo, l'operazione sarà considerata un errore.
* Riportami dentro i tag <shell></shell> tutti i comandi a terminale (windows, integrato in VS Code) necessari per far funzionare le nuove modifiche (tralascia pnpm build o pnpm dev, quello è scontato e solitamente c'è l'ho costantemente attivo). Quando vedi che l'app si interfaccia con dei db dammi gli appositi comandi di generate e migrazione se le modifiche lo rendono necessario. Di default dammi i comandi per aggiornare il sistema in locale, perché di base lavorarerò più che altro in locale. Ad esempio se sto usando drizzle su un D1 all'interno del tag shell aggiungerai:
   pnpm drizzle-kit generate
   echo "y" | pnpm wrangler d1 migrations apply nome-del-db --local

{formato_output}
