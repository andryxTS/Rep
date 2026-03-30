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
import tempfile
import ctypes
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
TEMP_DIR = ".rep_temp"  # Cartella temporanea locale
CURRENT_TEMP_DIR = TEMP_DIR  # Traccia la cartella effettivamente in uso
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
PROMPT_PATCH_RECOVERY_FILE = os.path.join(PROMPTS_DIR, "patch_recovery.md")
PROMPT_ANTI_ESCAPE_FILE = os.path.join(PROMPTS_DIR, "anti_escape_quadre.md")
GLOBAL_IGNORE_FILE = os.path.join(PROMPTS_DIR, ".repomixignore.template")

# --- UTILS SISTEMA ---

def cleanup_and_exit():
    """Pulisce i file temporanei ed esce dallo script."""
    print(f"\n{Fore.RED}⛔ Operazione annullata.{Style.RESET_ALL}")
    
    if CURRENT_TEMP_DIR and os.path.exists(CURRENT_TEMP_DIR):
        try:
            shutil.rmtree(CURRENT_TEMP_DIR, ignore_errors=True)
        except Exception:
            pass
    sys.exit(0)

def setup_temp_dir():
    """Prepara la cartella temporanea, gestendo i lock di Google Drive/OneDrive."""
    global CURRENT_TEMP_DIR
    local_temp = TEMP_DIR
    
    try:
        if os.path.exists(local_temp):
            shutil.rmtree(local_temp)
        os.makedirs(local_temp)
        CURRENT_TEMP_DIR = local_temp
        return CURRENT_TEMP_DIR
    except (PermissionError, OSError) as e:
        print_warn(f"Accesso negato alla cartella '{local_temp}'. Fallback attivo.")
        fallback_dir = tempfile.mkdtemp(prefix="rep_temp_")
        print_step(f"Uso cartella temporanea di sistema: {fallback_dir}")
        CURRENT_TEMP_DIR = fallback_dir
        return CURRENT_TEMP_DIR

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

def send_to_trash(path):
    """Tenta di inviare il file o cartella nel cestino tramite API di sistema (Windows).
    Se fallisce o il sistema non è Windows, ripiega sull'eliminazione definitiva."""
    if platform.system() != "Windows":
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return

    try:
        HWND = ctypes.c_void_p
        UINT = ctypes.c_uint
        LPCWSTR = ctypes.c_wchar_p
        WORD = ctypes.c_ushort
        BOOL = ctypes.c_int
        LPVOID = ctypes.c_void_p

        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ =[
                ("hwnd", HWND),
                ("wFunc", UINT),
                ("pFrom", LPCWSTR),
                ("pTo", LPCWSTR),
                ("fFlags", WORD),
                ("fAnyOperationsAborted", BOOL),
                ("hNameMappings", LPVOID),
                ("lpszProgressTitle", LPCWSTR)
            ]

        FO_DELETE = 3
        FOF_ALLOWUNDO = 0x40
        FOF_NOCONFIRMATION = 0x10
        FOF_SILENT = 0x04
        FOF_NOERRORUI = 0x0400

        # SHFileOperation richiede una stringa terminata con doppio null byte
        double_null_path = os.path.abspath(path) + '\0\0'

        shfos = SHFILEOPSTRUCTW()
        shfos.hwnd = None
        shfos.wFunc = FO_DELETE
        shfos.pFrom = double_null_path
        shfos.pTo = None
        shfos.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
        shfos.fAnyOperationsAborted = False
        shfos.hNameMappings = None
        shfos.lpszProgressTitle = None

        result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(shfos))
        
        if result != 0:
            raise Exception(f"SHFileOperationW failed with code {result}")
    except Exception:
        # Fallback in caso di errore
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

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
        PROMPT_PROCEDURA_ANALISI_FILE,
        PROMPT_PATCH_RECOVERY_FILE,
        PROMPT_ANTI_ESCAPE_FILE
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
            if not event.current_buffer.text.strip():
                event.current_buffer.validate_and_handle()
            else:
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

        print(f"{Style.DIM}(Scrivi il messaggio. Premi {Fore.CYAN}INVIO a vuoto{Style.RESET_ALL}{Style.DIM} per saltare/inviare, {Fore.CYAN}CTRL+INVIO{Style.RESET_ALL}{Style.DIM} per inviare testo multilinea, {Fore.RED}ESC{Style.RESET_ALL}{Style.DIM} per annullare){Style.RESET_ALL}")
        
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
        print(f"{Style.DIM}(Premi INVIO a vuoto per saltare/inviare, o scrivi 'END' su una riga vuota per terminare il multilinea. CTRL+C per annullare){Style.RESET_ALL}")
        lines = []
        try:
            while True:
                line = input()
                if not lines and not line.strip(): break
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

def extract_repomix_include(text):
    """Cerca la richiesta dell'LLM di espandere file compressi."""
    if not text: return None
    match = re.search(r'repomix\s+--include\s+([^\s`\n]+)', text)
    if match:
        paths = match.group(1).strip()
        # Esclude l'esempio letterale presente nel prompt
        if "path_file_1,path_file_2" in paths:
            return None
        return paths
    return None

def generate_partial_xml(paths_str, output_path):
    """Genera un XML minimale contenente solo i file richiesti, bypassando il repomixignore."""
    paths =[p.strip() for p in paths_str.split(',') if p.strip()]
    xml_lines = ["<files>"]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                xml_lines.append(f'<file path="{path}">\n<![CDATA[\n{content}\n]]>\n</file>')
            except Exception as e:
                print_warn(f"Impossibile leggere il file {path}: {e}")
        else:
            print_warn(f"Il file richiesto non esiste: {path}")
    xml_lines.append("</files>")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))
    return True

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

