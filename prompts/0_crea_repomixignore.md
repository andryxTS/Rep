**Contesto**
Devo mandare l'intero codebase del mio progetto a un chatbot LLM per l'analisi globale e l'effettuazione di alcune modifiche.

**Task**
Devi darmi il contenuto del file `.repomixignore`, in modo che il codebase esportato da repomix sia il più leggero possibile ma completo in ogni sua parte (tutto ciò che può servire all'analisi globale dell'llm, scartando tutto il resto che andrebbe solo ad appesantire: es. assets, package-lock, ecc.).

**Input**
Ecco i dati su cui lavorare:

1. **Global Ignore (Riferimento)**
Questo è il file di esclusione "standard" che uso per tutti i progetti. Usalo come base intoccabile.
```
{global_ignore}
```

2. **Local Ignore (Progetto Attuale)**
Questo è il file `.repomixignore` attualmente presente nella cartella del progetto.
```
{local_ignore}
```

3. **Lista File Attuale**
Questa è la lista dei file che repomix sta attualmente includendo tramite local ignore (e che forse dovremmo filtrare meglio).
```
{file_list}
```

**Eccezioni**
Sui seguenti file fai un'eccezione, mantienili nell'output di repomix se sono presenti:
docker-compose.yml
ecosystem.config.js
proxy.ts
package.json
tsconfig.json
jsconfig.json
tailwind.config.js
tailwind.config.ts
drizzle.config.ts
prisma.config.ts
next.config.js
next.config.ts
middleware.ts
.env.example

**Regole**
1. **Merge Additivo**: Parti dal **Global Ignore**. Aggiungi le regole del **Local Ignore**. Infine, aggiungi nuove regole basandoti sulla **Lista File** per escludere file inutili non ancora coperti.
2. **Nessuna sovrascrittura**: Non rimuovere regole presenti nel Global Ignore.
3. **Nessuna eccezione manuale**: Non usare la sintassi `!file`. Se un file deve essere incluso (come le eccezioni sopra), semplicemente assicurati che non ci sia una regola che lo escluda.

**Output**
Esegui la tua analisi e scrivimi:
* L'elenco dei file che hai deciso di aggiungere alle regole di esclusione.
* Il file `.repomixignore` FINALE COMPLETO (Globale + Locale + Nuove aggiunte).
* Mettimi il file per intero dentro 3 backtick.