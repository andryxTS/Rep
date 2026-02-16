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
import time
from colorama import init, Fore, Style

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
    content = content.strip() # Questo pulisce FUORI dai backtick (sicuro)
    pattern = r"^```[a-zA-Z0-9]*\n?(.*?)```$"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        # rstrip() rimuove spazi/invii SOLO dalla fine della stringa
        # preservando l'indentazione iniziale
        return match.group(1).rstrip()
    return content

# --- CORE FUNCTIONS ---

def cmd_init():
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
        input("PREMERE un tasto qualsiasi per procedere con l'ottimizzazione di Repomix tramite chatbot...")
        cmd_ignore()
        print("\n" + "="*40 + "\n")
        print_step("Riprendo l'inizializzazione del progetto...")
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
        print("👉 1. Vai nella chat e premi CTRL+V (Incolla).")
    else:
        print_warn("Impossibile copiare i file automaticamente.")
        open_folder(TEMP_DIR)
        print("👉 Ho aperto la cartella. Seleziona i 2 file e trascinali nella chat.")

    # 5. Attesa Feedback
    # print(f"\n{Fore.MAGENTA}Quando hai ricevuto l'analisi dal chatbot, premi INVIO per lo Step 2...{Style.RESET_ALL}")
    # input()

    print(f"\n{Fore.YELLOW}👉 2. Quando hai ricevuto l'analisi dal chatbot, inserisci il tuo feedback di seguito:{Style.RESET_ALL}")
    feedback_input = input()

    # 6. Pulizia Temp e Step 2
    if os.path.exists(TEMP_DIR): 
        shutil.rmtree(TEMP_DIR)
        print_step("Cartella temporanea pulita.")
    
    with open(PROMPT_EXECUTE_FILE, "r", encoding="utf-8") as f: template = f.read()
    final_exec_prompt = template.replace("{user_input}", feedback_input)
    
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
        {current_ignore}
        ```

        2. La lista dei file che repomix attualmente mi include nel suo file di output
        ```
        {file_list}
        ```

        3. Eccezioni
        Sui seguenti file fai un'eccezione, mantienili nell'output di repomix se sono presenti, (ma non serve metterli con il punto esclamativo per assicurarti che vengano mantenuti):
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
    print(f"\n{Fore.YELLOW}👉 1. INCOLLA gli appunti sul chatbot per generare il Prompt.{Style.RESET_ALL}")    
    print(f"{Fore.YELLOW}👉 2. COPIA la risposta del chatbot negli appunti e premi INVIO.{Style.RESET_ALL}")
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