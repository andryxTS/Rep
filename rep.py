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
from colorama import init, Fore, Style

# Inizializza colorama
init(autoreset=True)

# --- CONFIGURAZIONE ---
STATE_FILE = ".rep_state.json"
REPOMIX_IGNORE = ".repomixignore"
TEMP_DIR = ".rep_temp"  # Nuova cartella temporanea
REPOMIX_OUTPUT_FILENAME = "repomix-output.xml"
PROMPT_FILENAME = "PROMPT.md"

PROMPTS_DIR = os.path.expanduser("~/.rep_prompts")
PROMPT_ANALYSIS_FILE = os.path.join(PROMPTS_DIR, "1_analysis.md")
PROMPT_EXECUTE_FILE = os.path.join(PROMPTS_DIR, "2_execute.md")
GLOBAL_IGNORE_FILE = os.path.join(PROMPTS_DIR, ".repomixignore")

# --- PROMPT DEFAULT (Aggiornati per gestione allegati) ---
DEFAULT_ANALYSIS_PROMPT = """
**MODIFICHE RICHIESTE:**
{user_input}

**Input:**
In allegato a questo messaggio trovi due file:
1. `repomix-output.xml`: L'intero codebase del progetto.
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
* Pianifica le operazioni.
* Scrivi il nuovo codice per le pagine modificate o nuove, PER INTERO, nel formato XML specificato sotto.

**FORMATO DELL'OUTPUT: XML**
1.  **STRUTTURA:** Usa il tag radice `<changes>`.
    *   `<file path="path/to/file">` per file creati o riscritti interamente.
    *   `<snippet path="path/to/file">` per modifiche mirate (Search & Replace).
        *   Dentro snippet usa `<original>` (codice da cercare) e `<edit>` (codice da sostituire).
    *   `<delete_file path="path/to/file" />` per file eliminati.
    *   `<shell>` comandi da eseguire nel terminale `</shell>`
2.  **WRAPPER ESTERNO:** Restituisci l'intero output XML racchiuso in un unico blocco Markdown con **4 backticks**.
3.  **CONTENUTO CODICE:**
    *   Usa SEMPRE `<![CDATA[ ... ]]>`.
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

def get_multiline_input(prompt_text):
    print(f"\n{Fore.YELLOW}{prompt_text} (Premi INVIO due volte per terminare):{Style.RESET_ALL}")
    lines = []
    while True:
        line = input()
        if not line: break
        lines.append(line)
    return "\n".join(lines)

def clean_code_content(content):
    if not content: return ""
    content = content.strip()
    pattern = r"^```[a-zA-Z0-9]*\n?(.*?)```$"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1) if match else content

# --- CORE FUNCTIONS ---

def cmd_init():
    ensure_prompts_exist()
    
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
    user_input = get_multiline_input("Descrivi l'obiettivo delle modifiche")
    
    with open(PROMPT_ANALYSIS_FILE, "r", encoding="utf-8") as f: template = f.read()
    
    # Gestione intelligente del placeholder {codebase}
    # Se il template vecchio lo ha ancora, lo togliamo o lo sostituiamo con un avviso
    final_prompt = template.replace("{user_input}", user_input)
    if "{codebase}" in final_prompt:
        final_prompt = final_prompt.replace("{codebase}", "[VEDI FILE ALLEGATO: repomix-output.xml]")
    
    with open(prompt_path, "w", encoding="utf-8") as f: f.write(final_prompt)
    print_success(f"File creato: {prompt_path}")

    # 4. Copia negli Appunti / Apertura Cartella
    files_to_copy = [prompt_path, repomix_path]
    copied = copy_files_to_clipboard_os(files_to_copy)
    
    print_step("--- PRONTO PER IL CHATBOT ---")
    if copied:
        print_success("✅ I 2 file (PROMPT.md e XML) sono stati copiati negli appunti!")
        print("👉 Vai nella chat e premi CTRL+V (Incolla).")
    else:
        print_warn("Impossibile copiare i file automaticamente.")
        open_folder(TEMP_DIR)
        print("👉 Ho aperto la cartella. Seleziona i 2 file e trascinali nella chat.")

    # 5. Attesa Feedback
    # print(f"\n{Fore.MAGENTA}Quando hai ricevuto l'analisi dal chatbot, premi INVIO per lo Step 2...{Style.RESET_ALL}")
    # input()

    print(f"\n{Fore.YELLOW}Quando hai ricevuto l'analisi dal chatbot, inserisci il tuo feedback di seguito:{Style.RESET_ALL}")
    feedback_input = input()

    # 6. Pulizia Temp e Step 2
    if os.path.exists(TEMP_DIR): 
        shutil.rmtree(TEMP_DIR)
        print_step("Cartella temporanea pulita.")
    
    with open(PROMPT_EXECUTE_FILE, "r", encoding="utf-8") as f: template = f.read()
    final_exec_prompt = template.replace("{user_input}", feedback_input)
    
    pyperclip.copy(final_exec_prompt)
    print_success("Prompt di ESECUZIONE (testo) copiato negli appunti!")
    print("👉 Incollalo nel Chatbot. Poi usa 'rep apply'.")
    save_state()

def apply_snippet(file_path, original_block, edit_block):
    if not os.path.exists(file_path): return False
    with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
    if original_block.strip() in content:
        new_content = content.replace(original_block.strip(), edit_block.strip())
        with open(file_path, 'w', encoding='utf-8') as f: f.write(new_content)
        print_success(f"[Snippet] Applicato: {file_path}")
        return True
    return False

def get_file_hashes():
    hashes = {}
    for root, dirs, files in os.walk("."):
        if any(ignore in root for ignore in ["node_modules", ".git", ".next", "dist", ".rep_temp"]):
            continue
        for file in files:
            try:
                path = os.path.join(root, file)
                with open(path, "rb") as f: hashes[path] = hashlib.md5(f.read()).hexdigest()
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

    for file_node in root.findall('file'):
        path = file_node.get('path')
        content = clean_code_content(file_node.text or "")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        print_success(f"[FILE] Scritto: {path}")
        changes_count += 1

    for snippet in root.findall('snippet'):
        if apply_snippet(snippet.get('path'), 
                         clean_code_content(snippet.find('original').text), 
                         clean_code_content(snippet.find('edit').text)):
            changes_count += 1

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

def cmd_mod():
    old_hashes = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f: old_hashes = json.load(f)
    
    current = get_file_hashes()
    modified = [p for p, h in current.items() if p not in old_hashes or old_hashes[p] != h]
    
    if not modified: return print_success("Nessuna modifica locale rilevata.")
    print_warn(f"{len(modified)} file modificati localmente.")
    
    req = get_multiline_input("Richiesta:")
    xml = "<modified_files>\n" + "".join([f' <file path="{p}"><![CDATA[\n{open(p,"r",encoding="utf-8").read()}\n]]></file>\n' for p in modified]) + "</modified_files>"
    
    pyperclip.copy(f"{req}\n\nATTENZIONE: Ho modificato questi file:\n{xml}")
    print_success("Copiato negli appunti.")
    save_state()

def cmd_check():
    out = run_command("npx tsc --noEmit", capture=True)
    if not out: print_success("Nessun errore TS.")
    else:
        pyperclip.copy(f"Correggi questi errori TS:\n```\n{out}\n```")
        print_success("Errori copiati negli appunti.")

def cmd_ignore():
    ensure_prompts_exist()
    print_step("Preparazione suggerimento .repomixignore...")

    # 1. Recupero contenuto ignore attuale e creazione file locale se assente
    current_ignore_content = ""
    local_ignore = ".repomixignore"
    
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
    # Ora repomix leggerà il .repomixignore appena creato/esistente
    print_step("Esecuzione Repomix per analisi struttura...")
    temp_repomix_out = os.path.join(TEMP_DIR, "structure_check.xml")
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    
    run_command(f"repomix --style xml --output {temp_repomix_out}", capture=False)

    file_list_str = ""
    if os.path.exists(temp_repomix_out):
        with open(temp_repomix_out, "r", encoding="utf-8") as f:
            xml_content = f.read()
            # Estrazione contenuto tra <directory_structure>
            match = re.search(r'<directory_structure>(.*?)</directory_structure>', xml_content, re.DOTALL)
            if match:
                file_list_str = match.group(1).strip()
    
    if not file_list_str:
        print_error("Impossibile estrarre la struttura dei file da Repomix.")
        return

    # 3. Preparazione Prompt (basato sul tuo file MD)
    # Nota: Ho inserito il testo del template direttamente qui per comodità, 
    # ma puoi anche caricarlo da file se preferisci.
    prompt_template = """**Contesto**
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
        Esegui la tua analisi e dammi il file .repomixignore aggiornato, con tutto ciò che avevo prima (punto 1), aggiornato con tutto il resto che ritieni conveniente escludere. 
        Mettimi il nuovo file repomixignore per intero dentro 3 backtick."""

    final_prompt = prompt_template.format(
        current_ignore=current_ignore_content,
        file_list=file_list_str
    )

    pyperclip.copy(final_prompt)
    print_success("Prompt per l'ottimizzazione ignore copiato negli appunti!")
    
    # 4. Acquisizione con normalizzazione forzata
    print(f"\n{Fore.YELLOW}INCOLLA gli appunti sul chatbot per generare il Prompt.{Style.RESET_ALL}")    
    print(f"{Fore.YELLOW}... (attendi la sua risposta) ...{Style.RESET_ALL}")  
    print(f"{Fore.YELLOW}Quindi COPIA la risposta del chatbot negli appunti e premi INVIO.{Style.RESET_ALL}")
    input()

    raw_clipboard = pyperclip.paste()
    
    # Pulizia dai backtick
    content = clean_code_content(raw_clipboard)
    
    # --- FIX RIDEFINITO PER RIGHE VUOTE ---
    # 1. Normalizziamo i fine riga (rimuove \r e tiene solo \n)
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # 2. Suddividiamo in righe, puliamo gli spazi bianchi a destra/sinistra
    lines = [line.strip() for line in content.splitlines()]
    
    # 3. Rimuoviamo i duplicati di righe vuote (se presenti nell'output LLM)
    final_lines = []
    for i, line in enumerate(lines):
        # Aggiungiamo la riga se non è vuota, OPPURE se è vuota ma quella precedente non lo era
        # (questo preserva al massimo una riga vuota di separazione tra blocchi)
        if line != "" or (i > 0 and final_lines[-1] != ""):
            final_lines.append(line)
    
    final_content = "\n".join(final_lines).strip()

    # 5. Salvataggio con controllo newline
    if not final_content:
        print_warn("Contenuto non rilevato negli appunti. Uso il default.")
        final_content = current_ignore_content.strip()

    with open(local_ignore, "w", encoding="utf-8", newline='\n') as f:
        f.write(final_content)
    print_success(f"File {local_ignore} salvato (pulizia righe doppie eseguita).")

    # Aggiornamento globale (confronto basato su righe significative)
    if len(final_content.splitlines()) > len(current_ignore_content.splitlines()):
        with open(GLOBAL_IGNORE_FILE, "w", encoding="utf-8", newline='\n') as f:
            f.write(final_content)
        print_success("Default globale aggiornato.")

    if os.path.exists(temp_repomix_out):
        os.remove(temp_repomix_out)
        
def main():
    if len(sys.argv) < 2: return print(f"Uso: rep [init|apply|mod|check|ignore]")
    action = sys.argv[1]
    if action == "init": cmd_init()
    elif action == "apply": cmd_apply()
    elif action == "mod": cmd_mod()
    elif action == "check": cmd_check()
    elif action == "ignore": cmd_ignore()

if __name__ == "__main__":
    main()