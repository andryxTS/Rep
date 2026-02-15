**Contesto**
Devo mandare l'intero codebase del mio progetto a un chatbot LLM per l'analisi globale e l'effettuazione di alcune modifiche.

**Task**
Devi darmi il contenuto del file .repomixignore, in modo che il codebase esportato da repomix sia il più leggero possibile ma completo in ogni suo parte (tutto ciò che può servire all'analisi globale dell'llm, scartando tutto il resto che andrebbe solo ad appesantire: es. assets, package-lock, ecc.).

**Riferimenti**
Come riferimento hai:

1. Il contenuto dell'attuale .repomixignore (da tenere e solo integrare)
```
(contenuto del file .repomixignore se presente nella cartella di lavoro, o se non presente del file .repomixignore nella cartella .rep_prompts)
```

2. La lista dei file che repomix attualmente mi include nel suo file di output
```
INSERIRE_QUA_ELENCO_FILE_REPOMIX_OUTPUT
```

3. Eccezioni
Sui seguenti file fai un'eccezione, mantienili nell'output di repomix se sono presenti, perché capita che a volte ho proprio problemi nel deploy, e poi preferisco dare queste informazioni in più all'LLM, d'altronde sono anche file di poche decine di righe:
docker-compose.yml
ecosystem.config.js
proxy.ts

**Output**
Esegui la tua analisi e dammi il file .repomixignore aggiornato, con tutto ciò che avevo prima (punto 1), aggiornato con tutto il resto che ritieni conveniente escludere. Mettimi il nuovo file repomixignore per intero dentro 3 backtick.