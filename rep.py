# NOTA PER LLM CODER: QUANDO MODIFICHI QUESTO FILE USANDO IL FORMATO OUTPUT CHE TI PERMETTE DI SCRIVERE IL FILE INTERO O GLI SNIPPET:
# Assicurati che eventuali testi tipo il tag "< changes >" (scritto appositamente qui con gli spazi in più) siano soggetti a giusti escape, e in generale
# che l'XML che mi dai in output non sia rotto
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
PROMPT_CREA_REPOMIXIGNORE = os.path.join(PROMPTS_DIR, "0_crea_repomixignore.md")
PROMPT_ANALYSIS_FILE = os.path.join(PROMPTS_DIR, "1_analysis.md")
PROMPT_EXECUTE_FILE = os.path.join(PROMPTS_DIR, "2_execute.md")
PROMPT_NEW_SESSION_FILE = os.path.join(PROMPTS_DIR, "3_new_session.md") 
PROMPT_FORMATO_OUTPUT = os.path.join(PROMPTS_DIR, "formato_output.md") 
PROMPT_BEST_PRACTICE_FILE = os.path.join(PROMPTS_DIR, "best_practice.md")
PROMPT_PROCEDURA_SCRITTURA_FILE = os.path.join(PROMPTS_DIR, "procedura_scrittura.md")
PROMPT_PROCEDURA_ANALISI_FILE = os.path.join(PROMPTS_DIR, "procedura_analisi.md")
GLOBAL_IGNORE_FILE = os.path.join(PROMPTS_DIR, ".repomixignore.template")

# --- UTILS SISTEMA ---

