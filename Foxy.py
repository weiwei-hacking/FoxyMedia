import sys
import subprocess

# ==========================================
# 1. 自動檢查並安裝缺少套件的啟動器
# ==========================================
REQUIRED_PACKAGES = ["yt-dlp"]

def install_and_bootstrap():
    """在腳本執行前，自動檢查並安裝缺少的第三方套件"""
    try:
        from importlib.metadata import distributions
        installed = {d.metadata['Name'].lower() for d in distributions()}
    except ImportError:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}

    missing_packages = []
    for pkg in REQUIRED_PACKAGES:
        if pkg.lower().replace('_', '-') not in installed:
            missing_packages.append(pkg)

    if missing_packages:
        print("=" * 50)
        print("Detecting missing required packages...")
        print(f"Installing: {', '.join(missing_packages)}")
        print("=" * 50)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
            print("\nAll packages installed successfully!\n")
        except subprocess.CalledProcessError as e:
            print(f"\n[Error] Failed to install dependencies automatically: {e}")
            print("Please run 'pip install yt-dlp' manually.")
            input("Press Enter to exit...")
            sys.exit(1)

install_and_bootstrap()

# ==========================================
# 2. FoxyMedia 主程式邏輯 (內建標準庫)
# ==========================================
import os
import json
import time
import shutil
import msvcrt
import zipfile
import urllib.request
import winreg  # 引入 Windows 登錄表模組，用來永久修改 PATH
import tkinter as tk
from tkinter import filedialog

os.system('')

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

FOXY_DIR = os.path.join(os.environ['USERPROFILE'], 'Documents', 'FoxyMedia')
CFG_PATH = os.path.join(FOXY_DIR, 'FoxyMediaCFG.json')
BACKUP_PATH = os.path.join(FOXY_DIR, 'FoxyMediaCFG_backup.json')
DEFAULT_DOWNLOAD_PATH = os.path.join(os.environ['USERPROFILE'], 'Downloads')
DEFAULT_FFMPEG_PATH = 'ffmpeg'

def load_config():
    default_cfg = {
        "download_path": DEFAULT_DOWNLOAD_PATH,
        "ffmpeg_path": DEFAULT_FFMPEG_PATH
    }
    if not os.path.exists(FOXY_DIR):
        os.makedirs(FOXY_DIR)
        
    if os.path.exists(CFG_PATH):
        try:
            with open(CFG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default_cfg
    else:
        with open(CFG_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_cfg, f, indent=4, ensure_ascii=False)
        return default_cfg

current_cfg = load_config()
temp_cfg = current_cfg.copy()

def save_config():
    global current_cfg
    current_cfg = temp_cfg.copy()
    if os.path.exists(CFG_PATH):
        shutil.copyfile(CFG_PATH, BACKUP_PATH)
    with open(CFG_PATH, 'w', encoding='utf-8') as f:
        json.dump(current_cfg, f, indent=4, ensure_ascii=False)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_key():
    ch = msvcrt.getch()
    if ch in (b'\x00', b'\xe0'):
        msvcrt.getch()
        return ""
    try:
        return ch.decode('utf-8')
    except:
        return ""

def print_centered_block(title, lines):
    """改良版置中排版：確保標題能與內容對齊，不被擠出螢幕"""
    terminal_width = shutil.get_terminal_size().columns
    if terminal_width < 20: 
        terminal_width = 80  # 防止獲取到錯誤的視窗寬度
        
    def get_visible_len(s):
        return len(s.replace(RED, '').replace(GREEN, '').replace(YELLOW, '').replace(RESET, ''))
    
    # 計算內容中最長的一行
    max_len = max(get_visible_len(line) for line in lines) if lines else 0
    title_len = get_visible_len(title)
    
    # 決定基準對齊點（以最長的內容或標題為準）
    base_len = max(max_len, title_len)
    pad_left = (terminal_width - base_len) // 2
    if pad_left < 0: pad_left = 0
    indent = " " * pad_left
    
    # 印出標題（相對於內容區塊做微調置中）
    if title:
        title_pad = pad_left + (base_len - title_len) // 2
        print(" " * title_pad + title)
        print()
        
    # 印出內容
    for line in lines:
        print(f"{indent}{line}")

def select_directory(initial_dir):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askdirectory(initialdir=initial_dir, title="Select Download Folder")
    root.destroy()
    return os.path.normpath(path) if path else ""

def select_ffmpeg_exe(initial_dir):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askopenfilename(
        initialdir=initial_dir, 
        title="Select ffmpeg.exe",
        filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
    )
    root.destroy()
    return os.path.normpath(path) if path else ""

def open_folder_and_select_file(file_path):
    if file_path and os.path.exists(file_path):
        subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])
    else:
        download_dir = current_cfg['download_path']
        if os.path.exists(download_dir):
            subprocess.run(['explorer', os.path.normpath(download_dir)])

