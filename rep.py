#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import xml.etree.ElementTree as ET
import pyperclip
import json
import hashlib
import re
import shutil
import platform
import re
import fnmatch
import shutil
from colorama import init, Fore, Style

# --- GESTIONE DIPENDENZE OPZIONALI ---
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.key_binding import KeyBindings
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

# Inizializza colorama
init(autoreset=True)

# --- CONFIGURAZIONE ---
STATE_FILE = ".rep_state.json"
REPOMIX_IGNORE = ".repomixignore"
TEMP_DIR = ".rep_temp"  # Nuova cartella temporanea
REPOMIX_OUTPUT_FILENAME = "repomix-output.txt"
PROMPT_FILENAME = "PROMPT.md"

# PROMPTS_DIR = os.path.expanduser("~/.rep_prompts")  // SOSTITUITO, COSÌ GIT MI TRACCIA I PROMPT
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
PROMPT_CREA_REPOMIXIGNORE = os.path.join(PROMPTS_DIR, "0_crea_repomixignore.md")
PROMPT_ANALYSIS_FILE = os.path.join(PROMPTS_DIR, "1_analysis.md")
PROMPT_EXECUTE_FILE = os.path.join(PROMPTS_DIR, "2_execute.md")
PROMPT_NEW_SESSION_FILE = os.path.join(PROMPTS_DIR, "3_new_session.md") 
PROMPT_FORMATO_OUTPUT = os.path.join(PROMPTS_DIR, "formato_output.md") 
GLOBAL_IGNORE_FILE = os.path.join(PROMPTS_DIR, ".repomixignore")

# --- PROMPT DEFAULT (Aggiornati per gestione allegati) ---
DEFAULT_ANALYSIS_PROMPT = """
**MODIFICHE RICHIESTE:**
{user_input}

**Input:**
In allegato a questo messaggio trovi due file:
1. `repomix-output.txt`: L'intero codebase del progetto.
2. Questo file `PROMPT.md` con le istruzioni.

**Task:**
Ti chiederò di effettuare alcune modifiche al mio codebase. Per adesso farai un'analisi e aspetterei il mio feedback. In una seconda fase futura procederai con il coding.

**PROCEDURA**
* Analizza il codebase, capendo: architettura, approccio, stile, flusso dei dati.
* Leggi le modifiche che ti propongo, pensa ad un piano su come applicarle; ci saranno probabilmente da prendere delle decisioni: voglio essere coinvolto in queste decisioni.
* Chiedimi il feedback riguardo alle scelte da fare presentandomele come elenco numerato con più opzioni (es. A, B, C...).
* Aspetta il mio feedback e le nuove istruzioni operative su come proseguire con il lavoro di coding vero e proprio.

**BEST PRACTICE**
* Best-practice: il lavoro dovrà essere eseguito secondo le best-practice per il framework in questione.
* Practice del mio repo: Adattati all'approccio che vedi utilizzato nel mio repo anche se non standard, previa mia approvazione.
* Dati dinamici: Evita contenuti hardcoded per dati da CMS.
* initialValue: se aggiungi campi a Sanity, includi sempre un initialValue.
"""

DEFAULT_EXECUTE_PROMPT = """
**MIO FEEDBACK:**
{user_input}

### Fase ESECUTIVA
Ora sei entrato nella fase esecutiva. Modifica i file necessari.

**Procedura**
* Analizza il mio feedback.
* Rivedi la tua analisi.
* Pianifica le operazioni che dovrai eseguire, cura ogni dettaglio.
* Scrivi questo piano in chiaro, prima di cominciare il lavoro di coding.
* VINCOLO DI ESISTENZA DEI PATH: Prima di generare un <file> o uno <snippet>, devi obbligatoriamente verificare che il path esista esattamente come elencato nella sezione 'Directory Structure' o all'interno dei tag <file path="..."> del file repomix-output.txt fornito. Non inventare percorsi basandoti su convenzioni (es. non assumere /components/ui/ se il file è in /components/). Se un file non esiste nel contesto, non tentare di modificarlo.
* Scrivi un piccolo riepilogo testuale con i file che dovrai modificare/aggiungere/eliminare [EDIT] / [NEW] / [DELETE]; per ognuno di questi, prima di scriverlo, verifica che il path e file esistano realmente, come suggerito al punto precedente.
* Scrivi il nuovo codice per le pagine modificate o nuove, PER INTERO (salvo uso snippets), nel formato XML specificato sotto, **modifica solo quanto necessario** e **mantieni intatto il resto, compresi i commenti, LA FEDELTÀ ESTREMA È RICHIESTA E CRUCIALE**).
* Dichiarazione Strategia: Nel tuo riepilogo testuale, per ogni file devi scrivere esplicitamente: "File: [nome], Righe stimate: [N], Strategia: [FULL REWRITE / SNIPPET]". Se scrivi "SNIPPET" per un file piccolo, l'operazione sarà considerata un errore.

{formato_output}
"""

DEFAULT_NEW_SESSION_PROMPT = """
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

{formato_output}
"""

DEFAULT_FORMATO_OUTPUT = """
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
"""

# --- UTILS SISTEMA ---

def print_step(msg): print(f"\n{Fore.CYAN}➤ {msg}{Style.RESET_ALL}")
def print_success(msg): print(f"{Fore.GREEN}✔ {msg}{Style.RESET_ALL}")
def print_error(msg): print(f"{Fore.RED}✘ {msg}{Style.RESET_ALL}")
def print_warn(msg): print(f"{Fore.YELLOW}⚠ {msg}{Style.RESET_ALL}")

