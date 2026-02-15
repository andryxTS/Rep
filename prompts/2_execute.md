
**MIO FEEDBACK:**
{user_input}

### Fase ESECUTIVA
Ora sei entrato nella fase esecutiva, è MOLTO delicata, perché sei chiamato a modificare più file, perché è un sito in produzione, perché NON abbiamo a disposizione più tentativi, dev'essere one-shot e il tuo output verrà automaticamente convertito in modifiche al mio repo (i file verranno sovrascritti!).

**Procedura**
* Analizza il mio feedback.
* Rivedi la tua analisi del prompt precedente.
* Pianifica le operazioni che dovrai eseguire, cura ogni dettaglio.
* Scrivi questo piano in chiaro, prima di cominciare il lavoro di coding.
* VINCOLO DI ESISTENZA DEI PATH: Prima di generare un <file> o uno <snippet>, devi obbligatoriamente verificare che il path esista esattamente come elencato nella sezione 'Directory Structure' o all'interno dei tag <file path="..."> del file repomix-output.xml fornito. Non inventare percorsi basandoti su convenzioni (es. non assumere /components/ui/ se il file è in /components/). Se un file non esiste nel contesto, non tentare di modificarlo.
* Scrivi un piccolo riepilogo testuale con i file che dovrai modificare/aggiungere/eliminare [EDIT] / [NEW] / [DELETE]; per ognuno di questi, prima di scriverlo, verifica che il path e file esistano realmente, come suggerito al punto precedente.
* Scrivi il nuovo codice per le pagine modificate o nuove, PER INTERO (salvo uso snippets), nel formato XML specificato sotto, **modifica solo quanto necessario** e **mantieni intatto il resto, compresi i commenti, LA FEDELTÀ ESTREMA È RICHIESTA E CRUCIALE**).
* Puoi usare il formato "snippets" solo quando le modifiche sono su file con più di 200 righe e in cui le modifiche da fare sono su meno di 1/4 delle righe totali di quel file.

**Formato Snippets (per piccole modifiche)**
Quando scegli per alcuni file il formato snippets, per le piccole modifiche, devi includere:
1. in modo ASSOLUTAMENTE FEDELE (cruciale!) lo snippet di codice originale da sostituire, lo racchiuderai contornato tra 3 backtick dentro il tag <original>, 
2. lo snippet nuovo che andrà a sostituire l'originale, racchiuso fra 3 backtick, dentro il tag <edit>
Massima attenzione, perché il tuo output verrà elaborato automaticamente da uno script che cercherà nel file la stringa di testo indicata in <original> e la sostituirà con il testo contenuto in <edit>; ovviamente questa cosa funziona fintante che:
* Ciò che è contenuto in <original> è assolutamente FEDELE al file originale che ti ho passato in contesto. ⚠️ VINCOLO DI FEDELTÀ ESTREMA: Quando compili il tag <original>, non ricostruire il codice a memoria e non riassumere. Devi eseguire una ricerca testuale nel codebase che ti ho inviato, individuare il blocco esatto di righe e copiarlo carattere per carattere, inclusi spazi, tabulazioni e commenti. Se il contenuto di <original> non è identico al 100% al file sorgente, l'intera operazione fallirà. Se hai dubbi sulla versione esatta, chiedi conferma invece di ipotizzare.
* Ciò che è contenuto in <edit> è pensato per sostituire ciò che è contenuto in <original> garantendo il funzionamento del codice.
* L'indentazione è tenuta in seria considerazione.

**Esempio Snippet 1 (modifica righe):**
<snippet path="src/utils.ts">
    <original>
        ```
            const x = 10;
        ```
    </original>
    <edit>
        ```
            const x = 20;
        ```
    </edit>
</snippet>

**Esempio Snippet 2 (aggiunta righe):**
<snippet path="src/utils.ts">
    <original>
    ```
        const x = 10;
        const y = 5;
    ```
    </original>
    <edit>
    ```
        const x = 10;
        const z = 15; // Riga aggiunta
        const y = 5;
    ```
    </edit>
</snippet>

**FORMATO DELL'OUTPUT: XML**
1.  **STRUTTURA:** Usa il tag radice `<changes>`.
    *   `<file path="path/to/file">` per file creati o riscritti interamente.
    *   `<snippet path="path/to/file">` per modifiche mirate (Search & Replace).
        *   Dentro snippet usa `<original>` (codice da cercare) e `<edit>` (codice da sostituire).
    *   `<delete_file path="path/to/file" />` per file eliminati.
    *   `<shell>` comandi da eseguire nel terminale (es. pnpm install) `</shell>`
2.  **WRAPPER ESTERNO:** Restituisci l'intero output XML racchiuso in un unico blocco Markdown con **4 backticks** (````xml).
3.  **CONTENUTO CODICE:**
    *   Usa SEMPRE `<![CDATA[ ... ]]>` per il contenuto dei file.
    *   All'interno dei CDATA, racchiudi il codice del file in un blocco Markdown standard con **3 backticks** (es: ```tsx o ```css).
    *   **Indentazione:** Mantieni l'indentazione perfetta dentro i 3 backticks. NON minificare.
4.  **SINTASSI:** Fai estrema attenzione all'escape dei caratteri speciali (es. apostrofi) nelle stringhe TSX. Usa template strings o entità HTML se necessario.

**Esempio Esatto di Output XML:**

````xml
<changes>
 <!-- Ripeti per ogni file aggiunto/modificato: -->
  <file path="src/components/ExampleTemplate.tsx"><![CDATA[
```tsx
import { Button } from "@/components/ui/button"

export interface ExampleProps {
  title: string;
}

export default function ExampleTemplate({ title }: ExampleProps) {
  return (
    <div className="p-4">
      <h1>{title}</h1>
      <p>L&apos;arte del taglio</p> {/* Nota l'escape dell'apostrofo */}
    </div>
  )
}
// [CODICE COMPLETO PRESERVANDO ESATTAMENTE L'ORIGINALE CON MODIFICHE SOLO SULLA PARTE DA MODIFICARE]
```
  ]]></file>
 <!-- Se devi cancellare file: -->
  <delete_file path="src/app/old_file.ts" />
 <!-- Se devi modificare solo dei piccoli snippet: -->
    <snippet path="src/utils.ts">
        <original>
            ```tsx
                const x = 10;
            ```
        </original>
        <edit>
            ```tsx
                const x = 20;
            ```
        </edit>
    </snippet>
 <!-- Per i comandi a shell da eseguire: -->
    <shell>
        ```bat
            pnpm add -D new-library
        ```
    </shell>
</changes>
````