def cmd_init(auto_input=None, compress_mode=False):
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
    global CURRENT_TEMP_DIR
    CURRENT_TEMP_DIR = setup_temp_dir()
    
    repomix_path = os.path.join(CURRENT_TEMP_DIR, REPOMIX_OUTPUT_FILENAME)
    prompt_path = os.path.join(CURRENT_TEMP_DIR, PROMPT_FILENAME)

    # 2. Esecuzione Repomix
    print_step("Esecuzione Repomix (Output su file)...")
    if not os.path.exists(REPOMIX_IGNORE):
        with open(REPOMIX_IGNORE, "w") as f:
            f.write("node_modules/**\n.git/**\n.next/**\ndist/**\nbuild/**\npackage-lock.json\npnpm-lock.yaml\n**/*.pyc")
    
    # Output diretto nel file temporaneo
    cmd = f"repomix . --style xml --output {repomix_path} --quiet"
    if compress_mode:
        cmd += " --compress"
    run_command(cmd, capture=False) # Mostra log a video

    if not os.path.exists(repomix_path):
        print_error("Repomix fallito. File non creato.")
        return

    # Sostituisce il blocco iniziale di repomix con il Tree personalizzato
    tree_str = generate_project_tree()
    patch_repomix_with_tree(repomix_path, tree_str)

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
    files_to_copy =[prompt_path, repomix_path]
    copied = copy_files_to_clipboard_os(files_to_copy)
    
    print_step("--- PRONTO PER IL CHATBOT ---")
    if copied:
        print_success("✅ I 2 file (PROMPT.md e XML) sono stati copiati negli appunti!")
        print("👉 1. Vai nella chat e premi CTRL+V (Incolla).")
    else:
        print_warn("Impossibile copiare i file automaticamente.")
        open_folder(CURRENT_TEMP_DIR)
        print("👉 Ho aperto la cartella. Seleziona i 2 file e trascinali nella chat.")

    # 5. Attesa Feedback
    msg = "👉 2. Inserisci il feedback dal chatbot (lascia vuoto per default):"
    feedback_input = get_multiline_input(msg).strip()
    
    if not feedback_input:
        feedback_input = "OK, fai tu in autonomia le scelte che ritieni più opportune."

    # Intercetta richiesta LLM per file non compressati
    raw_clipboard = pyperclip.paste()
    requested_paths = extract_repomix_include(raw_clipboard)

    # 6. Pulizia Temp e Step 2
    if os.path.exists(CURRENT_TEMP_DIR): 
        shutil.rmtree(CURRENT_TEMP_DIR, ignore_errors=True)
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
    
    if requested_paths:
        print_step(f"Rilevata richiesta LLM per file completi: {requested_paths}")
        CURRENT_TEMP_DIR = setup_temp_dir()
        repomix_parziale_path = os.path.join(CURRENT_TEMP_DIR, "repomix-parziale-non-compressato.txt")
        prompt_path = os.path.join(CURRENT_TEMP_DIR, "PROMPT.md")
        
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(final_exec_prompt)
            
        generate_partial_xml(requested_paths, repomix_parziale_path)
        
        files_to_copy = [prompt_path]
        if os.path.exists(repomix_parziale_path):
            files_to_copy.append(repomix_parziale_path)
            
        copied = copy_files_to_clipboard_os(files_to_copy)
        save_state()
        if copied:
            print_success("✅ PROMPT.md e file Parziale copiati negli appunti come file!")
            print("👉 1. Vai nella chat e premi CTRL+V (Incolla i due file).")
        else:
            open_folder(CURRENT_TEMP_DIR)
            print_warn("Trascina i due file generati nella chat.")
    else:
        pyperclip.copy(final_exec_prompt)
        save_state()
        print_success("✅ Prompt di ESECUZIONE (testo) copiato negli appunti!\n")
        print("👉 1. Vai nella chat e premi CTRL+V, quindi invia il prompt.")

    print(f"{Fore.YELLOW}👉 2. Quando hai ricevuto l'XML di risposta, COPIALO e premi INVIO qui per applicarlo.{Style.RESET_ALL}")
    wait_for_enter()
    cmd_apply()

def apply_snippet(file_path, original_block, edit_block, snippet_index="N/A"):
    if not os.path.exists(file_path): return False
    with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
    if original_block.strip() in content:
        new_content = content.replace(original_block.strip(), edit_block.strip())
        with open(file_path, 'w', encoding='utf-8') as f: f.write(new_content)
        print(f"✅ Snippet [{snippet_index}] applicato a: {file_path}")
        return True
    return False

def normalize_line(line):
    """
    Pulisce una riga per il confronto 'fuzzy' ultra-aggressivo:
    - Ignora i commenti per matchare le righe anche se l'LLM li omette o li modifica.
    - Rimuove TUTTI gli spazi, tabulazioni, a capo e caratteri invisibili.
    Restituisce None se la riga diventa vuota dopo la pulizia.
    """
    line = line.strip()
    if not line:
        return None
        
    # 1. Rimuove i commenti monoriga (le condizioni evitano di rompere codice valido)
    line = re.sub(r'<!--.*?-->', '', line)           # Commenti HTML
    line = re.sub(r'/\*.*?\*/', '', line)            # Commenti a blocco monoriga JS/CSS
    line = re.sub(r'(?<!:)//.*$', '', line)          # Commenti // (il negative lookbehind esclude gli URL con ://)
    line = re.sub(r'(^|\s)#.*$', '', line)           # Commenti # (solo inizio riga o dopo spazio, salva href="#id" e bg-[#fff])

    # 2. Rimuove tutti gli spazi e caratteri invisibili (es. Zero-width space)
    line = re.sub(r'[\s\u200B-\u200D\uFEFF]+', '', line)
    
    if not line:
        return None
        
    return line