def run_command(command, capture=True):
    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=capture,
            encoding='utf-8', errors='replace'
        )
        return result.stdout.strip() if capture else ""
    except Exception as e:
        print_error(f"Errore cmd '{command}': {e}")
        return None

def copy_files_to_clipboard_os(file_paths):
    """Tenta di copiare i file negli appunti a livello di sistema operativo"""
    abs_paths = [os.path.abspath(p) for p in file_paths]
    system = platform.system()
    
    try:
        if system == "Windows":
            # Usa PowerShell per settare i file nella clipboard
            file_list = ",".join([f"'{p}'" for p in abs_paths])
            cmd = f"powershell -command \"Set-Clipboard -Path {file_list}\""
            subprocess.run(cmd, shell=True, check=True)
            return True
        elif system == "Darwin": # Mac
            # Usa AppleScript
            # Formato: set the clipboard to { POSIX file "/path/1", POSIX file "/path/2" }
            file_list = ", ".join([f'POSIX file "{p}"' for p in abs_paths])
            script = f'tell app "Finder" to set the clipboard to {{ {file_list} }}'
            subprocess.run(["osascript", "-e", script], check=True)
            return True
        elif system == "Linux":
            # Linux è complicato (xclip/xsel gestiscono testo). 
            # Aprire la cartella è meglio.
            return False
    except Exception as e:
        print_warn(f"Copia file fallita ({e}). Apro la cartella invece.")
        return False
    return False

def open_folder(path):
    """Apre la cartella nel file manager di sistema"""
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

def ensure_prompts_exist():
    if not os.path.exists(PROMPTS_DIR): os.makedirs(PROMPTS_DIR)
    
    # Sovrascrive Analysis se vecchio (per rimuovere placeholder {codebase})
    # OCCHIO: Se hai modificato molto i tuoi prompt, controlla questo passaggio.
    # Qui creo se non esistono.
    if not os.path.exists(PROMPT_ANALYSIS_FILE):
        with open(PROMPT_ANALYSIS_FILE, "w", encoding="utf-8") as f: f.write(DEFAULT_ANALYSIS_PROMPT)
    
    if not os.path.exists(PROMPT_EXECUTE_FILE):
        with open(PROMPT_EXECUTE_FILE, "w", encoding="utf-8") as f: f.write(DEFAULT_EXECUTE_PROMPT)

    if not os.path.exists(PROMPT_NEW_SESSION_FILE):
        with open(PROMPT_NEW_SESSION_FILE, "w", encoding="utf-8") as f: f.write(DEFAULT_NEW_SESSION_PROMPT)

    if not os.path.exists(PROMPT_FORMATO_OUTPUT):
        with open(PROMPT_FORMATO_OUTPUT, "w", encoding="utf-8") as f: f.write(DEFAULT_FORMATO_OUTPUT)

def get_multiline_input(prompt_text):
    print(f"\n{Fore.YELLOW}{prompt_text}{Style.RESET_ALL}")

    if HAS_PROMPT_TOOLKIT:
        # --- CONFIGURAZIONE AVANZATA ---
        kb = KeyBindings()

        # 1. Tasto INVIO -> Inserisce una nuova riga (non invia)
        @kb.add('enter')
        def _(event):
            event.current_buffer.insert_text('\n')

        # 2. CTRL+INVIO -> invia
        # 'escape','[','1','3',';','5','u' = sequenza VSCode integrato + Windows Terminal (Win11)
        # 'c-j' = fallback per VSCode vecchi / terminale classico Windows
        @kb.add('escape', '[', '1', '3', ';', '5', 'u')
        @kb.add('c-j')
        def _(event):
            event.current_buffer.validate_and_handle()

        print(f"{Style.DIM}(Scrivi il messaggio. Premi {Fore.CYAN}CTRL+INVIO{Style.RESET_ALL}{Style.DIM} per inviare){Style.RESET_ALL}")        
        session = PromptSession(key_bindings=kb, multiline=True)
        return session.prompt("> ")

    else:
        # Fallback se manca la libreria
        print(f"{Fore.RED}⚠ Per input avanzato installa: pip install prompt_toolkit{Style.RESET_ALL}")
        print(f"{Style.DIM}(Scrivi 'END' su una riga vuota e premi Invio per terminare){Style.RESET_ALL}")
        lines = []
        while True:
            line = input()
            if line.strip() == "END": break
            lines.append(line)
        return "\n".join(lines)
            
def clean_code_content(content):
    if not content: return ""
    content = content.strip() # Questo pulisce FUORI dai backtick (sicuro)
    pattern = r"^```[a-zA-Z0-9]*\n?(.*?)```$"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        # rstrip() rimuove spazi/invii SOLO dalla fine della stringa
        # preservando l'indentazione iniziale
        return match.group(1).rstrip()
    return content

# --- CORE FUNCTIONS ---