def get_latest_downloaded_file(download_dir):
    try:
        files = [os.path.join(download_dir, f) for f in os.listdir(download_dir)]
        files = [f for f in files if os.path.isfile(f)]
        # 過濾掉獨立的圖片檔案，確保抓到的是影片或音樂主檔
        files = [f for f in files if not f.lower().endswith(('.png', '.webp', '.jpg', '.jpeg'))]
        if not files: return None
        return max(files, key=os.path.getmtime)
    except:
        return None

def post_download_menu(downloaded_file_path, mode_name):
    while True:
        clear_screen()
        display_path = downloaded_file_path if downloaded_file_path else os.path.join(current_cfg['download_path'], "your_file.xxx")
        lines = [
            f"Your content is downloaded, your file in the {display_path}",
            "",
            "[1] Open Folder",
            f"[2] Keep {mode_name} Mode",
            "[0] Back to menu"
        ]
        print_centered_block("FoxyMedia - Download Completed", lines)
        
        key = get_key()
        if key == '1':
            open_folder_and_select_file(downloaded_file_path)
        elif key == '2':
            return "keep"
        elif key == '0':
            return "menu"

def add_to_user_path_permanently(path_to_add):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            current_path, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            current_path = ""

        norm_paths = [os.path.normpath(p.strip()) for p in current_path.split(';') if p.strip()]
        if os.path.normpath(path_to_add) not in norm_paths:
            new_path = current_path + (";" if current_path and not current_path.endswith(';') else "") + path_to_add
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
            
            try:
                import ctypes
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                ctypes.windll.user32.PostMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment")
            except:
                pass
            return True
        winreg.CloseKey(key)
    except Exception as e:
        print(f"{RED}Warning: Could not write to Windows Registry permanently: {e}{RESET}")
    return False

