### Formato Snippets (per piccole modifiche)
Quando scegli per alcuni file il formato snippets, per le piccole modifiche, devi includere:
1. in modo ASSOLUTAMENTE FEDELE (cruciale!) lo snippet di codice originale da sostituire, lo racchiuderai contornato tra 3 backtick dentro il tag <original>, 
2. lo snippet nuovo che andrà a sostituire l'originale, racchiuso fra 3 backtick, dentro il tag <edit>
Massima attenzione, perché il tuo output verrà elaborato automaticamente da uno script che cercherà nel file la stringa di testo indicata in <original> e la sostituirà con il testo contenuto in <edit>; ovviamente questa cosa funziona fintante che:
* Ciò che è contenuto in <original> è assolutamente FEDELE al file originale che ti ho passato in contesto. ⚠️ VINCOLO DI FEDELTÀ ESTREMA: Quando compili il tag <original>, non ricostruire il codice a memoria e non riassumere. Devi eseguire una ricerca testuale nel codebase che ti ho inviato, individuare il blocco esatto di righe e copiarlo carattere per carattere, inclusi i commenti. Se il contenuto di <original> non è identico al 100% al file sorgente, l'intera operazione fallirà. Se hai dubbi sulla versione esatta, chiedi conferma invece di ipotizzare.
* Ciò che è contenuto in <edit> è pensato per sostituire ciò che è contenuto in <original> garantendo il funzionamento del codice.
*   Usa SEMPRE `<![CDATA[ ... ]]>` per il contenuto dei file.
*   All'interno dei CDATA, racchiudi il codice del file in un blocco Markdown standard con **3 backticks** (es: ```tsx o ```css).
*   **Indentazione:** Mantieni l'indentazione perfetta dentro i 3 backticks. NON minificare.

**Esempio Snippet 1 (modifica righe):**
<snippet path="src/utils.ts">
    <original><![CDATA[
        ```
            const x = 10;
        ```
    ]]></original>
    <edit><![CDATA[
        ```
            const x = 20;
        ```
    ]]></edit>
</snippet>

**Esempio Snippet 2 (aggiunta righe):**
<snippet path="src/utils.ts">
    <original><![CDATA[
    ```
        const x = 10;
        const y = 5;
    ```
    ]]></original>
    <edit><![CDATA[
    ```
        const x = 10;
        const z = 15; // Riga aggiunta
        const y = 5;
    ```
    ]]></edit>
</snippet>

**ATTENZIONE: IL TUO OUTPUT VERRÀ RIGETTATO SE:**
* Il contenuto di <original> non matcha bit-per-bit il file sul disco (esclusi gli indent che vengono ignorati per il match).
* Cerchi di "riassumere" il codice in <original> (es. usando ... o commenti tipo // resto del codice).
* All'interno del blocco <original> cambi l'ordine di proprietà, dichiarazioni, espressioni. (se cambia l'ordine non ottengo più il match indispensabile per eseguire la patch)

**SCELTA DEL FORMATO: FULL REWRITE vs SNIPPET**
Devi scegliere il formato in base a regole rigide. Non ottimizzare per la lunghezza del tuo output, ottimizza per la sicurezza dell'esecuzione.
1.  **Formato `<file>` (FULL REWRITE):**
    *   **OBBLIGATORIO** se il file ha meno di 150 righe.
    *   **OBBLIGATORIO** se devi modificare più del 30% del file.
    *   **OBBLIGATORIO** se devi riscrivere intere funzioni o blocchi di codice lunghi (> 25 righe).
    *   *Istruzione:* Riscrivi l'intero file da cima a fondo (SII ESTREMAMENTE FEDELE AL FILE ORIGINALE bit-per-bit tranne ovviamente per le righe da modificare).
2.  **Formato `<snippet>` (SEARCH & REPLACE):**
    *   **PERMESSO SOLO** se il file è grande (> 150 righe) e la modifica è chirurgica (es. cambiare da 1 a 25 righe di codice).
    *   *Istruzione:*
        *   Dentro `<original>`: Devi copiare una porzione di codice UNICA ed ESISTENTE. **AVVISO CRITICO:** Mentre le indentazioni sono ignorate, per tutto il resto se sbagli anche solo un carattere rispetto al file sorgente, lo script di replace fallirà. Non indovinare. Copia bit-per-bit. Non usare mai `...` o commenti riassuntivi.
        *   Dentro `<edit>`: Il nuovo codice che sostituirà ESATTAMENTE il blocco `<original>` (qui invece concentrati molto sulle giuste indentazioni).
**Se violi queste regole (es. usi snippet su un file piccolo o sbagli l'original), il codice di produzione si romperà.**

### FORMATO DELL'OUTPUT: XML
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
        <original><![CDATA[
            ```
                const x = 10;
            ```
        ]]></original>
        <edit><![CDATA[
            ```
                const x = 20;
            ```
        ]]></edit>
    </snippet>
 <!-- Per i comandi a shell da eseguire: -->
    <shell>
        ```bat
            pnpm add -D new-library
        ```
    </shell>
</changes>
````