def cmd_init(auto_input=None):
    ensure_prompts_exist()

    # --- Controllo presenza RepomixIgnore ---
    trigger_ignore = False
    local_lines = 0
    global_lines = 0
    
    # Conta righe significative file locale
    if os.path.exists(REPOMIX_IGNORE):
        with open(REPOMIX_IGNORE, 'r', encoding='utf-8', errors='ignore') as f:
            local_lines = len([l for l in f if l.strip()])
    else:
        print_warn(f"File {REPOMIX_IGNORE} mancante.")
        trigger_ignore = True

    # Conta righe significative file globale (se esiste) e confronta
    if not trigger_ignore and os.path.exists(GLOBAL_IGNORE_FILE):
        with open(GLOBAL_IGNORE_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            global_lines = len([l for l in f if l.strip()])
        
        if local_lines < global_lines:
            print()
            print_warn(f"Il tuo {REPOMIX_IGNORE} ({local_lines} righe) sembra meno completo del globale ({global_lines} righe).")
            trigger_ignore = True

    if trigger_ignore:
        # Se c'è auto_input (modalità automatica), saltiamo il blocco interattivo dell'ignore per non interrompere il flusso
        if not auto_input:
            input("PREMERE un tasto qualsiasi per procedere con l'ottimizzazione di Repomix tramite chatbot...")
            cmd_ignore()
            print("\n" + "="*40 + "\n")
            print_step("Riprendo l'inizializzazione del progetto...")
        else:
            print_warn("Ignoro ottimizzazione .repomixignore per flusso automatico.")
    # --------------------------------------
    
    # 1. Preparazione Temp
    if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)
    
    repomix_path = os.path.join(TEMP_DIR, REPOMIX_OUTPUT_FILENAME)
    prompt_path = os.path.join(TEMP_DIR, PROMPT_FILENAME)

    # 2. Esecuzione Repomix
    print_step("Esecuzione Repomix (Output su file)...")
    if not os.path.exists(REPOMIX_IGNORE):
        with open(REPOMIX_IGNORE, "w") as f:
            f.write("node_modules/**\n.git/**\n.next/**\ndist/**\nbuild/**\npackage-lock.json\npnpm-lock.yaml\n**/*.pyc")
    
    # Output diretto nel file temporaneo
    cmd = f"repomix . --style xml --output {repomix_path}"
    run_command(cmd, capture=False) # Mostra log a video

    if not os.path.exists(repomix_path):
        print_error("Repomix fallito. File non creato.")
        return

    # 3. Input Utente e Creazione Prompt File
    if auto_input:
        user_input = auto_input
        print_step("Input acquisito automaticamente dal report errori.")
    else:
        user_input = get_multiline_input("Descrivi l'obiettivo delle modifiche")
    
    with open(PROMPT_ANALYSIS_FILE, "r", encoding="utf-8") as f: template = f.read()
    
    # Gestione intelligente del placeholder {codebase}
    final_prompt = template.replace("{user_input}", user_input)
    if "{codebase}" in final_prompt:
        final_prompt = final_prompt.replace("{codebase}", "[VEDI FILE ALLEGATO: repomix-output.txt]")
    
    with open(prompt_path, "w", encoding="utf-8") as f: f.write(final_prompt)
    print_success(f"File creato: {prompt_path}")

    # 4. Copia negli Appunti / Apertura Cartella
    files_to_copy = [prompt_path, repomix_path]
    copied = copy_files_to_clipboard_os(files_to_copy)
    
    print_step("--- PRONTO PER IL CHATBOT ---")
    if copied:
        print_success("✅ I 2 file (PROMPT.md e XML) sono stati copiati negli appunti!")
        print("👉 1. Vai nella chat e premi CTRL+V (Incolla).")
    else:
        print_warn("Impossibile copiare i file automaticamente.")
        open_folder(TEMP_DIR)
        print("👉 Ho aperto la cartella. Seleziona i 2 file e trascinali nella chat.")

    # 5. Attesa Feedback
    msg = "👉 2. Inserisci il feedback dal chatbot (lascia vuoto per default):"
    feedback_input = get_multiline_input(msg).strip()
    
    if not feedback_input:
        feedback_input = "Fai tu in autonomia le scelte che ritieni più opportune, mi fido."

    # 6. Pulizia Temp e Step 2
    if os.path.exists(TEMP_DIR): 
        shutil.rmtree(TEMP_DIR)
        print_step("Cartella temporanea pulita.")
    
    # Legge il file con le regole di formattazione
    formato_output_content = ""
    if os.path.exists(PROMPT_FORMATO_OUTPUT):
        with open(PROMPT_FORMATO_OUTPUT, "r", encoding="utf-8") as f: 
            formato_output_content = f.read()
    else:
        print_warn(f"File {PROMPT_FORMATO_OUTPUT} non trovato, il placeholder rimarrà vuoto.")

    with open(PROMPT_EXECUTE_FILE, "r", encoding="utf-8") as f: template = f.read()
    
    # Sostituisce sia l'input utente che il formato output
    final_exec_prompt = template.replace("{user_input}", feedback_input).replace("{formato_output}", formato_output_content)
    
    pyperclip.copy(final_exec_prompt)
    save_state()
    print_success("✅ Prompt di ESECUZIONE (testo) copiato negli appunti!\n")

    print("👉 1. Vai nella chat e premi CTRL+V, quindi invia il prompt.")
    print(f"{Fore.YELLOW}👉 2. Quando hai ricevuto l'XML di risposta, COPIALO e premi INVIO qui per applicarlo.{Style.RESET_ALL}")
    input()
    cmd_apply()

def apply_snippet(file_path, original_block, edit_block):
    if not os.path.exists(file_path): return False
    with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
    if original_block.strip() in content:
        new_content = content.replace(original_block.strip(), edit_block.strip())
        with open(file_path, 'w', encoding='utf-8') as f: f.write(new_content)
        print_success(f"[Snippet] Applicato: {file_path}")
        return True
    return False

