### 1. Istruzioni di Installazione

Servono solo 2 requisiti: Python e Node.js (per repomix).

1.  Installa le dipendenze Python:
    ```bash
    pip install pyperclip colorama
    ```
2.  Installa Repomix globalmente (se non lo hai):
    ```bash
    npm install -g repomix
    ```

**ATTENZIONE!!!**
Se si usa il termine in VS Code serve togliere il bindings di ctrl+invio e rimandarlo al terminale sennò viene intercettato:
- Premere CTRL+SHIFT+P cercare Open Keyboard Shortcuts (JSON) 
- Aggiungere un binding mettendo la virgola all'ultima quadre e incollando sotto:
    {
    "key": "ctrl+enter",
    "command": "workbench.action.terminal.sendSequence",
    "args": { "text": "\u001b[13;5u" },
    "when": "terminalFocus"
    }

### 2. Come Funziona il Nuovo Workflow

Ecco esattamente cosa accadrà quando lo userai:

**Fase 1: Inizio Lavoro (`rep init`)**
1.  Lanci `rep init`.
2.  Ti chiederà: *"Descrivi l'obiettivo"*. Scrivi quello che vuoi, invio 2 volte.
3.  Lo script crea il pacchetto Repomix, lo unisce al tuo prompt di analisi (file `~/.rep_prompts/1_analysis.md`) e lo mette negli appunti.
4.  **Non si chiude.** Ti dice: *"Quando il chatbot ha risposto, premi INVIO per procedere allo Step 2"*.
5.  Tu vai sul chatbot, incolli. Lui ti risponde con le opzioni (A, B, C).
6.  Torni sul terminale, premi INVIO.
7.  Ti chiede: *"Inserisci il tuo feedback"*. Scrivi (es: *"Opzione B, ma cambia il colore in rosso"*).
8.  Lui prende il prompt di esecuzione (file `~/.rep_prompts/2_execute.md`), ci infila il tuo feedback e lo copia negli appunti.
9.  Incolli nel chatbot.

**Fase 2: Applicazione (`rep apply`)**
1.  Il chatbot ti sputa fuori l'XML. Copia tutto il messaggio (o clicca copy sul blocco di codice).
2.  Lanci `rep apply`.
3.  Lui legge gli appunti, trova `<changes>`, scrive i file, cancella quelli vecchi.
4.  Se nel XML c'è il tag `<shell>npm install...</shell>`, ti chiede conferma e lo esegue.

**Fase 3: Manutenzione (`rep mod` / `rep check`)**
1.  Se tocchi un file a mano e vuoi dirlo al chatbot: `rep mod`. Lui vede che l'hash del file è cambiato rispetto all'ultima volta e crea un prompt solo con quel file.
2.  Se hai errori rossi in VS Code: `rep check`. Lui fa girare `tsc` e ti copia gli errori pronti da incollare.

### Personalizzazione dei Prompt
Dopo aver lanciato `rep init` la prima volta, troverai i file markdown in `~/.rep_prompts/`.
Puoi aprirli ed editarli come vuoi. Ricorda solo di lasciare i segnaposto `{user_input}` e `{codebase}` nel file 1, e `{user_input}` nel file 2.