def apply_snippet_fuzzy(file_path, original_block, edit_block, snippet_index="N/A"):
    if not os.path.exists(file_path):
        print_warn(f"Snippet [{snippet_index}] - File non trovato: {file_path}")
        return False

    # 1. Leggiamo il file originale preservando tutto
    with open(file_path, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()

    # 2. Creiamo la mappa "Searchable" del file
    file_map =[]
    for idx, line in enumerate(original_lines):
        norm = normalize_line(line)
        if norm:
            file_map.append((idx, norm))

    # 3. Creiamo la sequenza "Target" e mappiamo gli offset
    original_lines_raw = original_block.strip('\r\n').splitlines()
    target_mapping =[]
    
    for idx, line in enumerate(original_lines_raw):
        norm = normalize_line(line)
        if norm:
            target_mapping.append((idx, norm))

    match_found = False
    true_start_index = -1
    true_end_index = -1

    if not target_mapping:
        if not original_lines_raw:
            print_warn(f"Lo snippet[{snippet_index}] originale è vuoto.")
            return False
            
        n_raw = len(original_lines_raw)
        n_file_lines = len(original_lines)
        
        for i in range(n_file_lines - n_raw + 1):
            window = original_lines[i : i + n_raw]
            if all(window[j].strip() == original_lines_raw[j].strip() for j in range(n_raw)):
                true_start_index = i
                true_end_index = i + n_raw - 1
                match_found = True
                break
                
    else:
        target_sequence = [item[1] for item in target_mapping]
        target_start_offset = target_mapping[0][0]
        target_end_offset = target_mapping[-1][0]

        # 4. Algoritmo di ricerca della sequenza (Sliding Window)
        n_file = len(file_map)
        n_target = len(target_sequence)

        for i in range(n_file - n_target + 1):
            window = [item[1] for item in file_map[i : i + n_target]]
            if window == target_sequence:
                start_real_index = file_map[i][0]
                end_real_index = file_map[i + n_target - 1][0]
                
                # Calcolo espansione per includere commenti/spazi
                pot_true_start = start_real_index - target_start_offset
                pot_true_end = end_real_index + (len(original_lines_raw) - 1 - target_end_offset)
                
                # Sicurezza: Bounds check
                if pot_true_start < 0 or pot_true_end >= len(original_lines):
                    continue
                    
                # Sicurezza: Verifica che le righe espanse siano effettivamente ignorabili (commenti/spazi)
                valid_expansion = True
                for j in range(pot_true_start, start_real_index):
                    if normalize_line(original_lines[j]) is not None:
                        valid_expansion = False
                        break
                for j in range(end_real_index + 1, pot_true_end + 1):
                    if normalize_line(original_lines[j]) is not None:
                        valid_expansion = False
                        break
                        
                if not valid_expansion:
                    continue # Le estremità contengono logica inattesa, prosegue a cercare un match esatto
                    
                # Match confermato e sicuro
                true_start_index = pot_true_start
                true_end_index = pot_true_end
                match_found = True
                break

    if match_found:
        # 1. Recuperiamo l'indentazione originale della prima riga FISICA sostituita
        first_orig_line = original_lines[true_start_index]
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
            is_eof = (true_end_index == len(original_lines) - 1)

            # Logica "Best Practice": Se c'era prima o se siamo alla fine, aggiungi \n
            if original_lines[true_end_index].endswith('\n') or is_eof:
                new_segment.append(last_line_content + '\n')
            else:
                new_segment.append(last_line_content)

            # 6. Sostituzione effettiva (ORA INDENTATA CORRETTAMENTE)
            original_lines[true_start_index : true_end_index + 1] = new_segment

        else:
            # Gestione cancellazione: se edit_lines è vuoto, rimuoviamo le righe originali
            del original_lines[true_start_index : true_end_index + 1]

        # Scrittura su disco (Dentro if match_found, ma fuori dalla logica di edit)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(original_lines)
            
        print(f"✅ Snippet[{snippet_index}] applicato a: {file_path}")
        return True
    
    else:
        print_warn(f"Lo snippet[{snippet_index}] originale non coincide: {file_path}")
        return False

# --- HELPER PER GESTIONE IGNORE ---

def load_ignore_patterns():
    """Carica i pattern dai file ignore, separando ignores e unignores (es. !prompts/)."""
    ignores = set()
    unignores = set()
    
    # Pattern di sistema hardcoded (sempre ignorati)
    ignores.add(".rep_temp")
    ignores.add(".git")
    ignores.add(STATE_FILE)
    ignores.add(".open-next")
    ignores.add(".next")
    ignores.add("node_modules")
    
    files_to_read = []
    
    # 1. Legge .gitignore per massimizzare la compatibilità (Repomix lo fa di default)
    if os.path.exists(".gitignore"): files_to_read.append(".gitignore")
    # 2. Legge il file globale
    if os.path.exists(GLOBAL_IGNORE_FILE): files_to_read.append(GLOBAL_IGNORE_FILE)
    # 3. Legge il file locale
    if os.path.exists(REPOMIX_IGNORE): files_to_read.append(REPOMIX_IGNORE)
        
    for file_path in files_to_read:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if line.startswith('!'):
                            unignores.add(line[1:])
                        else:
                            ignores.add(line)
        except Exception as e:
            print_warn(f"Impossibile leggere ignore file {file_path}: {e}")
            
    return list(ignores), list(unignores)

def match_pattern(path, name, pattern):
    """Helper che adatta un pattern stile glob/gitignore per fnmatch OS-aware"""
    p = pattern.rstrip('/')
    # Rimuove wildcard finali per far matchare l'intera cartella (es. node_modules/** -> node_modules)
    if p.endswith('/**'): p = p[:-3]
    elif p.endswith('/*'): p = p[:-2]
    
    # Gestione del leading slash (es. /.next indica la cartella solo in root)
    is_root = False
    if p.startswith('/'):
        is_root = True
        p = p[1:]
    
    # Adatta i path per Windows se necessario
    p = p.replace('/', os.sep)
    
    if is_root:
        if path == p: return True
        if path.startswith(p + os.sep): return True
        if fnmatch.fnmatch(path, p): return True
    else:
        if fnmatch.fnmatch(name, p): return True
        if fnmatch.fnmatch(path, p): return True
        if path == p: return True
        if path.startswith(p + os.sep): return True
        if (os.sep + p + os.sep) in path: return True
        if path.endswith(os.sep + p): return True
        
    return False

def is_ignored(path, ignores, unignores):
    """Controlla se un path deve essere ignorato, dando precedenza alle eccezioni (!)."""
    path = os.path.normpath(path)
    if path.startswith("." + os.sep):
        path = path[2:]
    
    name = os.path.basename(path)
    
    # Prima controlla le eccezioni (!pattern) che invalidano l'ignore
    for pattern in unignores:
        if match_pattern(path, name, pattern):
            return False

    # Poi controlla le esclusioni
    for pattern in ignores:
        if match_pattern(path, name, pattern):
            return True

    return False

# --- FUNZIONE AGGIORNATA ---

def get_file_hashes():
    hashes = {}
    ignores, unignores = load_ignore_patterns()
    
    for root, dirs, files in os.walk("."):
        # OTTIMIZZAZIONE: Modifica 'dirs' in-place per impedire a os.walk 
        # di scendere nelle cartelle ignorate (es. node_modules).
        # Questo velocizza enormemente lo script.
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), ignores, unignores)]
        
        # Controllo se la root corrente è ignorata (doppio check)
        if is_ignored(root, ignores, unignores):
            continue

        for file in files:
            file_path = os.path.join(root, file)
            
            # Se il file non è ignorato, calcola l'hash
            if not is_ignored(file_path, ignores, unignores):
                try:
                    with open(file_path, "rb") as f: 
                        hashes[file_path] = hashlib.md5(f.read()).hexdigest()
                except: pass
    return hashes