def normalize_line(line):
    """
    Pulisce una riga per il confronto 'fuzzy':
    - Rimuove spazi a inizio/fine.
    - Rimuove commenti (// o #).
    - Riduce spazi multipli interni a uno solo.
    Restituisce None se la riga diventa vuota dopo la pulizia.
    """
    # Rimuove whitespace laterali
    line = line.strip()
    
    # Rimuove i commenti (gestione base per python/js/jsonc)
    if line.startswith('//') or line.startswith('#'):
        return None
        
    # Se la riga è vuota, la ignoriamo
    if not line:
        return None
        
    # Normalizza gli spazi interni (es. "def  func" diventa "def func")
    return re.sub(r'\s+', ' ', line)

def apply_snippet_fuzzy(file_path, original_block, edit_block):
    if not os.path.exists(file_path):
        print_warn(f"[Snippet] File non trovato: {file_path}")
        return False

    # 1. Leggiamo il file originale preservando tutto
    with open(file_path, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()

    # 2. Creiamo la mappa "Searchable" del file
    # Ogni elemento è una tupla: (indice_reale_nel_file, contenuto_normalizzato)
    file_map = []
    for idx, line in enumerate(original_lines):
        norm = normalize_line(line)
        if norm:
            file_map.append((idx, norm))

    # 3. Creiamo la sequenza "Target" dallo snippet originale
    # Qui ci serve solo il contenuto normalizzato
    target_sequence = []
    for line in original_block.splitlines():
        norm = normalize_line(line)
        if norm:
            target_sequence.append(norm)

    if not target_sequence:
        print_warn(f"Lo snippet originale conteneva solo commenti o spazi vuoti.")
        return False

    # 4. Algoritmo di ricerca della sequenza (Sliding Window)
    match_found = False
    start_real_index = -1
    end_real_index = -1
    
    # Cerchiamo la sequenza target dentro la mappa del file
    n_file = len(file_map)
    n_target = len(target_sequence)

    for i in range(n_file - n_target + 1):
        # Estraiamo una "finestra" di righe normalizzate dal file
        window = [item[1] for item in file_map[i : i + n_target]]
        
        # Confrontiamo con lo snippet cercato
        if window == target_sequence:
            # TROVATO!
            # Recuperiamo gli indici reali dal primo e dall'ultimo elemento del match
            start_real_index = file_map[i][0]
            end_real_index = file_map[i + n_target - 1][0]
            match_found = True
            break

    if match_found:
        # 1. Recuperiamo l'indentazione originale della prima riga
        first_orig_line = original_lines[start_real_index]
        indent_match = re.match(r"^\s*", first_orig_line)
        original_indent = indent_match.group(0) if indent_match else ""

        # 2. Pulizia: togliamo invii/spazi SOLO in coda e invii in testa
        # Ma NON facciamo lo strip degli spazi in testa per non distruggere tutto
        clean_edit = edit_block.lstrip('\r\n').rstrip()
        edit_lines = clean_edit.splitlines()

        if edit_lines:
            # 3. Applichiamo l'indentazione originale alla prima riga
            edit_lines[0] = original_indent + edit_lines[0].lstrip()
            
            # 4. Ricostruiamo il segmento. 
            # Aggiungiamo \n a tutte le righe tranne l'ultima del blocco.
            new_segment = [line + '\n' for line in edit_lines[:-1]]
            
            # 5. Gestione dell'ultima riga del blocco
            last_line_content = edit_lines[-1]
            # Se la riga originale che stiamo sostituendo aveva un \n, lo rimettiamo
            if original_lines[end_real_index].endswith('\n'):
                new_segment.append(last_line_content + '\n')
            else:
                new_segment.append(last_line_content)

        # 6. Sostituzione effettiva
        original_lines[start_real_index : end_real_index + 1] = new_segment

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(original_lines)
            
        print(f"✅ Snippet applicato a: {file_path}")
        return True
    
    else:
        print_warn(f"Lo snippet originale non coincide: {file_path}")

    return False

# --- HELPER PER GESTIONE IGNORE ---

def load_ignore_patterns():
    """Carica i pattern da GLOBAL_IGNORE_FILE e REPOMIX_IGNORE locale."""
    patterns = set() # Set per evitare duplicati
    
    # 1. Pattern di sistema hardcoded (sempre ignorati)
    patterns.add(".rep_temp")
    patterns.add(".git")
    patterns.add(STATE_FILE) # Ignoriamo il file di stato stesso
    
    files_to_read = []
    
    # Aggiunge file globale se esiste
    if os.path.exists(GLOBAL_IGNORE_FILE):
        files_to_read.append(GLOBAL_IGNORE_FILE)
        
    # Aggiunge file locale se esiste
    if os.path.exists(REPOMIX_IGNORE):
        files_to_read.append(REPOMIX_IGNORE)
        
    for file_path in files_to_read:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Ignora righe vuote e commenti
                    if line and not line.startswith('#'):
                        patterns.add(line)
        except Exception as e:
            print_warn(f"Impossibile leggere ignore file {file_path}: {e}")
            
    return list(patterns)

def is_ignored(path, patterns):
    """Controlla se un path deve essere ignorato basandosi sui pattern."""
    # Normalizza path (rimuove ./ iniziale e uniforma separatori)
    path = os.path.normpath(path)
    if path.startswith("." + os.sep):
        path = path[2:]
    
    name = os.path.basename(path)
    
    for pattern in patterns:
        # Rimuove slash finali dai pattern (es. "dist/")
        clean_pattern = pattern.rstrip("/")
        clean_pattern = clean_pattern.rstrip(os.sep)
        
        # 1. Match sul nome esatto o wildcard (es. "node_modules", "*.pyc")
        if fnmatch.fnmatch(name, clean_pattern):
            return True
            
        # 2. Match sul percorso completo relativo (es. "src/temp/*")
        if fnmatch.fnmatch(path, clean_pattern):
            return True
        
        # 3. Match se il pattern è una directory genitore del path attuale
        # Es: pattern="dist", path="dist/css/style.css" -> deve ignorare
        if path.startswith(clean_pattern + os.sep):
            return True

    return False

# --- FUNZIONE AGGIORNATA ---

def get_file_hashes():
    hashes = {}
    patterns = load_ignore_patterns()
    
    for root, dirs, files in os.walk("."):
        # OTTIMIZZAZIONE: Modifica 'dirs' in-place per impedire a os.walk 
        # di scendere nelle cartelle ignorate (es. node_modules).
        # Questo velocizza enormemente lo script.
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), patterns)]
        
        # Controllo se la root corrente è ignorata (doppio check)
        if is_ignored(root, patterns):
            continue

        for file in files:
            file_path = os.path.join(root, file)
            
            # Se il file non è ignorato, calcola l'hash
            if not is_ignored(file_path, patterns):
                try:
                    with open(file_path, "rb") as f: 
                        hashes[file_path] = hashlib.md5(f.read()).hexdigest()
                except: pass
    return hashes