def run_ffmpeg_patcher():
    clear_screen()
    print("=== FFmpeg Patcher ===")
    
    temp_cfg['ffmpeg_path'] = DEFAULT_FFMPEG_PATH
    print("Checking system PATH for ffmpeg...")
    
    ffmpeg_in_path = shutil.which("ffmpeg")
    
    if ffmpeg_in_path:
        print(f"{GREEN}Success: FFmpeg already exists in your system PATH!{RESET}")
        print("Set FFmpeg path option to default successfully.")
        print("\nPress any key to back to settings...")
        get_key()
        return

    print(f"{YELLOW}FFmpeg not found in system PATH. Preparing to download...{RESET}")
    
    target_exe = os.path.join(FOXY_DIR, "ffmpeg.exe")
    zip_tmp = os.path.join(FOXY_DIR, "ffmpeg_tmp.zip")
    
    url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    try:
        if os.path.exists(target_exe):
            os.remove(target_exe)
            
        print("Downloading FFmpeg Static package (This may take a moment)...")
        urllib.request.urlretrieve(url, zip_tmp)
        print("Extracting ffmpeg.exe...")
        
        with zipfile.ZipFile(zip_tmp, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith("ffmpeg.exe"):
                    with zip_ref.open(file_info) as source_file:
                        with open(target_exe, "wb") as target_file:
                            shutil.copyfileobj(source_file, target_file)
                    break
        
        if os.path.exists(zip_tmp):
            os.remove(zip_tmp)
            
        print(f"{GREEN}Successfully downloaded 100% standalone ffmpeg.exe to {FOXY_DIR}{RESET}")
        
        if FOXY_DIR not in os.environ['PATH']:
            os.environ['PATH'] = FOXY_DIR + os.pathsep + os.environ['PATH']
            
        if add_to_user_path_permanently(FOXY_DIR):
            print(f"{GREEN}Successfully and PERMANENTLY added {FOXY_DIR} to your Windows User PATH!{RESET}")
            print("Next time you open a new Command Prompt, 'ffmpeg' will be globally available.")
        else:
            print(f"{YELLOW}Path already exists in Windows Registry or was skipped.{RESET}")
            
    except Exception as e:
        print(f"{RED}Failed to download FFmpeg: {e}{RESET}")
        if os.path.exists(zip_tmp): os.remove(zip_tmp)
        
    print("\nPress any key to back to settings...")
    get_key()

# --- 主要模式 ---

def manual_mode():
    while True:
        clear_screen()
        print("[yt-dlp] Command Header")
        print("[back] Back to menu")
        print("-" * 40)
        cmd_input = input("Enter command: ").strip()
        
        if cmd_input.lower() == 'back':
            break
            
        if cmd_input.startswith("yt-dlp"):
            cmd_args = cmd_input.split()
            extra_args = []
            
            exe_patch_path = os.path.join(FOXY_DIR, "ffmpeg.exe")
            if "--ffmpeg-location" not in cmd_input:
                if current_cfg['ffmpeg_path'] != DEFAULT_FFMPEG_PATH:
                    cmd_args.extend(["--ffmpeg-location", current_cfg['ffmpeg_path']])
                elif os.path.exists(exe_patch_path):
                    cmd_args.extend(["--ffmpeg-location", exe_patch_path])
                    
            if "-P" not in cmd_input and "--paths" not in cmd_input:
                extra_args.extend(["-P", current_cfg['download_path']])
                
            final_cmd = [cmd_args[0]] + extra_args + cmd_args[1:]
            print(f"\nExecuting: {' '.join(final_cmd)}\n")
            subprocess.run(final_cmd, shell=True)
            
            latest = get_latest_downloaded_file(current_cfg['download_path'])
            if post_download_menu(latest, "Manual") == "menu":
                break

def wizard_mode():
    while True:
        clear_screen()
        lines = [
            "Welcome to use FoxyMedia Wizard Mode, you just need answer some questions and your download will start",
            "",
            "[1] Start",
            "[0] Back to menu"
        ]
        print_centered_block("FoxyMedia - Wizard Mode", lines)
        
        key = get_key()
        if key == '0':
            break
        elif key == '1':
            clear_screen()
            print("=== FoxyMedia Wizard Mode ===")
            url = input("What content you want download? (Paste URL and press Enter): ").strip()
            
            print("You want save it as [V] video or [A] audio only? ", end="", flush=True)
            while (v_or_a := get_key().upper()) not in ['V', 'A']: pass
            print(v_or_a)
            
            print("You want save [Y] thumbnails or [N] not? ", end="", flush=True)
            while (thumb := get_key().upper()) not in ['Y', 'N']: pass
            print(thumb)
            
            print("You want save it with [Y] custom name or [N] not? ", end="", flush=True)
            while (cust_name_choice := get_key().upper()) not in ['Y', 'N']: pass
            print(cust_name_choice)
            
            custom_name = ""
            if cust_name_choice == 'Y':
                custom_name = input("Enter custom filename (without extension): ").strip()
                
            print("\nHere is your answer, want start download?")
            print("[Y] Start")
            print("[C] Cancel")
            while (start_choice := get_key().upper()) not in ['Y', 'C']: pass
            
            if start_choice == 'C': continue
                
            cmd = ["yt-dlp"]
            
            exe_patch_path = os.path.join(FOXY_DIR, "ffmpeg.exe")
            if current_cfg['ffmpeg_path'] != DEFAULT_FFMPEG_PATH:
                cmd.extend(["--ffmpeg-location", current_cfg['ffmpeg_path']])
            elif os.path.exists(exe_patch_path):
                cmd.extend(["--ffmpeg-location", exe_patch_path])
                
            cmd.extend(["-P", current_cfg['download_path']])
            
            if v_or_a == 'V':
                cmd.extend([
                    "-f", "bv*[vcodec*=avc1]+ba[ext=m4a]/b[ext=mp4]",
                    "--merge-output-format", "mp4"
                ])
            else:
                cmd.extend([
                    "-x", 
                    "--audio-format", "mp3", 
                    "--audio-quality", "320K", 
                    "--force-overwrites"
                ])
                
            if thumb == 'Y': 
                # 修正：加上命令，指示 yt-dlp 在成功內嵌封面到影片/音訊後，自動將外面獨立的圖片暫存檔給刪除！
                cmd.extend(["--embed-thumbnail", "--convert-thumbnails", "png"])
                
            cmd.append("--no-playlist")
            
            if custom_name: cmd.extend(["-o", f"{custom_name}.%(ext)s"])
            else: cmd.extend(["-o", "%(title)s.%(ext)s"])
            cmd.append(url)
            
            clear_screen()
            print("Executing Wizard Download & Post-Processing...\n")
            subprocess.run(cmd, shell=True)
            
            # 安全防護：用 Python 再做一次保險清理，把殘留下來跟影片同名的獨立圖檔刪掉
            try:
                time.sleep(1) # 等檔案寫入完畢
                for item in os.listdir(current_cfg['download_path']):
                    if item.lower().endswith(('.webp', '.png', '.jpg')):
                        item_path = os.path.join(current_cfg['download_path'], item)
                        # 如果有與它對應的 mp4 檔存在，表示它是多出來的縮圖，直接刪除
                        base_name, _ = os.path.splitext(item)
                        if os.path.exists(os.path.join(current_cfg['download_path'], base_name + ".mp4")) or \
                           os.path.exists(os.path.join(current_cfg['download_path'], base_name + ".mp3")):
                            os.remove(item_path)
            except:
                pass
            
            latest = get_latest_downloaded_file(current_cfg['download_path'])
            if post_download_menu(latest, "Wizard") == "menu":
                break

def settings_menu():
    global temp_cfg
    while True:
        clear_screen()
        
        c1 = RED if temp_cfg['download_path'] != current_cfg['download_path'] else RESET
        c2 = RED if temp_cfg['ffmpeg_path'] != current_cfg['ffmpeg_path'] else RESET
        c4 = RED if temp_cfg != current_cfg and temp_cfg['download_path'] == DEFAULT_DOWNLOAD_PATH and temp_cfg['ffmpeg_path'] == DEFAULT_FFMPEG_PATH else RESET
        
        lines = [
            f"{c1}[1] Change downloaded path{RESET}",
            f"{c2}[2] Change FFmpeg.exe path{RESET}",
            "[3] FFmpeg Patcher",
            f"{c4}[4] RESET ALL THING{RESET}",
            "[X] Don't Save and Back to menu",
            "[0] Save and Back to menu"
        ]
        
        print_centered_block("FoxyMedia - Settings", lines)
        
        key = get_key().upper()
        if key == '0':
            save_config()
            break
        elif key == 'X':
            temp_cfg = current_cfg.copy()
            break
        elif key == '4':
            temp_cfg['download_path'] = DEFAULT_DOWNLOAD_PATH
            temp_cfg['ffmpeg_path'] = DEFAULT_FFMPEG_PATH
        elif key == '1':
            path_setting_flow('download')
        elif key == '2':
            path_setting_flow('ffmpeg')
        elif key == '3':
            run_ffmpeg_patcher()

def path_setting_flow(mode):
    global temp_cfg
    orig_path = temp_cfg['download_path'] if mode == 'download' else temp_cfg['ffmpeg_path']
    show_orig = False
    
    while True:
        clear_screen()
        curr_val = temp_cfg['download_path'] if mode == 'download' else temp_cfg['ffmpeg_path']
        lines = []
        if show_orig:
            label_orig = "Original downloaded path" if mode == 'download' else "Original ffmpeg path"
            lines.append(f"{label_orig} - {orig_path}")
            
        label_curr = "Current downloaded path" if mode == 'download' else "Current ffmpeg path"
        lines.append(f"{label_curr} - {curr_val}")
        lines.extend(["", "[1] Modify", "[2] Set to default setting", "[0] Back to settings"])
        
        title = "Settings - Download Path" if mode == 'download' else "Settings - FFmpeg Path"
        print_centered_block(title, lines)
        
        key = get_key()
        if key == '0': break
        elif key == '2':
            if mode == 'download': temp_cfg['download_path'] = DEFAULT_DOWNLOAD_PATH
            else: temp_cfg['ffmpeg_path'] = DEFAULT_FFMPEG_PATH
            show_orig = True
        elif key == '1':
            if mode == 'download':
                new_path = select_directory(curr_val)
                if new_path: temp_cfg['download_path'] = new_path; show_orig = True
            else:
                new_path = select_ffmpeg_exe(os.path.dirname(curr_val) if os.path.isabs(curr_val) else os.environ['USERPROFILE'])
                if new_path: temp_cfg['ffmpeg_path'] = new_path; show_orig = True

def main():
    if not os.path.exists(FOXY_DIR):
        os.makedirs(FOXY_DIR)
    if FOXY_DIR not in os.environ['PATH']:
        os.environ['PATH'] = FOXY_DIR + os.pathsep + os.environ['PATH']

    print("Initializing FoxyMedia...")
    print("Executing: yt-dlp --update-to master")
    try:
        subprocess.run(["yt-dlp", "--update-to", "master"])
    except FileNotFoundError:
        print(f"{RED}Error: 'yt-dlp' is not installed or not in PATH.{RESET}")
        input("Press Enter to exit...")
        sys.exit(1)
        
    clear_screen()
    quit_confirm = False
    quit_timer = 0
    
    while True:
        clear_screen()
        if quit_confirm and (time.time() - quit_timer > 3):
            quit_confirm = False
            
        quit_label = "[0] Really want quit?" if quit_confirm else "[0] Quit"
        lines = ["[1] Wizard Mode", "[2] Manual Mode", "[3] Settings", quit_label]
        
        # 呼叫修正過的排版區塊，完美顯示標題
        print_centered_block("FoxyMedia - Menu", lines)
        
        key = get_key()
        if key == '1':
            quit_confirm = False; wizard_mode()
        elif key == '2':
            quit_confirm = False; manual_mode()
        elif key == '3':
            quit_confirm = False; settings_menu()
        elif key == '0':
            if quit_confirm:
                clear_screen()
                print("Goodbye!")
                break
            else:
                quit_confirm = True
                quit_timer = time.time()
        else:
            pass

if __name__ == "__main__":
    main()
