import os
import shutil
import time
import threading
import queue
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Tuple, Optional, List

# Audio metadata libraries
import mutagen
from tinytag import TinyTag

SUPPORTED_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", 
    ".flac", ".ogg", ".opus", ".wma"
}

# --- THEME CONSTANTS ---
BG_MAIN = "#1e1e2e"       # Dark Slate / Mocha
BG_CARD = "#25263a"       # Slightly lighter card panel
BG_ENTRY = "#181825"      # Input background
FG_TEXT = "#cdd6f4"       # Primary light text
FG_MUTED = "#a6adc8"      # Subdued text
ACCENT_PRIMARY = "#89b4fa"# Vibrant Blue
ACCENT_SUCCESS = "#a6e3a1"# Soft Green
ACCENT_WARN = "#f9e2af"   # Muted Yellow
ACCENT_DANGER = "#f38ba8" # Coral Red
FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"


def get_audio_duration(file_path: str) -> Optional[float]:
    """
    Extract exact duration in seconds from an audio file.
    Attempts mutagen first; falls back to TinyTag.
    """
    try:
        audio = mutagen.File(file_path)
        if audio is not None and audio.info is not None and hasattr(audio.info, 'length'):
            if audio.info.length > 0:
                return float(audio.info.length)
    except Exception:
        pass

    try:
        tag = TinyTag.get(file_path)
        if tag.duration is not None and tag.duration > 0:
            return float(tag.duration)
    except Exception:
        pass

    return None


def resolve_destination_filename(dest_folder: str, filename: str) -> str:
    """Returns a unique target path in dest_folder, resolving duplicate collisions."""
    base_name, ext = os.path.splitext(filename)
    counter = 1
    target_path = os.path.join(dest_folder, filename)
    
    while os.path.exists(target_path):
        target_path = os.path.join(dest_folder, f"{base_name}_{counter}{ext}")
        counter += 1
        
    return target_path


class AudioOrganizerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Audio Length Organizer Pro")
        self.geometry("780x720")
        self.minsize(700, 650)
        self.configure(bg=BG_MAIN)

        self.is_processing = False
        self.msg_queue = queue.Queue()

        self._configure_styles()
        self._build_ui()
        self.after(100, self._process_queue)

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Global Frame Styling
        style.configure("TFrame", background=BG_MAIN)
        style.configure("Card.TFrame", background=BG_CARD, relief="flat", borderwidth=0)
        
        # Labels
        style.configure("TLabel", background=BG_MAIN, foreground=FG_TEXT, font=(FONT_FAMILY, 10))
        style.configure("Card.TLabel", background=BG_CARD, foreground=FG_TEXT, font=(FONT_FAMILY, 10))
        style.configure("Header.TLabel", background=BG_MAIN, foreground=FG_TEXT, font=(FONT_FAMILY, 16, "bold"))
        style.configure("SubHeader.TLabel", background=BG_MAIN, foreground=FG_MUTED, font=(FONT_FAMILY, 9))
        style.configure("CardHeader.TLabel", background=BG_CARD, foreground=ACCENT_PRIMARY, font=(FONT_FAMILY, 11, "bold"))
        
        # Entries & Comboboxes
        style.configure("TEntry", fieldbackground=BG_ENTRY, foreground=FG_TEXT, insertcolor=FG_TEXT, borderwidth=1)
        style.map("TEntry", bordercolor=[("focus", ACCENT_PRIMARY)])
        
        style.configure("TCombobox", fieldbackground=BG_ENTRY, background=BG_CARD, foreground=FG_TEXT, arrowcolor=FG_TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", BG_ENTRY)])

        # Buttons
        style.configure("TButton", font=(FONT_FAMILY, 9, "bold"), background=BG_CARD, foreground=FG_TEXT, borderwidth=1, focuscolor="none")
        style.map("TButton", background=[("active", ACCENT_PRIMARY)], foreground=[("active", BG_MAIN)])

        style.configure("Primary.TButton", font=(FONT_FAMILY, 11, "bold"), background=ACCENT_PRIMARY, foreground=BG_MAIN, borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#b4befe")], foreground=[("active", BG_MAIN)])

        # Checkbuttons & Radiobuttons
        style.configure("Card.TCheckbutton", background=BG_CARD, foreground=FG_TEXT, font=(FONT_FAMILY, 10))
        style.configure("Card.TRadiobutton", background=BG_CARD, foreground=FG_TEXT, font=(FONT_FAMILY, 10))
        style.map("Card.TCheckbutton", background=[("active", BG_CARD)])
        style.map("Card.TRadiobutton", background=[("active", BG_CARD)])

        # Progressbar
        style.configure("Custom.Horizontal.TProgressbar", troughcolor=BG_ENTRY, background=ACCENT_PRIMARY, thickness=12, borderwidth=0)

    def _build_ui(self):
        main_layout = ttk.Frame(self, padding="20")
        main_layout.pack(fill=tk.BOTH, expand=True)

        # Header Section
        header_frame = ttk.Frame(main_layout)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="Audio Length Organizer", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(header_frame, text="Automatically scan, categorize, and structure your audio library by duration.", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(2, 0))

        # --- Card 1: Directory Paths ---
        paths_card = ttk.Frame(main_layout, style="Card.TFrame", padding="15")
        paths_card.pack(fill=tk.X, pady=(0, 15))
        paths_card.columnconfigure(1, weight=1)

        ttk.Label(paths_card, text="DIRECTORY CONFIGURATION", style="CardHeader.TLabel").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        ttk.Label(paths_card, text="Source Folder:", style="Card.TLabel").grid(row=1, column=0, sticky=tk.W, pady=6)
        self.src_var = tk.StringVar()
        ttk.Entry(paths_card, textvariable=self.src_var).grid(row=1, column=1, sticky=tk.EW, padx=10, pady=6)
        ttk.Button(paths_card, text="Browse", command=self._browse_src, width=10).grid(row=1, column=2, pady=6)

        ttk.Label(paths_card, text="Destination Folder:", style="Card.TLabel").grid(row=2, column=0, sticky=tk.W, pady=6)
        self.dest_var = tk.StringVar()
        ttk.Entry(paths_card, textvariable=self.dest_var).grid(row=2, column=1, sticky=tk.EW, padx=10, pady=6)
        ttk.Button(paths_card, text="Browse", command=self._browse_dest, width=10).grid(row=2, column=2, pady=6)

        # --- Card 2: Filter Rules & Settings ---
        rules_card = ttk.Frame(main_layout, style="Card.TFrame", padding="15")
        rules_card.pack(fill=tk.X, pady=(0, 15))
        rules_card.columnconfigure(1, weight=1)

        ttk.Label(rules_card, text="FILTER & OPERATION RULES", style="CardHeader.TLabel").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        # Duration Rule Input
        ttk.Label(rules_card, text="Maximum Duration:", style="Card.TLabel").grid(row=1, column=0, sticky=tk.W, pady=6)
        
        dur_input_frame = ttk.Frame(rules_card, style="Card.TFrame")
        dur_input_frame.grid(row=1, column=1, sticky=tk.W, padx=10, pady=6)
        
        self.duration_var = tk.StringVar(value="15")
        ttk.Entry(dur_input_frame, textvariable=self.duration_var, width=12).pack(side=tk.LEFT, padx=(0, 8))

        self.unit_var = tk.StringVar(value="Seconds")
        unit_cb = ttk.Combobox(dur_input_frame, textvariable=self.unit_var, values=["Seconds", "Minutes"], state="readonly", width=10)
        unit_cb.pack(side=tk.LEFT)

        # Mode Selection
        ttk.Label(rules_card, text="File Mode:", style="Card.TLabel").grid(row=2, column=0, sticky=tk.W, pady=6)
        self.operation_var = tk.StringVar(value="COPY")
        op_frame = ttk.Frame(rules_card, style="Card.TFrame")
        op_frame.grid(row=2, column=1, sticky=tk.W, padx=10, pady=6)
        
        ttk.Radiobutton(op_frame, text="Copy (Safe)", variable=self.operation_var, value="COPY", style="Card.TRadiobutton").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(op_frame, text="Move (Relocate)", variable=self.operation_var, value="MOVE", style="Card.TRadiobutton").pack(side=tk.LEFT)

        # Subfolders Option
        self.subfolder_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(rules_card, text="Scan Subdirectories Recursively", variable=self.subfolder_var, style="Card.TCheckbutton").grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

        # --- Action Button ---
        self.btn_run = ttk.Button(main_layout, text="START ORGANIZING", style="Primary.TButton", command=self._start_processing)
        self.btn_run.pack(fill=tk.X, ipady=8, pady=(0, 15))

        # --- Card 3: Status & Console ---
        status_card = ttk.Frame(main_layout, style="Card.TFrame", padding="15")
        status_card.pack(fill=tk.BOTH, expand=True)

        ttk.Label(status_card, text="LIVE EXECUTION CONSOLE", style="CardHeader.TLabel").pack(anchor=tk.W, pady=(0, 8))

        self.progress_bar = ttk.Progressbar(status_card, style="Custom.Horizontal.TProgressbar", orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        # Metrics Bar
        self.lbl_stats = ttk.Label(
            status_card, 
            text="Scanned: 0 | Audio Found: 0 | Matched: 0 | Processed: 0 | Skipped: 0 | Errors: 0", 
            style="Card.TLabel"
        )
        self.lbl_stats.pack(anchor=tk.W, pady=(0, 8))

        # Terminal Console Output Window
        console_frame = ttk.Frame(status_card, style="Card.TFrame")
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            console_frame, 
            bg=BG_ENTRY, 
            fg=FG_TEXT, 
            selectbackground=ACCENT_PRIMARY,
            selectforeground=BG_MAIN,
            relief="flat",
            font=("Consolas", 9),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        
        scrollbar = ttk.Scrollbar(console_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Custom text color tags for logs
        self.log_text.tag_config("OK", foreground=ACCENT_SUCCESS)
        self.log_text.tag_config("SKIP", foreground=ACCENT_WARN)
        self.log_text.tag_config("ERR", foreground=ACCENT_DANGER)
        self.log_text.tag_config("INFO", foreground=ACCENT_PRIMARY)

    def _browse_src(self):
        path = filedialog.askdirectory(title="Select Source Directory")
        if path:
            self.src_var.set(os.path.normpath(path))

    def _browse_dest(self):
        path = filedialog.askdirectory(title="Select Destination Directory")
        if path:
            self.dest_var.set(os.path.normpath(path))

    def _append_log(self, msg: str, tag: str = None):
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {msg}\n"
        
        if tag:
            self.log_text.insert(tk.END, formatted_msg, tag)
        else:
            self.log_text.insert(tk.END, formatted_msg)
            
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _start_processing(self):
        if self.is_processing:
            return

        src = os.path.abspath(self.src_var.get().strip())
        dest = os.path.abspath(self.dest_var.get().strip())
        dur_str = self.duration_var.get().strip()
        unit = self.unit_var.get()
        operation = self.operation_var.get()
        include_subfolders = self.subfolder_var.get()

        if not src or not os.path.exists(src):
            messagebox.showerror("Invalid Path", f"Source folder path is invalid or missing:\n{src}")
            return
        if not dest:
            messagebox.showerror("Invalid Path", "Please specify a Destination directory.")
            return

        try:
            val = float(dur_str)
            if val <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Invalid Input", "Maximum Duration must be a positive number.")
            return

        target_limit_sec = val * 60.0 if unit == "Minutes" else val

        if src == dest:
            messagebox.showerror("Path Collision", "Source and Destination folders cannot be identical.")
            return

        if operation == "MOVE":
            if not messagebox.askyesno("Confirm Move Operation", "Moving files will permanently relocate them from the source folder.\n\nAre you sure you want to proceed?"):
                return

        # Prepare GUI for execution
        self.is_processing = True
        self.btn_run.config(state=tk.DISABLED)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0

        self._append_log("Initializing audio organizer thread...", "INFO")

        threading.Thread(
            target=self._worker_process,
            args=(src, dest, target_limit_sec, unit, dur_str, operation, include_subfolders),
            daemon=True
        ).start()

    def _worker_process(self, src: str, dest: str, limit_sec: float, unit: str, dur_raw: str, operation: str, subfolders: bool):
        start_time = time.time()
        folder_tag = f"≤ {dur_raw} {unit}"
        out_directory = os.path.join(dest, folder_tag)
        
        try:
            os.makedirs(out_directory, exist_ok=True)
        except Exception as e:
            self.msg_queue.put(("LOG", (f"Failed to create output directory: {e}", "ERR")))
            self.msg_queue.put(("FINISH", None))
            return

        abs_out = os.path.abspath(out_directory)
        file_list = []
        scanned_count = 0

        self.msg_queue.put(("LOG", (f"Scanning directory: {src}", "INFO")))

        # File Discovery
        for root, dirs, files in os.walk(src):
            abs_root = os.path.abspath(root)

            # Avoid recursively re-scanning output folder if inside source
            if abs_out.startswith(abs_root) and abs_out != abs_root:
                dirs.clear()
                continue

            for f in files:
                scanned_count += 1
                ext = os.path.splitext(f)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    file_list.append(os.path.join(root, f))
            
            if not subfolders:
                break

        audio_found = len(file_list)
        self.msg_queue.put(("LOG", (f"Scan completed. Discovered {audio_found} audio files across {scanned_count} total files.", "INFO")))

        matching_count = 0
        processed_count = 0
        skipped_count = 0
        error_count = 0

        self.msg_queue.put(("UPDATE_STATS", (scanned_count, audio_found, matching_count, processed_count, skipped_count, error_count)))

        for idx, file_path in enumerate(file_list):
            filename = os.path.basename(file_path)
            duration = get_audio_duration(file_path)

            if duration is None:
                error_count += 1
                self.msg_queue.put(("LOG", (f"[ERROR] {filename} — Could not read metadata/duration", "ERR")))
            elif duration <= limit_sec:
                matching_count += 1
                target_file_path = resolve_destination_filename(out_directory, filename)
                try:
                    if operation == "COPY":
                        shutil.copy2(file_path, target_file_path)
                        self.msg_queue.put(("LOG", (f"[COPY OK] {filename} ({duration:.2f}s) -> {os.path.basename(target_file_path)}", "OK")))
                    else:
                        shutil.move(file_path, target_file_path)
                        self.msg_queue.put(("LOG", (f"[MOVE OK] {filename} ({duration:.2f}s) -> {os.path.basename(target_file_path)}", "OK")))
                    processed_count += 1
                except Exception as e:
                    error_count += 1
                    self.msg_queue.put(("LOG", (f"[ERROR] {filename} — File operation failed: {e}", "ERR")))
            else:
                skipped_count += 1
                self.msg_queue.put(("LOG", (f"[SKIP] {filename} ({duration:.2f}s) > Limit ({limit_sec:.2f}s)", "SKIP")))

            progress = int(((idx + 1) / audio_found) * 100) if audio_found > 0 else 100
            self.msg_queue.put(("PROGRESS", progress))
            self.msg_queue.put(("UPDATE_STATS", (scanned_count, audio_found, matching_count, processed_count, skipped_count, error_count)))

        elapsed_time = time.time() - start_time
        summary = f"Execution Finished in {elapsed_time:.2f}s. Total Audio Processed: {processed_count}."
        self.msg_queue.put(("LOG", (summary, "INFO")))
        self.msg_queue.put(("FINISH", None))

    def _process_queue(self):
        try:
            while True:
                msg_type, payload = self.msg_queue.get_nowait()
                if msg_type == "LOG":
                    text, tag = payload
                    self._append_log(text, tag)
                elif msg_type == "PROGRESS":
                    self.progress_bar['value'] = payload
                elif msg_type == "UPDATE_STATS":
                    scanned, audio, matched, proc, skipped, err = payload
                    self.lbl_stats.config(
                        text=f"Scanned: {scanned} | Audio Found: {audio} | Matched: {matched} | Processed: {proc} | Skipped: {skipped} | Errors: {err}"
                    )
                elif msg_type == "FINISH":
                    self.is_processing = False
                    self.btn_run.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        self.after(100, self._process_queue)


if __name__ == "__main__":
    app = AudioOrganizerApp()
    app.mainloop()