def save_state():
    with open(STATE_FILE, "w") as f: json.dump(get_file_hashes(), f)

def cmd_apply():
    print_step("Analisi Clipboard XML...")
    raw_content = pyperclip.paste()
    match = re.search(r'<changes>(.*?)</changes>', raw_content, re.DOTALL)
    if not match: return print_error("Nessun tag <changes> trovato.")
    
    try: root = ET.fromstring(f"<changes>{match.group(1)}</changes>")
    except ET.ParseError as e: return print_error(f"Errore XML: {e}")

    changes_count = 0
    shell_commands = []
    failed_snippets = []

    for file_node in root.findall('file'):
        path = file_node.get('path')
        content = clean_code_content(file_node.text or "")
        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        print_success(f"[FILE] Scritto: {path}")
        changes_count += 1

    for snippet in root.findall('snippet'):
        path = snippet.get('path')
        # Gestione sicura dei nodi figlio
        original_node = snippet.find('original')
        edit_node = snippet.find('edit')
        
        original_text = clean_code_content(original_node.text) if original_node is not None else ""
        edit_text = clean_code_content(edit_node.text) if edit_node is not None else ""

        # Tenta l'applicazione
        if apply_snippet_fuzzy(path, original_text, edit_text):
            changes_count += 1
        else:
            failed_snippets.append(path)

    for del_node in root.findall('delete_file'):
        path = del_node.get('path')
        if os.path.exists(path):
            os.remove(path)
            print_warn(f"[DEL] Eliminato: {path}")
            changes_count += 1
            
    shell_node = root.find('shell')
    if shell_node is not None: shell_commands.append(shell_node.text.strip())

    save_state()
    
    
    if shell_commands:
        print(f"\n{Fore.YELLOW}Comandi shell suggeriti:{Style.RESET_ALL}")
        for cmd in shell_commands: print(f"> {cmd}")
        if input("\nEseguire? (y/n): ").lower() == 'y':
            for cmd in shell_commands: run_command(cmd, capture=False)

    # NUOVO: Gestione fallimenti e generazione prompt di ripristino
    if failed_snippets:
        print_error(f"\nAttenzione: {len(failed_snippets)} snippet non sono stati applicati.")
        # Formatta la lista dei file per il prompt
        file_list_str = "\n".join([f"- {f}" for f in failed_snippets])
        recovery_prompt = f"""Le seguenti patch in modalità Snippet non hanno funzionato (match non perfetto con l'originale), perciò ti chiedo per questi file di riscrivermi l'output, questa volta usando la modalità FULL REWRITE; attenzione doppia alla fedeltà con i file originali: 
            {file_list_str}"""
        pyperclip.copy(recovery_prompt)
        print_success("✅ Prompt di ripristino copiato negli appunti!\n")
        print("👉 1. Incolla il prompt nella chat per far correggere all'LLM i file rimanenti.")
        print("👉 2. Poi COPIA la sua risposta qui e premi INVIO.")
        input()
        cmd_apply()
    else:
        print_success("Tutte le modifiche sono state applicate con successo.")

def cmd_mod(auto_input=None):
    old_hashes = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f: old_hashes = json.load(f)
    
    current = get_file_hashes()
    modified = [p for p, h in current.items() if p not in old_hashes or old_hashes[p] != h]
    
    if not modified: 
        print_success("Nessuna modifica locale rilevata.")
        return False # Segnala che non è stato fatto nulla
    
    print_warn(f"{len(modified)} file modificati localmente.")
    
    # Gestione input automatico o manuale
    if auto_input:
        req = auto_input
        print_step("Input acquisito automaticamente dal report errori.")
    else:
        req = get_multiline_input("Richiesta:")

    xml = "<modified_files>\n" + "".join([f' <file path="{p}"><![CDATA[\n{open(p,"r",encoding="utf-8").read()}\n]]></file>\n' for p in modified]) + "</modified_files>"
    
    pyperclip.copy(f"{req}\n\n[ATTENZIONE, avviso automatico di sistema: dall'ultimo aggiornamento sono stati modificati alcuni file, che verranno riportati qui sotto e verranno considerati la nuova versione di riferimento:]\n```{xml}```")
    print_success("Prompt con file modificati copiato negli appunti.")
    save_state()
    return True