def cleanup_and_exit():
    """Pulisce i file temporanei ed esce dallo script."""
    print(f"\n{Fore.RED}⛔ Operazione annullata.{Style.RESET_ALL}")
    
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
        except Exception:
            pass
    sys.exit(0)

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
    if not os.path.exists(PROMPTS_DIR):
        print_error(f"Errore: Cartella prompts mancante in {PROMPTS_DIR}.")
        cleanup_and_exit()
        
    required_files = [
        PROMPT_ANALYSIS_FILE, 
        PROMPT_EXECUTE_FILE, 
        PROMPT_NEW_SESSION_FILE, 
        PROMPT_FORMATO_OUTPUT,
        PROMPT_BEST_PRACTICE_FILE,
        PROMPT_PROCEDURA_SCRITTURA_FILE,
        PROMPT_PROCEDURA_ANALISI_FILE
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        for m in missing:
            print_error(f"Errore: File prompt mancante ({os.path.basename(m)}).")
        print_error("Assicurati che la cartella prompts sia presente e contenga tutti i file necessari.")
        cleanup_and_exit()

def get_multiline_input(prompt_text, default_text=""):
    print(f"\n{Fore.YELLOW}{prompt_text}{Style.RESET_ALL}")

    if HAS_PROMPT_TOOLKIT:
        kb = KeyBindings()

        @kb.add('enter')
        def _(event):
            event.current_buffer.insert_text('\n')

        @kb.add('c-v')
        def _(event):
            event.current_buffer.insert_text(pyperclip.paste())
        
        @kb.add('escape')
        def _(event):
            # Solleva l'eccezione che verrà catturata sotto
            event.app.exit(exception=KeyboardInterrupt)

        @kb.add('escape', '[', '1', '3', ';', '5', 'u')
        @kb.add('c-j')
        def _(event):
            event.current_buffer.validate_and_handle()

        print(f"{Style.DIM}(Scrivi il messaggio. Premi {Fore.CYAN}CTRL+INVIO{Style.RESET_ALL}{Style.DIM} per inviare, {Fore.RED}ESC{Style.RESET_ALL}{Style.DIM} per annullare){Style.RESET_ALL}")        
        
        session = PromptSession(key_bindings=kb, multiline=True)
        try:
            return session.prompt("> ", default=default_text)
        except KeyboardInterrupt:
            cleanup_and_exit()
            return "" 
    else:
        # Fallback standard
        if default_text:
            print(f"{Style.DIM}Testo originale:\n{default_text}{Style.RESET_ALL}")
        print(f"{Style.DIM}(Scrivi 'END' su una riga vuota e premi Invio per terminare. CTRL+C per annullare){Style.RESET_ALL}")
        lines = []
        try:
            while True:
                line = input()
                if line.strip() == "END": break
                lines.append(line)
        except KeyboardInterrupt:
            cleanup_and_exit()
        return "\n".join(lines)
                
def smart_input(prompt_text):
    """Sostituto di input() che supporta ESC tramite prompt_toolkit"""
    if HAS_PROMPT_TOOLKIT:
        kb = KeyBindings()

        @kb.add('escape')
        def _(event):
            event.app.exit(exception=KeyboardInterrupt)

        session = PromptSession(key_bindings=kb)
        try:
            return session.prompt(prompt_text, multiline=False)
        except KeyboardInterrupt:
            cleanup_and_exit()
            return ""
    else:
        try:
            return input(prompt_text)
        except KeyboardInterrupt:
            cleanup_and_exit()

def wait_for_enter(prompt_text=""):
    """Sostituto di input() per pause, supporta ESC"""
    if prompt_text:
        print(f"\n{Fore.YELLOW}{prompt_text}{Style.RESET_ALL}")
        
    if HAS_PROMPT_TOOLKIT:
        kb = KeyBindings()
        
        # Manteniamo eager=True per tentare di essere più veloci possibile
        @kb.add('escape', eager=True)
        def _(event):
            event.app.exit(exception=KeyboardInterrupt)
            
        @kb.add('enter')
        def _(event):
            event.app.exit(result=None)

        session = PromptSession(key_bindings=kb)
        try:
            session.prompt("", multiline=False)
        except KeyboardInterrupt:
            cleanup_and_exit()
    else:
        try:
            input()
        except KeyboardInterrupt:
            cleanup_and_exit()

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
            choice = smart_input(f"\nVuoi ottimizzare il .repomixignore con l'AI? (y/N): ").strip().lower()
            if choice == 'y':
                cmd_ignore()
                print("\n" + "="*40 + "\n")
                print_step("Riprendo l'inizializzazione del progetto...")
            else:
                print_warn("Ottimizzazione .repomixignore saltata.")
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
    with open(PROMPT_BEST_PRACTICE_FILE, "r", encoding="utf-8") as f: best_practice_content = f.read()
    with open(PROMPT_PROCEDURA_ANALISI_FILE, "r", encoding="utf-8") as f: procedura_analisi_content = f.read()
    
    # Gestione intelligente dei placeholder
    final_prompt = template.replace("{user_input}", user_input)
    final_prompt = final_prompt.replace("{best_practice}", best_practice_content)
    final_prompt = final_prompt.replace("{procedura_analisi}", procedura_analisi_content)
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
        feedback_input = "OK, fai tu in autonomia le scelte che ritieni più opportune."

    # 6. Pulizia Temp e Step 2
    if os.path.exists(TEMP_DIR): 
        shutil.rmtree(TEMP_DIR)
        print_step("Cartella temporanea pulita.")
    
    # I file sono garantiti da ensure_prompts_exist()
    with open(PROMPT_FORMATO_OUTPUT, "r", encoding="utf-8") as f: 
        formato_output_content = f.read()
        
    with open(PROMPT_PROCEDURA_SCRITTURA_FILE, "r", encoding="utf-8") as f: 
        procedura_scrittura_content = f.read()

    with open(PROMPT_EXECUTE_FILE, "r", encoding="utf-8") as f: template = f.read()
    
    # Sostituisce l'input utente, il formato output e la procedura
    final_exec_prompt = template.replace("{user_input}", feedback_input)
    final_exec_prompt = final_exec_prompt.replace("{formato_output}", formato_output_content)
    final_exec_prompt = final_exec_prompt.replace("{procedura_scrittura}", procedura_scrittura_content)
    
    pyperclip.copy(final_exec_prompt)
    save_state()
    print_success("✅ Prompt di ESECUZIONE (testo) copiato negli appunti!\n")

    print("👉 1. Vai nella chat e premi CTRL+V, quindi invia il prompt.")
    print(f"{Fore.YELLOW}👉 2. Quando hai ricevuto l'XML di risposta, COPIALO e premi INVIO qui per applicarlo.{Style.RESET_ALL}")
    wait_for_enter()
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
    - Riduce spazi multipli interni a uno solo.
    Restituisce None se la riga diventa vuota dopo la pulizia.
    """
    # Rimuove whitespace laterali
    line = line.strip()
    
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
    file_map = []
    for idx, line in enumerate(original_lines):
        norm = normalize_line(line)
        if norm:
            file_map.append((idx, norm))

    # 3. Creiamo la sequenza "Target" dallo snippet originale
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
    
    n_file = len(file_map)
    n_target = len(target_sequence)

    for i in range(n_file - n_target + 1):
        window = [item[1] for item in file_map[i : i + n_target]]
        if window == target_sequence:
            start_real_index = file_map[i][0]
            end_real_index = file_map[i + n_target - 1][0]
            match_found = True
            break

    if match_found:
        # 1. Recuperiamo l'indentazione originale della prima riga
        first_orig_line = original_lines[start_real_index]
        indent_match = re.match(r"^\s*", first_orig_line)
        original_indent = indent_match.group(0) if indent_match else ""

        # 2. Pulizia edit block
        clean_edit = edit_block.lstrip('\r\n').rstrip()
        edit_lines = clean_edit.splitlines()

        if edit_lines:
            # 3. Applichiamo l'indentazione originale alla prima riga
            edit_lines[0] = original_indent + edit_lines[0].lstrip()
            
            # 4. Ricostruiamo il segmento (tutti tranne l'ultimo hanno \n sicuro)
            new_segment = [line + '\n' for line in edit_lines[:-1]]
            
            # 5. Gestione dell'ultima riga del blocco
            last_line_content = edit_lines[-1]
            
            # Verifichiamo se il blocco sostituito tocca la fine fisica del file
            is_eof = (end_real_index == len(original_lines) - 1)

            # Logica "Best Practice": Se c'era prima o se siamo alla fine, aggiungi \n
            if original_lines[end_real_index].endswith('\n') or is_eof:
                new_segment.append(last_line_content + '\n')
            else:
                new_segment.append(last_line_content)

            # 6. Sostituzione effettiva (ORA INDENTATA CORRETTAMENTE)
            original_lines[start_real_index : end_real_index + 1] = new_segment

        else:
            # Gestione cancellazione: se edit_lines è vuoto, rimuoviamo le righe originali
            del original_lines[start_real_index : end_real_index + 1]

        # Scrittura su disco (Dentro if match_found, ma fuori dalla logica di edit)
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
    while True:
        print_step("Analisi Clipboard XML...")
        raw_content = pyperclip.paste()
        
        tag_open = "<" + "changes>"
        tag_close = "</" + "changes>"
        match = re.search(tag_open + r'(.*?)' + tag_close, raw_content, re.DOTALL)
        
        if not match: 
            print_error(f"Nessun tag {tag_open} trovato.")
        else:
            try: 
                root = ET.fromstring(f"{tag_open}{match.group(1)}{tag_close}")
                
                changes_count = 0
                shell_commands = []
                failed_snippets = []

                for file_node in root.findall('file'):
                    path = file_node.get('path')
                    content = clean_code_content(file_node.text or "")
                    if content and not content.endswith('\n'):
                        content += '\n'
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
                        
                # --- NUOVO: Gestione best_practice_append ---
                for bp_node in root.findall('best_practice_append'):
                    bp_text = clean_code_content(bp_node.text)
                    if bp_text:
                        print(f"\n{Fore.YELLOW}L'AI propone di aggiungere questa nuova Best Practice al sistema:{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}{bp_text}{Style.RESET_ALL}")
                        choice = smart_input(f"Vuoi aggiungerla a best_practice.md? (y/N): ").strip().lower()
                        if choice == 'y':
                            with open(PROMPT_BEST_PRACTICE_FILE, "a", encoding="utf-8") as f:
                                f.write(f"\n\n{bp_text}")
                            print_success("Best practice aggiunta con successo al file.")
                        else:
                            print_warn("Aggiunta best practice ignorata.")

                shell_commands = [] # Reset lista comandi
                shell_node = root.find('shell')
                if shell_node is not None:
                    raw_cmd = clean_code_content(shell_node.text)
                    if raw_cmd:
                        # Divide in righe ignorando quelle vuote
                        shell_commands = [l.strip() for l in raw_cmd.splitlines() if l.strip()]

                save_state()
                
                # --- NUOVO MENU INTERATTIVO SHELL (Lineare) ---
                if shell_commands:
                    print(f"\n{Fore.YELLOW}Comandi shell suggeriti:{Style.RESET_ALL}")
                    for i, cmd in enumerate(shell_commands, 1):
                        print(f"{Fore.CYAN}{i}.{Style.RESET_ALL} {cmd}")
                    
                    print(f"\n{Fore.YELLOW}Scegli un'azione:{Style.RESET_ALL}")
                    print(f"1) {Fore.GREEN}Esegui{Style.RESET_ALL} (Default)")
                    print(f"2) {Fore.BLUE}Modifica ed Esegui{Style.RESET_ALL}")
                    print(f"3) {Fore.RED}Ignora{Style.RESET_ALL}")
                    
                    choice = smart_input(f"\nScelta [1]: ").strip()
                    
                    # --- GESTIONE MODIFICA ---
                    if choice == "2":
                        current_block = "\n".join(shell_commands)
                        print(f"{Fore.YELLOW}Modifica i comandi (CTRL+INVIO per confermare ed eseguire):{Style.RESET_ALL}")
                        
                        # Qui si apre l'editor con il testo precompilato
                        new_input = get_multiline_input("", default_text=current_block)
                        
                        # Aggiorniamo la lista comandi
                        if new_input.strip():
                            shell_commands = [l.strip() for l in new_input.splitlines() if l.strip()]
                        else:
                            print_warn("Lista comandi svuotata.")
                            shell_commands = []
                        
                        # Forziamo la scelta a "1" per far scattare l'esecuzione subito dopo
                        choice = "1"

                    # --- GESTIONE ESECUZIONE ---
                    if choice == "" or choice == "1":
                        if shell_commands:
                            print_step("Esecuzione comandi...")
                            for cmd in shell_commands:
                                print(f"> {cmd}")
                                # check=False permette di continuare anche se un comando da warning
                                subprocess.run(cmd, shell=True, check=False)
                        else:
                            print_warn("Nessun comando da eseguire.")
                            
                    elif choice == "3":
                        print_warn("Comandi ignorati.")

                # NUOVO: Gestione fallimenti e generazione prompt di ripristino
                if failed_snippets:
                    print_error(f"\nAttenzione: {len(failed_snippets)} snippet non sono stati applicati.")
                    
                    # Deduplica mantenendo l'ordine (evita ripetizioni se falliscono più snippet sullo stesso file)
                    unique_fails = list(dict.fromkeys(failed_snippets))
                    file_list_str = "\n".join([f"- {f}" for f in unique_fails])
                    
                    recovery_prompt = f"Le seguenti patch in modalità Snippet non hanno funzionato (match non perfetto con l'originale):\n{file_list_str}\n\nTi fornisco di seguito il contenuto AGGIORNATO e REALE di questi file.\nPer favore, riscrivi l'output per applicare le tue correzioni a questi file, rispettando le nostre regole standard (usa FULL REWRITE se il file è molto piccolo, usa SNIPPET se è grande ma assicurati che <original> corrisponda esattamente a quanto vedi qui sotto):\n\n"
                    
                    for f_path in unique_fails:
                        recovery_prompt += f"### File: {f_path}\n"
                        try:
                            with open(f_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            recovery_prompt += f"```\n{file_content}\n```\n\n"
                        except Exception as e:
                            recovery_prompt += f"*(Errore durante la lettura del file: {e})*\n\n"
                            
                    pyperclip.copy(recovery_prompt)
                    print_success("✅ Prompt di ripristino copiato negli appunti!\n")
                    print("👉 1. Incolla il prompt nella chat per far correggere all'LLM i file rimanenti.")
                    print(f"👉 2. {Fore.YELLOW}COPIA la risposta del chatbot{Style.RESET_ALL} e torna qui.")
                    print(f"\n{Fore.YELLOW}Quando hai copiato la correzione, premi INVIO per applicarla (ESC per uscire).{Style.RESET_ALL}")
                else:
                    print_success("Tutte le modifiche sono state applicate con successo.")
                    print(f"\n{Fore.YELLOW}Premere INVIO per elaborare un altro blocco XML, ESC per terminare.{Style.RESET_ALL}")

            except ET.ParseError as e: 
                print_error(f"Errore XML: {e}")
                print(f"\n{Fore.YELLOW}Premere INVIO per riprovare, ESC per terminare.{Style.RESET_ALL}")

        wait_for_enter()

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
        
        choice = smart_input(f"\nScelta [1]: ").strip()
        
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

    # Rimosso --incremental (che creava cache buggate) e mantenuto l'essenziale
    cmd = f'"{tsc_path}" --noEmit --skipLibCheck --pretty false'

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
            
            # A. FILTRO IGNORE
            if is_ignored(file_path, patterns):
                continue
            
            # B. RIMOSSO IL FILTRO RUMORE - Vogliamo vedere tutti gli errori veri!
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
        
        choice = smart_input(f"\nScelta [1]: ").strip()
        
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
    local_ignore_content_for_prompt = ""
    local_ignore = ".repomixignore"
    
    # MANTENUTA LOGICA ORIGINALE: check esistenza locale o creazione da globale
    if os.path.exists(local_ignore):
        with open(local_ignore, "r", encoding="utf-8") as f:
            current_ignore_content = f.read()
        local_ignore_content_for_prompt = current_ignore_content
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
            
        # Impostiamo il testo per il prompt indicando che il file non c'era
        local_ignore_content_for_prompt = "Al momento non è presente alcun file .repomixignore nel progetto."

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

    # 3. Preparazione Prompt (MODIFICATO per gestire Global e Local separatamente)
    if not os.path.exists(PROMPT_CREA_REPOMIXIGNORE):
        print_error(f"File Prompt non trovato: {PROMPT_CREA_REPOMIXIGNORE}")
        print_warn("Crea il file nella cartella 'prompts'.")
        return

    # Lettura esplicita del Global Ignore
    global_ignore_content = ""
    if os.path.exists(GLOBAL_IGNORE_FILE):
        with open(GLOBAL_IGNORE_FILE, "r", encoding="utf-8") as f:
            global_ignore_content = f.read()

    # Lettura esplicita del Local Ignore (già letto sopra in current_ignore_content, ma per chiarezza)
    # Lettura esplicita del Local Ignore (impostata in precedenza per distinguere se era assente)
    local_ignore_content = local_ignore_content_for_prompt

    try:
        with open(PROMPT_CREA_REPOMIXIGNORE, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # Usiamo le chiavi aggiornate del nuovo file Markdown
        final_prompt = prompt_template.format(
            global_ignore=global_ignore_content,
            local_ignore=local_ignore_content,
            file_list=file_list_str
        )
    except Exception as e:
        print_error(f"Errore formattazione prompt (verifica che il file MD abbia i placeholder {{global_ignore}}, {{local_ignore}}, {{file_list}}): {e}")
        return

    pyperclip.copy(final_prompt)
    print_success(f"Prompt caricato e copiato negli appunti!")
    
    # 4. Acquisizione con normalizzazione forzata
    print(f"\n{Fore.YELLOW}👉 1. INCOLLA gli appunti sul chatbot per generare il Prompt.{Style.RESET_ALL}")    
    print(f"{Fore.YELLOW}👉 2. COPIA la risposta del chatbot negli appunti e premi INVIO.{Style.RESET_ALL}")
    wait_for_enter()

    raw_clipboard = pyperclip.paste()
    
    # --- CHECK CHECK SKIP (Input == Output) ---
    # Se l'utente preme invio senza copiare nulla, negli appunti c'è ancora il prompt.
    if final_prompt.strip()[:50] == raw_clipboard.strip()[:50]:
        print_warn("Rilevato stesso contenuto negli appunti. Ottimizzazione ignorata.")
        # Pulizia temp
        if os.path.exists(temp_repomix_out):
            os.remove(temp_repomix_out)
        return
    
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

    # --- BLOCCO AGGIORNAMENTO GLOBALE (OTTIMIZZATO) ---
    # 1. Rileggiamo il file globale dal disco per sicurezza assoluta
    disk_global_content = ""
    if os.path.exists(GLOBAL_IGNORE_FILE):
        with open(GLOBAL_IGNORE_FILE, "r", encoding="utf-8") as f:
            disk_global_content = f.read()

    # 2. Helper per pulire e contare le righe
    # Rimuove spazi vuoti e considera significative solo le righe con testo
    def get_clean_lines(text):
        return [line.strip() for line in text.splitlines() if line.strip()]

    global_lines = get_clean_lines(disk_global_content)
    new_lines = get_clean_lines(final_content)

    # 3. Print di Debug per capire perché non scattava
    print(f"\n{Style.DIM}[Info Confronto] Righe significative -> Globale: {len(global_lines)} vs Nuovo: {len(new_lines)}{Style.RESET_ALL}")

    # 4. Logica di confronto
    if len(new_lines) > len(global_lines):
        print(f"{Fore.YELLOW}⚠ Il nuovo .repomixignore contiene più regole ({len(new_lines)}) del globale ({len(global_lines)}).{Style.RESET_ALL}")
        
        choice = smart_input(f"Vuoi AGGIORNARE il file globale di riferimento sovrascrivendolo? (y/N): ").strip().lower()
        
        if choice == 'y':
            with open(GLOBAL_IGNORE_FILE, "w", encoding="utf-8", newline='\n') as f:
                f.write(final_content)
            print_success(f"Default globale aggiornato su: {GLOBAL_IGNORE_FILE}")
        else:
            print_step("File globale mantenuto invariato.")
    
    elif len(new_lines) < len(global_lines):
        print_warn("Nota: Il nuovo file generato è più piccolo del globale. Non propongo aggiornamenti.")
    
    else:
        # Stesso numero di righe
        pass

    # Pulizia temp
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
    wait_for_enter("👉 3. Premi INVIO qui quando hai copiato il riassunto negli appunti...")

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

    # I file sono garantiti da ensure_prompts_exist()
    with open(PROMPT_FORMATO_OUTPUT, "r", encoding="utf-8") as f: 
        formato_output_content = f.read()

    with open(PROMPT_BEST_PRACTICE_FILE, "r", encoding="utf-8") as f:
        best_practice_content = f.read()
        
    with open(PROMPT_PROCEDURA_SCRITTURA_FILE, "r", encoding="utf-8") as f:
        procedura_scrittura_content = f.read()

    with open(PROMPT_PROCEDURA_ANALISI_FILE, "r", encoding="utf-8") as f:
        procedura_analisi_content = f.read()

    with open(PROMPT_NEW_SESSION_FILE, "r", encoding="utf-8") as f:
        new_session_template = f.read()
    
    # Sostituisce i placeholder nel template
    new_session_template = new_session_template.replace("{formato_output}", formato_output_content)
    new_session_template = new_session_template.replace("{best_practice}", best_practice_content)
    new_session_template = new_session_template.replace("{procedura_scrittura}", procedura_scrittura_content)
    new_session_template = new_session_template.replace("{procedura_analisi}", procedura_analisi_content)

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
        
def cmd_invert():
    print_step("Analisi Clipboard XML per UNDO...")
    raw_content = pyperclip.paste()
    
    # Trick per evitare che il parser XML si chiuda prematuramente leggendo questo codice
    tag_open = "<" + "changes>"
    tag_close = "</" + "changes>"
    
    match = re.search(tag_open + r'(.*?)' + tag_close, raw_content, re.DOTALL)
    if not match: 
        return print_error(f"Nessun tag {tag_open} trovato negli appunti.")
        
    try: 
        root = ET.fromstring(f"{tag_open}{match.group(1)}{tag_close}")
        fails, count = [], 0
        
        # Avviso se l'XML contiene tag non supportati da invert
        if root.findall('file') or root.findall('delete_file') or root.find('shell') is not None:
            print_warn("⚠ Ignorati <file>, <delete_file> e <shell> (invert supporta solo gli snippet).")
            
        for snip in root.findall('snippet'):
            p = snip.get('path')
            o_node = snip.find('original')
            e_node = snip.find('edit')
            
            o_txt = clean_code_content(o_node.text) if o_node is not None else ""
            e_txt = clean_code_content(e_node.text) if e_node is not None else ""
            
            # INVERSIONE REALE: cerchiamo 'edit' e ripristiniamo 'original'
            if apply_snippet_fuzzy(p, e_txt, o_txt): 
                count += 1
            else: 
                fails.append(p)
                
        save_state()
        
        if fails:
            print_error(f"❌ {len(fails)} snippet non invertiti (possibili modifiche manuali intercorse).")
            
            unique_fails = list(dict.fromkeys(fails))
            file_list_str = "\n".join([f"- {f}" for f in unique_fails])
            
            recovery_prompt = f"Le seguenti patch in modalità Snippet non hanno funzionato in undo:\n{file_list_str}\n\nTi fornisco di seguito il contenuto AGGIORNATO e REALE di questi file.\nPer favore, analizza le tue modifiche precedenti e ripristina il codice allo stato originale per questi file, rispettando le nostre regole standard (usa FULL REWRITE se il file è molto piccolo, usa SNIPPET se è grande ma assicurati che <original> corrisponda esattamente a quanto vedi qui sotto):\n\n"
            
            for f_path in unique_fails:
                recovery_prompt += f"### File: {f_path}\n"
                try:
                    with open(f_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    recovery_prompt += f"```\n{file_content}\n```\n\n"
                except Exception as e:
                    recovery_prompt += f"*(Errore durante la lettura del file: {e})*\n\n"
                    
            pyperclip.copy(recovery_prompt)
            print_success("✅ Prompt di ripristino copiato! Incollalo nella chat.")
        elif count > 0: 
            print_success(f"✅ Ripristino completato ({count} snippet).")
        else: 
            print_warn("Nessuno snippet elaborato.")
            
    except ET.ParseError as e: 
        print_error(f"Errore XML: {e}")

def main():
    if len(sys.argv) < 2: cmd_apply()
    action = sys.argv[1]
    if action == "init": cmd_init()
    elif action == "apply": cmd_apply()
    elif action == "mod": cmd_mod()
    elif action == "check": cmd_check()
    elif action == "ignore": cmd_ignore()
    elif action == "new": cmd_new()
    elif action in ["invert", "undo", "annulla", "cancel", "ripristina"]: cmd_invert()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Cattura CTRL+C globale (utile nei menu input standard)
        cleanup_and_exit()