def save_state():
    with open(STATE_FILE, "w") as f: json.dump(get_file_hashes(), f)

# --- TREE GENERATOR ---
def generate_project_tree():
    sys_ignores = {".git", "node_modules", ".next", ".open-next", "dist", "build", "out", ".rep_temp", "__pycache__", ".venv", "venv", ".wrangler", ".idea", ".vscode"}
    sys_unignores = set()
    
    if os.path.exists(".gitignore"):
        try:
            with open(".gitignore", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if line.startswith('!'): sys_unignores.add(line[1:])
                        else: sys_ignores.add(line)
        except: pass

    repo_ignores = set()
    repo_unignores = set()
    
    for ignore_file in[GLOBAL_IGNORE_FILE, REPOMIX_IGNORE]:
        if os.path.exists(ignore_file):
            try:
                with open(ignore_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if line.startswith('!'): repo_unignores.add(line[1:])
                            else: repo_ignores.add(line)
            except: pass

    tree_lines =[]
    
    def is_sys_ignored(path, name):
        path = os.path.normpath(path)
        if path.startswith("." + os.sep): path = path[2:]
        for p in sys_unignores:
            if match_pattern(path, name, p): return False
        for p in sys_ignores:
            if match_pattern(path, name, p): return True
        return False

    def is_repo_ignored(path, name):
        path = os.path.normpath(path)
        if path.startswith("." + os.sep): path = path[2:]
        for p in repo_unignores:
            if match_pattern(path, name, p): return False
        for p in repo_ignores:
            if match_pattern(path, name, p): return True
        return False

    def walk(current_dir, prefix="", parent_omitted=False):
        try:
            entries = list(os.scandir(current_dir))
        except PermissionError:
            return

        valid_entries =[]
        for e in entries:
            rel_path = os.path.relpath(e.path, start=".")
            if not is_sys_ignored(rel_path, e.name):
                valid_entries.append(e)
                
        valid_entries.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        
        count = len(valid_entries)
        for i, e in enumerate(valid_entries):
            is_last = (i == count - 1)
            connector = "└── " if is_last else "├── "
            
            rel_path = os.path.relpath(e.path, start=".")
            
            is_omitted = False
            currently_omitted = parent_omitted
            
            if not parent_omitted and is_repo_ignored(rel_path, e.name):
                is_omitted = True
                currently_omitted = True
                
            omit_label = " OMIT" if is_omitted else ""
            tree_lines.append(f"{prefix}{connector}{e.name}{'/' if e.is_dir() else ''}{omit_label}")
            
            if e.is_dir():
                ext = "    " if is_last else "│   "
                walk(e.path, prefix + ext, currently_omitted)

    project_name = os.path.basename(os.path.abspath("."))
    tree_lines.append(f"{project_name}/")
    walk(".")
    
    tree_str = "\n".join(tree_lines)
    
    print(f"\n{Fore.CYAN}--- PROJECT TREE ---{Style.RESET_ALL}")
    print(tree_str)
    print(f"{Fore.CYAN}--------------------{Style.RESET_ALL}\n")
    
    return tree_str

def patch_repomix_with_tree(filepath, tree_str):
    if not os.path.exists(filepath): return
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    files_idx = content.find("<files>")
    if files_idx != -1:
        files_content = content[files_idx:]
        new_content = (
            "<project_tree>\n"
            "Questa e' la struttura completa del progetto (esclusi file ignorati da .gitignore e build folder).\n"
            "Usa questo tree per comprendere l'architettura anche per i file il cui contenuto e' stato omesso per risparmiare token.\n"
            "Nota: Le cartelle e i file contrassegnati con OMIT sono presenti nel progetto ma il loro contenuto e' stato omesso nel repomix. Se il progetto e' stato esportato in modalita' compressa, i file presenti potrebbero essere minimizzati. Sentiti libero di richiedere la versione integrale di qualsiasi file ti serva, senza parsimonia.\n"
            "<![CDATA[\n"
            f"{tree_str}\n"
            "]]>\n"
            "</project_tree>\n\n"
            f"{files_content}"
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)


def cmd_apply():
    while True:
        print_step("Analisi Clipboard XML...")
        raw_content = pyperclip.paste()
        
        if raw_content.strip() == "":
            print_step("Appunti vuoti rilevati. Avvio scansione file modificati (cmd_mod)...")
            if cmd_mod(auto_input=""):
                print(f"{Fore.YELLOW}👉 Incolla il prompt generato nella chat, copia la risposta XML e premi INVIO qui per continuare.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Nessun file modificato. Copia un blocco XML valido e premi INVIO.{Style.RESET_ALL}")
            wait_for_enter()
            continue
            
        tag_open = "<" + "changes>"

        tag_close = "</" + "changes>"
        match = re.search(tag_open + r'(.*?)' + tag_close, raw_content, re.DOTALL)
        
        if not match: 
            requested_paths = extract_repomix_include(raw_content)
            if requested_paths:
                print_step(f"Rilevata richiesta LLM per file completi: {requested_paths}")
                global CURRENT_TEMP_DIR
                CURRENT_TEMP_DIR = setup_temp_dir()
                repomix_parziale_path = os.path.join(CURRENT_TEMP_DIR, "repomix-parziale-non-compressato.txt")
                
                generate_partial_xml(requested_paths, repomix_parziale_path)
                
                if os.path.exists(repomix_parziale_path):
                    if copy_files_to_clipboard_os([repomix_parziale_path]):
                        print_success("✅ File parziale non compressato copiato negli appunti!")
                        print("👉 Vai nella chat, incollalo (CTRL+V) e attendi la risposta (XML).")
                    else:
                        open_folder(CURRENT_TEMP_DIR)
                        print_warn("Trascina il file generato nella chat.")
                else:
                    print_error("Errore durante la generazione del file repomix parziale.")
            elif tag_open in raw_content:
                print_error(f"Trovato tag {tag_open} ma manca la chiusura {tag_close}. Flusso interrotto?")
                try:
                    with open(PROMPT_ANTI_ESCAPE_FILE, "r", encoding="utf-8") as f:
                        recovery_msg = f.read()
                    pyperclip.copy(recovery_msg)
                    print("Prompt anti-interruzione (spazio tra quadre) copiato negli appunti!")
                    print("👉 Incollalo nella chat per far correggere il problema all'LLM.")
                except Exception as ex:
                    print_warn(f"Impossibile caricare il prompt di recovery: {ex}")
            else:
                print_error(f"Nessun tag {tag_open} trovato.")
        else:
            try:
                root = ET.fromstring(f"{tag_open}{match.group(1)}{tag_close}")
                
                changes_count = 0
                shell_commands = []
                failed_snippets = []
                successful_snippets = []

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
                    idx = snippet.get('index', 'N/A')
                    # Gestione sicura dei nodi figlio
                    original_node = snippet.find('original')
                    edit_node = snippet.find('edit')
                    
                    original_text = clean_code_content(original_node.text) if original_node is not None else ""
                    edit_text = clean_code_content(edit_node.text) if edit_node is not None else ""

                    # Tenta l'applicazione
                    if apply_snippet_fuzzy(path, original_text, edit_text, snippet_index=idx):
                        changes_count += 1
                        successful_snippets.append(f"- [Snippet {idx}] {path}")
                    else:
                        failed_snippets.append((path, idx))

                for del_node in root.findall('delete_file'):
                    path = del_node.get('path')
                    if os.path.exists(path):
                        send_to_trash(path)
                        print_warn(f"[DEL] Rimosso (cestino): {path}")
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
                    # --- GESTIONE ESECUZIONE ---
                    if choice == "" or choice == "1":
                        if shell_commands:
                            print_step("Esecuzione comandi in batch (sessione unificata)...")
                            fd, bat_path = tempfile.mkstemp(suffix=".bat", text=True)
                            os.close(fd)
                            try:
                                with open(bat_path, "w", encoding="utf-8") as f:
                                    f.write("@echo off\n")
                                    # chcp 65001 serve a gestire correttamente gli accenti/caratteri speciali nel cmd
                                    f.write("chcp 65001 >nul\n")
                                    for cmd in shell_commands:
                                        # Escape per visualizzare correttamente i comandi con l'echo
                                        safe_cmd = cmd.replace('>', '^>').replace('<', '^<').replace('|', '^|').replace('&', '^&')
                                        f.write(f"echo ^> {safe_cmd}\n")
                                        
                                        # Fix per Windows: Aggiunge 'call' davanti agli script batch di Node 
                                        # altrimenti l'esecuzione del .bat si interrompe in modo anomalo
                                        exec_cmd = re.sub(r'(^|&&?|\|\|?)\s*(pnpm|npm|npx|yarn|bun)\b', r'\1 call \2', cmd)
                                        f.write(f"{exec_cmd}\n")
                                subprocess.run(bat_path, shell=True, check=False)
                            finally:
                                if os.path.exists(bat_path):
                                    try: os.remove(bat_path)
                                    except: pass
                        else:
                            print_warn("Nessun comando da eseguire.")
                            
                    elif choice == "3":
                        print_warn("Comandi ignorati.")

                # NUOVO: Gestione fallimenti e generazione prompt di ripristino
                if failed_snippets:
                    print()
                    print_error(f"Attenzione: {len(failed_snippets)} snippet non sono stati applicati.")
                    
                    # Raggruppa i fallimenti per file
                    fails_by_file = {}
                    for f_path, idx in failed_snippets:
                        if f_path not in fails_by_file:
                            fails_by_file[f_path] =[]
                        fails_by_file[f_path].append(idx)
                    
                    fail_list_str = "\n".join([f"- [Snippet {', '.join(indices)}] {path}" for path, indices in fails_by_file.items()])
                    success_list_str = "\n".join(successful_snippets) if successful_snippets else "Nessuno."
                    
                    with open(PROMPT_PATCH_RECOVERY_FILE, "r", encoding="utf-8") as f:
                        recovery_template = f.read()
                        
                    recovery_prompt = recovery_template.replace("{failed_count}", str(len(failed_snippets)))
                    recovery_prompt = recovery_prompt.replace("{fail_list_str}", fail_list_str)
                    recovery_prompt = recovery_prompt.replace("{success_list_str}", success_list_str)
                    
                    for f_path in fails_by_file.keys():
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
                try:
                    with open(PROMPT_ANTI_ESCAPE_FILE, "r", encoding="utf-8") as f:
                        recovery_msg = f.read()
                    pyperclip.copy(recovery_msg)
                    print_success("✅ Prompt anti-interruzione (spazio tra quadre) copiato negli appunti!")
                    print("👉 Incollalo nella chat per far correggere il problema all'LLM.")
                except Exception as ex:
                    print_warn(f"Impossibile caricare il prompt di recovery: {ex}")
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
    if auto_input is not None:
        req = auto_input
        if req:
            print_step("Input acquisito automaticamente dal report errori.")
        else:
            print_step("Generazione automatica report modifiche (senza richiesta specifica).")
    else:
        req = get_multiline_input("Richiesta (OPZIONALE, altrimenti lascia vuoto per ottenere solo l'aggiornamento file modificati):")

    xml = "<modified_files>\n" + "".join([f' <file path="{p}"><![CDATA[\n{open(p,"r",encoding="utf-8").read()}\n]]></file>\n' for p in modified]) + "</modified_files>"
    
    if req:
        pyperclip.copy(f"{req}\n\n[ATTENZIONE, avviso automatico di sistema: dall'ultimo aggiornamento sono stati modificati alcuni file, che verranno riportati qui sotto e verranno considerati la nuova versione di riferimento:]\n```{xml}```")
    else:
        pyperclip.copy(f"[ATTENZIONE, avviso automatico di sistema: dall'ultimo aggiornamento sono stati modificati alcuni file, che verranno riportati qui sotto e verranno considerati la nuova versione di riferimento:]\n```{xml}```")
    print_success("Prompt con file modificati copiato negli appunti.")
    save_state()
    return True

def cmd_check(strict_mode=True):
    # --- 1. RICERCA TSC LOCALE ---
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
    # --- 4. ESECUZIONE ANALISI ---
    print_step(f"Analisi TypeScript{' e Dipendenze (Strict Mode)' if strict_mode else ''} in corso...")

    # Pulizia hard cache tsbuildinfo per cold start check
    for f in os.listdir("."):
        if f.endswith(".tsbuildinfo"):
            try:
                os.remove(f)
            except Exception:
                pass

    # Seleziona l'esecutore corretto basandosi sul package manager (risolve problemi di percorsi/crash di tsc.cmd)
    if os.path.exists("pnpm-lock.yaml"): base_cmd = "pnpm exec tsc"
    elif os.path.exists("yarn.lock"): base_cmd = "yarn tsc"
    elif os.path.exists("bun.lockb"): base_cmd = "bunx tsc"
    else: base_cmd = "npx tsc"

    # Ripristinato --skipLibCheck e --pretty false, MA usiamo pnpm/npx per garantire l'esecuzione corretta e identica al manuale.
    cmd = f'{base_cmd} --noEmit --incremental false --skipLibCheck --pretty false'

    try:
        tsc_process = subprocess.Popen(
            cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', errors='replace'
        )
        
        depcheck_process = None
        if strict_mode:
            depcheck_cmd = "pnpm dlx depcheck --json"
            depcheck_process = subprocess.Popen(
                depcheck_cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', errors='replace'
            )

        tsc_stdout, tsc_stderr = tsc_process.communicate(timeout=60)
        tsc_returncode = tsc_process.returncode
        
        depcheck_missing = {}
        if strict_mode:
            dep_stdout, dep_stderr = depcheck_process.communicate(timeout=60)
            try:
                import json
                json_match = re.search(r'\{.*\}', dep_stdout, re.DOTALL)
                if json_match:
                    dep_data = json.loads(json_match.group(0))
                    depcheck_missing = dep_data.get("missing", {})
            except Exception as e:
                print_warn(f"Impossibile parsare l'output di depcheck: {e}")

    except subprocess.TimeoutExpired:
        try:
            tsc_process.kill()
            if depcheck_process:
                depcheck_process.kill()
        except: pass
        return print_error("Timeout: il controllo ci sta mettendo troppo.")
    
    # --- 5. FILTRO E REPORT ---
    raw_output = (tsc_stdout or "") + "\n" + (tsc_stderr or "")
    lines = raw_output.splitlines()
    
    filtered_errors = []
    missing_modules_count = 0
    ignores, unignores = load_ignore_patterns()
    
    # Regex ultra-resiliente per formati pretty/non-pretty e localizzazioni (con tolleranza per spazi)
    error_pattern = re.compile(r'^([^\s].+?)(?:\(\d+,\s*\d+\):?|:\d+:\d+\s+-?).*?(TS\d+)\s*:(.+)')
    # Regex completa per rimuovere TUTTI i codici ANSI, inclusi i link cliccabili OSC 8 (\x1b]8;;...\x1b\) generati da TypeScript
    ansi_escape = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\].*?(?:\x1b\\|\x07))')

    current_error_valid = False

    for line in lines:
        # Pulisce la riga dai colori del terminale che sfalsano la regex
        line_clean = ansi_escape.sub('', line).strip()
        if not line_clean:
            continue
            
        match = error_pattern.match(line_clean)
        
        if match:
            file_path = match.group(1)
            
            # A. FILTRO IGNORE
            if is_ignored(file_path, ignores, unignores):
                current_error_valid = False
                continue
            
            # B. Errore valido
            current_error_valid = True
            filtered_errors.append(line_clean)
        elif current_error_valid:
            # È una riga di continuazione di un errore valido (es. dettagli sul mismatch dei tipi)
            filtered_errors.append("  " + line_clean)

    # Difesa contro crash silenziosi (es. comando non trovato, execution policy o file non parsati)
    if not filtered_errors and tsc_returncode != 0:
        err_msg = ansi_escape.sub('', raw_output).strip() if raw_output.strip() else "Nessun output registrato (Processo terminato in modo anomalo o non trovato)."
        if "TS" in err_msg:
            # Fallback totale a prova di bomba: la regex ha fallito ma ci sono errori TS veri. Diamo in pasto tutto all'utente/LLM!
            filtered_errors.extend([line for line in err_msg.splitlines() if line.strip()])
        else:
            filtered_errors.append(f"ERRORE DI ESECUZIONE TS: Il comando TypeScript ha fallito in modo anomalo.\nOutput raw:\n{err_msg}")

    if strict_mode and depcheck_missing:
        for pkg, files in depcheck_missing.items():
            for f in files:
                try:
                    rel_f = os.path.relpath(f, start=os.getcwd())
                except:
                    rel_f = f
                
                if not is_ignored(rel_f, ignores, unignores):
                    filtered_errors.append(f"{rel_f}(1,1): error TS9999: Missing dependency '{pkg}' in package.json")

    # REPORT FINALE
    if missing_modules_count > 0:
        print_warn(f"Nascosti {missing_modules_count} errori di configurazione (tipi mancanti).")

    if not filtered_errors:
        print_success("✅ Nessun errore logico trovato nei file sorgente.")
    else:
        # Costruzione del prompt per LLM (Testo aggiornato come richiesto)
        ts_report = "\n".join(filtered_errors)
        prompt_message_init = (
            "Ho eseguito un controllo del typescript con tsc e ho ottenuto questi errori:\n"
            f"```typescript\n{ts_report}\n```\n\n"
            "**DIRETTIVE CRITICHE DI ANALISI:**\n"
            "1. **NO ALLUCINAZIONI:** Non dedurre il contenuto del file basandoti solo sul messaggio d'errore. L'errore ti dice *cosa* non va, ma solo il contesto allegato (`repomix-output.txt`) ti dice *com'è scritto davvero* il codice ora.\n"
            "2. **LOCALIZZAZIONE:** Ricorda che l'errore segnalato alla riga X potrebbe essere causato da una definizione mancante o errata in un punto precedente o in un file diverso (es. interfacce o tipi importati).\n"
            "3. **VERIFICA REALE:** Prima di proporre una soluzione, verifica se il codice nel contesto contiene già la fix (il report tsc potrebbe essere disallineato). Se il codice ti sembra già corretto, dimmelo.\n\n"
            "**PROCEDURA:**\n"
            "- Analizza l'errore confrontandolo con il codice reale.\n"
            "- Nell'eseguire le correzioni userai il formato XML che ti indicherò.\n"
            "- **NOTA:** Ignora il tag `<shell>` che ti scriverò nel formato output, per il controllo del typescript gestisco io l'esecuzione dei comandi."
        )
        prompt_message = (
            "Ho eseguito un controllo del typescript con tsc e ho ottenuto questi errori:\n"
            f"```typescript\n{ts_report}\n```\n\n"
            "Correggili usando il formato di output XML già concordato "
            "(omettendo i comandi <shell>, mi arrangio io rifare il controllo tsc)."
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
            cmd_init(auto_input=prompt_message_init)
            
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
    # 2. Esecuzione Repomix per ottenere la lista file attuale
    print_step("Esecuzione Repomix per analisi struttura...")
    global CURRENT_TEMP_DIR
    CURRENT_TEMP_DIR = setup_temp_dir()
    temp_repomix_out = os.path.join(CURRENT_TEMP_DIR, "structure_check.xml")
    
    run_command(f"repomix --style xml --output {temp_repomix_out} --quiet", capture=False)

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
    global CURRENT_TEMP_DIR
    CURRENT_TEMP_DIR = setup_temp_dir()
    
    repomix_path = os.path.join(CURRENT_TEMP_DIR, REPOMIX_OUTPUT_FILENAME)
    print_step("Generazione Repomix aggiornato...")
    
    # Crea repomixignore se non esiste (come in init)
    # Crea repomixignore se non esiste (come in init)
    if not os.path.exists(REPOMIX_IGNORE):
         with open(REPOMIX_IGNORE, "w") as f:
            f.write("node_modules/**\n.git/**\n.next/**\ndist/**\nbuild/**\npackage-lock.json\npnpm-lock.yaml\n**/*.pyc")

    run_command(f"repomix . --style xml --output {repomix_path} --quiet", capture=False)
    
    if not os.path.exists(repomix_path):
        print_error("Repomix fallito.")
        return

    tree_str = generate_project_tree()
    patch_repomix_with_tree(repomix_path, tree_str)

    # I file sono garantiti da ensure_prompts_exist()

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

    prompt_path = os.path.join(CURRENT_TEMP_DIR, PROMPT_FILENAME)
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
        open_folder(CURRENT_TEMP_DIR)
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
            idx = snip.get('index', 'N/A')
            o_node = snip.find('original')
            e_node = snip.find('edit')
            
            o_txt = clean_code_content(o_node.text) if o_node is not None else ""
            e_txt = clean_code_content(e_node.text) if e_node is not None else ""
            
            # INVERSIONE REALE: cerchiamo 'edit' e ripristiniamo 'original'
            if apply_snippet_fuzzy(p, e_txt, o_txt, snippet_index=idx): 
                count += 1
            else: 
                fails.append((p, idx))
                
        save_state()
        
        if fails:
            print_error(f"❌ {len(fails)} snippet non invertiti (possibili modifiche manuali intercorse).")
            
            fails_by_file = {}
            for f_path, idx in fails:
                if f_path not in fails_by_file:
                    fails_by_file[f_path] = []
                fails_by_file[f_path].append(idx)
            
            file_list_str = "\n".join([f"- {path} (Snippet {', '.join(indices)})" for path, indices in fails_by_file.items()])
            
            recovery_prompt = f"Le seguenti patch in modalità Snippet non hanno funzionato in undo:\n{file_list_str}\n\nTi fornisco di seguito il contenuto AGGIORNATO e REALE di questi file.\nPer favore, analizza le tue modifiche precedenti e ripristina il codice allo stato originale per questi file, rispettando le nostre regole standard (usa FULL REWRITE se il file è molto piccolo, usa SNIPPET se è grande ma assicurati che <original> corrisponda esattamente a quanto vedi qui sotto):\n\n"
            
            for f_path in fails_by_file.keys():
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

def cmd_best():
    ensure_prompts_exist()
    if not os.path.exists(PROMPT_BEST_PRACTICE_FILE):
        return print_error(f"File {PROMPT_BEST_PRACTICE_FILE} non trovato.")
        
    print_step(f"Apertura di {PROMPT_BEST_PRACTICE_FILE} ...")
    
    try:
        # Tenta di aprire con VS Code
        subprocess.run(f'code "{PROMPT_BEST_PRACTICE_FILE}"', shell=True, check=True)
        print_success("File aperto in VS Code.")
    except Exception as e:
        print_warn(f"Impossibile aprire con 'code' ({e}). Tento con l'apertura di sistema...")
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(PROMPT_BEST_PRACTICE_FILE)
            elif system == "Darwin":
                subprocess.run(["open", PROMPT_BEST_PRACTICE_FILE])
            else:
                subprocess.run(["xdg-open", PROMPT_BEST_PRACTICE_FILE])
            print_success("File aperto con l'applicazione predefinita.")
        except Exception as fallback_e:
            print_error(f"Impossibile aprire il file: {fallback_e}")

def main():
    if len(sys.argv) < 2: cmd_apply()
    action = sys.argv[1]
    if action == "init":
        compress_mode = len(sys.argv) > 2 and sys.argv[2] in ["comp", "compress"]
        cmd_init(compress_mode=compress_mode)
    elif action == "apply": cmd_apply()
    elif action == "mod": cmd_mod()
    elif action == "check":
        strict_mode = True
        if len(sys.argv) > 2 and sys.argv[2] in["no-strict", "lasca", "permissiva", "permissivo", "veloce", "fast"]:
            strict_mode = False
        cmd_check(strict_mode=strict_mode)
    elif action == "ignore": cmd_ignore()
    elif action == "new": cmd_new()
    elif action in ["invert", "undo", "annulla", "cancel", "ripristina"]: cmd_invert()
    elif action in["best", "bestpractice", "best-practice", "best_practice", "bestpractices", "best-practices", "best_practices"]: cmd_best()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Cattura CTRL+C globale (utile nei menu input standard)
        cleanup_and_exit()