def cmd_check():
    # --- 1. RICERCA TSC LOCALE ---
    local_tsc_unix = os.path.join("node_modules", ".bin", "tsc")
    local_tsc_win = os.path.join("node_modules", ".bin", "tsc.cmd")
    
    def get_local_tsc():
        if os.path.exists(local_tsc_unix): return local_tsc_unix
        if os.path.exists(local_tsc_win): return local_tsc_win
        return None

    tsc_path = get_local_tsc()

    # --- 2. MENU INSTALLAZIONE (Se necessario) ---
    if not tsc_path:
        print_warn("TypeScript locale non trovato (node_modules mancante?).")
        print(f"{Fore.YELLOW}Senza dipendenze, l'analisi genererà molti falsi positivi.{Style.RESET_ALL}")
        print("\nVuoi installare le dipendenze ora?")
        print(f"{Fore.CYAN}1) pnpm install (Default){Style.RESET_ALL}")
        print(f"{Fore.CYAN}2) npm install{Style.RESET_ALL}")
        print(f"{Fore.CYAN}3) Salta (Usa tsc globale se presente){Style.RESET_ALL}")
        
        choice = input(f"\nScelta [1]: ").strip()
        
        install_cmd = None
        if choice == "" or choice == "1":
            install_cmd = "pnpm install"
        elif choice == "2":
            install_cmd = "npm install"
        
        if install_cmd:
            print_step(f"Eseguo: {install_cmd} ...")
            try:
                subprocess.run(install_cmd, shell=True, check=True)
                print_success("Installazione completata.")
                # Riprova a cercare tsc locale dopo l'installazione
                tsc_path = get_local_tsc()
                if tsc_path:
                    print_success(f"Trovato tsc locale: {tsc_path}")
            except Exception as e:
                print_error(f"Errore durante l'installazione: {e}")
                print_warn("Proseguo con il controllo usando le risorse disponibili...")

    # --- 3. FALLBACK SU GLOBALE ---
    if not tsc_path:
        if shutil.which("tsc"):
            tsc_path = "tsc"
            print_warn("Uso tsc globale.")
        else:
            print_error("Non ho trovato né tsc locale né globale.")
            print("Per favore installa TypeScript o le dipendenze del progetto.")
            return

    # --- 4. ESECUZIONE ANALISI ---
    print_step("Analisi TypeScript in corso...")

    # --noEmit: solo check
    # --skipLibCheck: ignora errori dentro le librerie (fondamentale)
    # --pretty false: formato facile da leggere per python
    cmd = f'"{tsc_path}" --noEmit --skipLibCheck --incremental --pretty false'

    try:
        # Timeout 60s
        result = subprocess.run(
            cmd, shell=True, check=False, text=True, capture_output=True, encoding='utf-8', errors='replace', timeout=60
        )
    except subprocess.TimeoutExpired:
        return print_error("Timeout: il controllo ci sta mettendo troppo.")
    
    if result.returncode == 0:
        return print_success("✅ Nessun errore TypeScript rilevato.")

    # --- 5. FILTRO E REPORT ---
    raw_output = result.stdout + "\n" + result.stderr
    lines = raw_output.splitlines()
    
    filtered_errors = []
    missing_modules_count = 0
    patterns = load_ignore_patterns()
    
    # Regex per catturare "path/to/file.ts(10,20): error TSxxxx: ..."
    error_pattern = re.compile(r'^([^\s(].+?)\(\d+,\d+\):\s+error\s+(TS\d+):(.+)')

    for line in lines:
        line = line.strip()
        match = error_pattern.match(line)
        
        if match:
            file_path = match.group(1)
            error_code = match.group(2)
            
            # A. FILTRO IGNORE
            if is_ignored(file_path, patterns):
                continue
            
            # B. FILTRO RUMORE
            if error_code in ["TS2307", "TS7026", "TS2580"]:
                missing_modules_count += 1
                continue 

            filtered_errors.append(line)

    # REPORT FINALE
    if missing_modules_count > 0:
        print_warn(f"Nascosti {missing_modules_count} errori di configurazione (tipi mancanti).")

    if not filtered_errors:
        print_success("✅ Nessun errore logico trovato nei file sorgente.")
    else:
        # Costruzione del prompt per LLM (Testo aggiornato come richiesto)
        ts_report = "\n".join(filtered_errors)
        prompt_message = (
            "Ho eseguito un controllo del typescript con tsc e ho ottenuto questi errori:\n"
            f"```typescript\n{ts_report}\n```\n\n"
            "Proponimi delle soluzioni, chiedimi prima il feedback se c'è da prendere delle decisioni, "
            "e nell'eseguire le correzioni effettive usa il formato di output XML già concordato."
        )

        print_error(f"❌ Trovati {len(filtered_errors)} errori logici nel codice sorgente.")
        print("\nAnteprima:")
        for err in filtered_errors[:5]:
            print(f"  {Fore.RED}• {err}{Style.RESET_ALL}")
        
        # --- MENU DI SCELTA ---
        print(f"\n{Fore.YELLOW}Come vuoi procedere?{Style.RESET_ALL}")
        print(f"{Fore.CYAN}1) Avvia processo di correzione completo (Init + Repomix) [Default]{Style.RESET_ALL}")
        print(f"{Fore.CYAN}2) Genera solo il prompt (include eventuali modifiche recenti ai file){Style.RESET_ALL}")
        print(f"{Fore.CYAN}3) Non fare nulla{Style.RESET_ALL}")
        
        choice = input(f"\nScelta [1]: ").strip()
        
        if choice in ["", "1"]:
            # Opzione 1: Init Completo
            cmd_init(auto_input=prompt_message)
            
        elif choice == "2":
            # Opzione 2: Solo Prompt (Smart)
            # Tenta di usare cmd_mod per includere i file modificati
            modified_found = cmd_mod(auto_input=prompt_message)
            
            # Se cmd_mod non ha trovato file (ha restituito False), copiamo il prompt liscio
            if not modified_found:
                pyperclip.copy(prompt_message)
                print_success("Nessun file modificato localmente. Copiato solo il report errori.")
            else:
                # cmd_mod ha già copiato il prompt arricchito con i file xml
                pass
                
        else:
            print("Operazione annullata.")
            
