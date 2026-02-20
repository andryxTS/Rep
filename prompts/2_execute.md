
**MIO FEEDBACK:**
{user_input}

## Fase ESECUTIVA
Ora sei entrato nella fase esecutiva, è MOLTO delicata, perché sei chiamato a modificare più file, perché è un'app in produzione, perché NON abbiamo a disposizione più tentativi, dev'essere one-shot e il tuo output verrà automaticamente convertito in modifiche al mio repo (i file verranno sovrascritti!).

### Procedura
* Analizza il mio feedback.
* Rivedi la tua analisi del prompt precedente.
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