**Contesto**
Devo mandare l'intero codebase del mio progetto a un chatbot LLM per l'analisi globale e l'effettuazione di alcune modifiche.

**Task**
Devi darmi il contenuto del file .repomixignore, in modo che il codebase esportato da repomix sia il più leggero possibile ma completo in ogni suo parte (tutto ciò che può servire all'analisi globale dell'llm, scartando tutto il resto che andrebbe solo ad appesantire: es. assets, package-lock, ecc.).

**Riferimenti**
Come riferimento hai:

1. Il contenuto dell'attuale .repomixignore (da tenere e solo integrare)
```
{current_ignore}
```

2. La lista dei file che repomix attualmente mi include nel suo file di output
```
{file_list}
```

3. Eccezioni
Sui seguenti file fai un'eccezione, mantienili nell'output di repomix se sono presenti, perché capita che a volte ho proprio problemi nel deploy, e poi preferisco dare queste informazioni in più all'LLM, d'altronde sono anche file di poche decine di righe:
docker-compose.yml
ecosystem.config.js
proxy.ts

4. Non aggiungere manualmente eccezioni
Non aggiungere nel file .repomixignore eccezioni forzate, quelle con il punto esclamativo all'inizio, tipo:
!proxy.ts
L'importante è che questi file da mantenere non siano elencati nella lista di .repomixignore.

**Output**
Esegui la tua analisi e scrivimi:
* L'elenco dei file aggiunti
* Il file .repomixignore aggiornato, con tutto ciò che avevo prima (punto 1), aggiornato con tutto il resto che ritieni conveniente escludere. Mettimi il nuovo file repomixignore per intero dentro 3 backtick.
Eccezione: Se non ritieni necessarie integrazioni all'attuale .repomixignore comunicamelo e non serve alcun elenco o alcun file in output.