def cmd_ignore():
    ensure_prompts_exist()
    print_step("Preparazione suggerimento .repomixignore...")

    # 1. Recupero contenuto ignore attuale e creazione file locale se assente
    current_ignore_content = ""
    local_ignore = ".repomixignore"
    
    # MANTENUTA LOGICA ORIGINALE: check esistenza locale o creazione da globale
    if os.path.exists(local_ignore):
        with open(local_ignore, "r", encoding="utf-8") as f:
            current_ignore_content = f.read()
    else:
        # Se non esiste, determiniamo il contenuto iniziale
        if os.path.exists(GLOBAL_IGNORE_FILE):
            with open(GLOBAL_IGNORE_FILE, "r", encoding="utf-8") as f:
                current_ignore_content = f.read()
            print_step(f"File {local_ignore} creato partendo dal default globale.")
        else:
            current_ignore_content = "node_modules/**\n.git/**\n.next/**"
            print_step(f"File {local_ignore} creato con impostazioni minime.")
        
        # Scrittura fisica del file nella cartella di lavoro
        with open(local_ignore, "w", encoding="utf-8", newline='\n') as f:
            f.write(current_ignore_content.strip())

    # 2. Esecuzione Repomix per ottenere la lista file attuale
    print_step("Esecuzione Repomix per analisi struttura...")
    temp_repomix_out = os.path.join(TEMP_DIR, "structure_check.xml")
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    
    run_command(f"repomix --style xml --output {temp_repomix_out}", capture=False)

    file_list_str = ""
    if os.path.exists(temp_repomix_out):
        with open(temp_repomix_out, "r", encoding="utf-8") as f:
            xml_content = f.read()
            match = re.search(r'<directory_structure>(.*?)</directory_structure>', xml_content, re.DOTALL)
            if match:
                file_list_str = match.group(1).strip()
    
    if not file_list_str:
        print_error("Impossibile estrarre la struttura dei file da Repomix.")
        # Pulizia anche in caso di errore
        if os.path.exists(temp_repomix_out): os.remove(temp_repomix_out)
        return

    # 3. Preparazione Prompt (MODIFICATO: Solo File Esterno)
    if not os.path.exists(PROMPT_CREA_REPOMIXIGNORE):
        print_error(f"File Prompt non trovato: {PROMPT_CREA_REPOMIXIGNORE}")
        print_warn("Crea il file nella cartella 'prompts' con i segnaposto {current_ignore} e {file_list}.")
        return

    try:
        with open(PROMPT_CREA_REPOMIXIGNORE, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        final_prompt = prompt_template.format(
            current_ignore=current_ignore_content,
            file_list=file_list_str
        )
    except Exception as e:
        print_error(f"Errore formattazione prompt (controlla le graffe nel file MD): {e}")
        return

    pyperclip.copy(final_prompt)
    print_success(f"Prompt caricato da {os.path.basename(PROMPT_CREA_REPOMIXIGNORE)} e copiato negli appunti!")
    
    # 4. Acquisizione con normalizzazione forzata
    print(f"\n{Fore.YELLOW}👉 1. INCOLLA gli appunti sul chatbot per generare il Prompt.{Style.RESET_ALL}")    
    print(f"{Fore.YELLOW}👉 2. COPIA la risposta del chatbot negli appunti e premi INVIO.{Style.RESET_ALL}")
    input()

    raw_clipboard = pyperclip.paste()
    
    # Pulizia dai backtick
    content = clean_code_content(raw_clipboard)
    
    # --- MANTENUTA LOGICA ORIGINALE DI PULIZIA ---
    # 1. Normalizziamo i fine riga (rimuove \r e tiene solo \n)
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # 2. Suddividiamo in righe, puliamo gli spazi bianchi a destra/sinistra
    lines = [line.strip() for line in content.splitlines()]
    
    # 3. Rimuoviamo i duplicati di righe vuote (se presenti nell'output LLM)
    final_lines = []
    for i, line in enumerate(lines):
        # Aggiungiamo la riga se non è vuota, OPPURE se è vuota ma quella precedente non lo era
        if line != "" or (i > 0 and final_lines[-1] != ""):
            final_lines.append(line)
    
    final_content = "\n".join(final_lines).strip()

    # 5. Salvataggio con controllo newline
    if not final_content:
        print_warn("Contenuto non rilevato negli appunti. Uso il default esistente.")
        final_content = current_ignore_content.strip()

    with open(local_ignore, "w", encoding="utf-8", newline='\n') as f:
        f.write(final_content)
    print_success(f"File {local_ignore} salvato (pulizia righe doppie eseguita).")

    # Aggiornamento globale (confronto basato su righe significative) - MANTENUTO
    if len(final_content.splitlines()) > len(current_ignore_content.splitlines()):
        with open(GLOBAL_IGNORE_FILE, "w", encoding="utf-8", newline='\n') as f:
            f.write(final_content)
        print_success("Default globale aggiornato.")

    if os.path.exists(temp_repomix_out):
        os.remove(temp_repomix_out)

def cmd_new():
    ensure_prompts_exist()
    
    # --- FASE 1: Richiesta Riassunto al Vecchio LLM ---
    print_step("Generazione richiesta di migrazione sessione...")
    
    migration_prompt = (
        "Siamo arrivati al limite della finestra di contesto e dobbiamo avviare una nuova sessione.\n"
        "Per favore, fornisci un **riassunto dettagliato** per la prossima istanza del chatbot che includa:\n"
        "1. Cosa è stato fatto finora (stato del progetto).\n"
        "2. Analisi tecnica rilevante (scelte architetturali, pattern usati, file chiave).\n\n"
        "IMPORTANTE: Racchiudi l'intera tua risposta all'interno di un unico blocco di codice Markdown (tra tre backtick), "
        "in modo che io possa copiarlo integralmente senza perdere formattazione."
    )
    
    pyperclip.copy(migration_prompt)
    print_success("Prompt di richiesta riassunto copiato negli appunti!")
    print(f"{Fore.YELLOW}👉 1. Incolla questo prompt nella VECCHIA chat.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}👉 2. Copia la risposta (il blocco di codice) che ti darà l'LLM.{Style.RESET_ALL}")
    input("👉 3. Premi INVIO qui quando hai copiato il riassunto negli appunti...")

    # --- FASE 2: Acquisizione Riassunto ---
    raw_summary = pyperclip.paste()
    if not raw_summary.strip():
        print_error("Gli appunti sembrano vuoti.")
        return

    # Puliamo i backtick se l'utente ha copiato tutto il blocco codice
    summary_content = clean_code_content(raw_summary)
    print_step("Riassunto acquisito.")

    # --- FASE 3: Generazione Repomix ---
    if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)
    
    repomix_path = os.path.join(TEMP_DIR, REPOMIX_OUTPUT_FILENAME)
    print_step("Generazione Repomix aggiornato...")
    
    # Crea repomixignore se non esiste (come in init)
    if not os.path.exists(REPOMIX_IGNORE):
         with open(REPOMIX_IGNORE, "w") as f:
            f.write("node_modules/**\n.git/**\n.next/**\ndist/**\nbuild/**\npackage-lock.json\npnpm-lock.yaml\n**/*.pyc")

    run_command(f"repomix . --style xml --output {repomix_path}", capture=False)
    
    if not os.path.exists(repomix_path):
        print_error("Repomix fallito.")
        return

    # Legge il template per la nuova sessione (creato/gestito dall'utente in prompts/3_new_session.md)
    if not os.path.exists(PROMPT_NEW_SESSION_FILE):
        print_error(f"File template mancante: {PROMPT_NEW_SESSION_FILE}")
        return
        
    # Legge regole formattazione
    formato_output_content = ""
    if os.path.exists(PROMPT_FORMATO_OUTPUT):
        with open(PROMPT_FORMATO_OUTPUT, "r", encoding="utf-8") as f: 
            formato_output_content = f.read()

    with open(PROMPT_NEW_SESSION_FILE, "r", encoding="utf-8") as f:
        new_session_template = f.read()
    
    # Sostituisce il placeholder nel template
    new_session_template = new_session_template.replace("{formato_output}", formato_output_content)

    # Combina: Intestazione + Riassunto Vecchio + Istruzioni Nuovo
    final_prompt_content = (
        "# RIASSUNTO SESSIONE PRECEDENTE\n\n"
        f"{summary_content}\n\n"
        "---\n\n"
        f"{new_session_template}"
    )

    prompt_path = os.path.join(TEMP_DIR, PROMPT_FILENAME)
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(final_prompt_content)
    
    print_success(f"File creato: {prompt_path}")

    # --- FASE 5: Consegna ---
    files_to_copy = [prompt_path, repomix_path]
    copied = copy_files_to_clipboard_os(files_to_copy)
    
    print_step("--- PRONTO PER LA NUOVA SESSIONE ---")
    if copied:
        print_success("✅ I 2 file (PROMPT.md con riassunto e XML) sono stati copiati negli appunti!")
        print("👉 Vai nella NUOVA chat e premi CTRL+V.")
    else:
        open_folder(TEMP_DIR)
        print("👉 Ho aperto la cartella. Trascina i 2 file nella NUOVA chat.")
        
def main():
    if len(sys.argv) < 2: return print(f"Uso: rep [init|apply|mod|check|ignore]")
    action = sys.argv[1]
    if action == "init": cmd_init()
    elif action == "apply": cmd_apply()
    elif action == "mod": cmd_mod()
    elif action == "check": cmd_check()
    elif action == "ignore": cmd_ignore()
    elif action == "new": cmd_new()

if __name__ == "__main__":
    main()