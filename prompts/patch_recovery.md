{failed_count} patch in modalità Snippet non hanno funzionato (match non perfetto con l'originale).

✅ **SNIPPET APPLICATI CON SUCCESSO:**
Questi snippet hanno funzionato e sono GIÀ STATI APPLICATI al codice. **NON RIGENERARLI!**
{success_list_str}

❌ **SNIPPET FALLITI (DA CORREGGERE):**
Questi snippet hanno fallito. Riscrivi SOLO le patch per questi:
{fail_list_str}

Ti fornisco di seguito il contenuto AGGIORNATO e REALE di questi file.
Per favore, riscrivi l'output per applicare le tue correzioni a questi file, rispettando le nostre regole standard (usa sempre la modalità SNIPPET).

⚠️ **ISTRUZIONI CRITICHE DI SICUREZZA - LEGGI ATTENTAMENTE:**
1. **SOURCE OF TRUTH:** Il codice riportato qui sotto è l'unica Verità Assoluta. Ignora qualsiasi versione precedente tu abbia in memoria o nel contesto.
2. **DIVIETO DI ALLUCINAZIONE:** Prima di scrivere il tag <original>, devi **trovare letteralmente** quella stringa nel testo qui sotto. Se il codice che vuoi correggere non c'è (perché magari il file è già stato fixato o è diverso da come pensavi), **NON GENERARE LA PATCH** per quel file.
3. **CHECK PREVENTIVO:** Se noti che il codice contiene già la modifica desiderata (es. il tipo TypeScript è già presente), NON toccare il file e segnalalo semplicemente nel riepilogo.
4. **COPIA BIT-PER-BIT (ATTENZIONE AGLI SPAZI):** Il contenuto di <original> deve essere un copia-incolla chirurgico. Il parser ignora solo l'indentazione e gli spazi vuoti a inizio/fine riga, ma è **intransigente su tutto il resto**: spazi interni (es. dopo `if`, dopo `:`, tra parentesi), punteggiatura e casing. Se sbagli anche solo uno spazio, il match fallisce.
5. **ERRORI COMUNI:** Uno degli errori più comuni, per tua natura, è quello di essere impreciso nel riportare gli spazi presenti o non presenti prima delle parentesi quadre "[" laddove il linguaggio di programmazione consente di mettere o omettere lo spazio. Ad esempio:
    Esempio 1:
       `const[logId, setLogId] = useState("");`
       potrebbe esser stato scritto così:
       `const [logId, setLogId] = useState("");`
    Esempio 2:
       `var = [array];`
       potrebbe esser stato scritto così:
       `var =[array];`
    porta attenzione a questi spazi che precedono sì o no, le parentesi quadre, nel file originale e replicale allo stesso modo, perché è il tuo errore più comune; quando sbagli una patch fatti una mappa mentale per ogni riga che prente una parentesi quadra (tipo: questa riga ha lo spazio prima, questa riga non ha lo spazio prima, ecc.)
6. **PATCH PRECEDENTI GIÀ ESEGUITE:** Occhio anche a questo: potresti pensare che alcune delle patch che mi hai mandato siano fallite, quando magari hanno funzionato e sono state applicate; non importa, l'unica fonte di verità ora è il codice che ti incollo qui sotto, dal quale capirai lo stato attuale dei file e su quello baserai il contenuto dal blocco `<original>`.
7. **STRATEGIA DI RESET (INVERSIONE TAG):** Per tua natura, tendi a ricopiare lo stesso blocco errato che hai generato in precedenza. Per forzare un "reset" cognitivo, inverti l'ordine di scrittura dei tag <original> e <edit>, ad esempio se questa è la prima correzione patch che fai: **scrivi PRIMA il tag `<edit>` (il nuovo codice) e DOPO il tag `<original>`**. Questo ti obbligherà a guardare il codice sorgente con occhi nuovi al momento di copiare l'originale.

Ecco i file aggiornati:
