import os
import sys
import re
import json
import time
import shutil
import threading
import subprocess
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.simpledialog
import ttkbootstrap as ttkb
import tkinter.font as tkfont
from groq import Groq
import ctypes

# --- Helpers to avoid spawning visible consoles on Windows ---
WINDOWS = os.name == 'nt'

def _subprocess_run(*popenargs, **kwargs):
    """
    Wrapper for subprocess.run that prevents visible console windows on Windows.
    """
    if WINDOWS:
        # Ensure creationflags is set so no console window appears
        kwargs.setdefault('creationflags', subprocess.CREATE_NO_WINDOW)
    return subprocess.run(*popenargs, **kwargs)

def _subprocess_popen(*popenargs, **kwargs):
    """
    Wrapper for subprocess.Popen that prevents visible console windows on Windows.
    """
    if WINDOWS:
        kwargs.setdefault('creationflags', subprocess.CREATE_NO_WINDOW)
    return subprocess.Popen(*popenargs, **kwargs)

def _subprocess_check_call(*popenargs, **kwargs):
    """
    Wrapper for subprocess.check_call that prevents visible console windows on Windows.
    """
    if WINDOWS:
        kwargs.setdefault('creationflags', subprocess.CREATE_NO_WINDOW)
    return subprocess.check_call(*popenargs, **kwargs)

# ----------------------------------------------------------------

import ctypes
import time
import threading

def close_console_after_delay(delay=1.0):
    """Closes the current console window after a short delay (seconds)"""
    def _close():
        time.sleep(delay)
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
    threading.Thread(target=_close, daemon=True).start()

close_console_after_delay(delay=1.0)  # adjust delay as needed


if getattr(sys, 'frozen', False):  # Running as .exe
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ----------------------------

# Line Numbered Text Widget
# ----------------------------
class LineNumberedText(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        
        # Create line numbers widget
        self.line_numbers = tk.Text(self, width=4, padx=4, takefocus=0, border=0,
                                   background="#2d2d2d", foreground="#858585", 
                                   state='disabled', wrap='none')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Create main text widget
        self.text = tk.Text(self, **kwargs)
        self.text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Configure TAB to insert 4 spaces
        self.text.bind('<Tab>', self._insert_tab)
        
        # Create scrollbar with consistent dark theme
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._on_scroll)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure text widget
        self.text.configure(yscrollcommand=self._on_text_scroll)
        self.line_numbers.configure(yscrollcommand=self._on_line_scroll)
        
        # Bind events
        self.text.bind('<KeyPress>', self._on_key_press)
        self.text.bind('<MouseWheel>', self._on_mousewheel)
        self.text.bind('<Button-4>', self._on_mousewheel)
        self.text.bind('<Button-5>', self._on_mousewheel)
        
        # Update line numbers
        self._update_line_numbers()
        
    def _insert_tab(self, event):
        """Insert 4 spaces when TAB key is pressed"""
        self.text.insert(tk.INSERT, " " * 4)
        return "break"  # Prevent default TAB behavior
        
    def _on_scroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)
        
    def _on_text_scroll(self, *args):
        self.scrollbar.set(*args)
        self._on_scroll('moveto', args[0])
        
    def _on_line_scroll(self, *args):
        self.scrollbar.set(*args)
        self._on_scroll('moveto', args[0])
        
    def _on_key_press(self, event=None):
        self._update_line_numbers()
        
    def _on_mousewheel(self, event=None):
        if event.delta:
            self.text.yview_scroll(int(-1*(event.delta/120)), "units")
        else:
            self.text.yview_scroll(int(-1*(event.num)), "units")
        self._update_line_numbers()
        return "break"
        
    def _update_line_numbers(self):
        # Get current line count
        lines = int(self.text.index('end-1c').split('.')[0])
        
        # Update line numbers
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')
        
        for i in range(1, lines + 1):
            self.line_numbers.insert('end', f'{i}\n')
            
        self.line_numbers.config(state='disabled')
        
        # Sync scrolling
        text_yview = self.text.yview()
        self.line_numbers.yview_moveto(text_yview[0])
    
    # Proxy methods for text widget
    def get(self, *args):
        return self.text.get(*args)
        
    def insert(self, *args):
        result = self.text.insert(*args)
        self._update_line_numbers()
        return result
        
    def delete(self, *args):
        result = self.text.delete(*args)
        self._update_line_numbers()
        return result
        
    def tag_configure(self, *args, **kwargs):
        return self.text.tag_configure(*args, **kwargs)
        
    def tag_add(self, *args):
        return self.text.tag_add(*args)
        
    def tag_remove(self, *args):
        return self.text.tag_remove(*args)
        
    def bind(self, *args):
        return self.text.bind(*args)
        
    def see(self, *args):
        return self.text.see(*args)
        
    def index(self, *args):
        return self.text.index(*args)

# ----------------------------
# DarkScrolledText (with line numbers)
# ----------------------------
class DarkScrolledText(tk.Frame):
    def __init__(self, master, **text_kwargs):
        super().__init__(master)
        
        # Use our line numbered text widget
        self.ln_text = LineNumberedText(self,
                            bg="#1e1e1e", fg="#d4d4d4",
                            insertbackground="white",
                            relief=tk.FLAT,
                            **text_kwargs)
        self.ln_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Set text widget reference for compatibility
        self.text = self.ln_text.text

    # proxy methods
    def get(self, *args):
        return self.ln_text.get(*args)

    def insert(self, *args):
        return self.ln_text.insert(*args)

    def delete(self, *args):
        return self.ln_text.delete(*args)

    def tag_configure(self, *args, **kwargs):
        return self.ln_text.tag_configure(*args, **kwargs)

    def tag_add(self, *args):
        return self.ln_text.tag_add(*args)

    def tag_remove(self, *args):
        return self.ln_text.tag_remove(*args)

    def bind(self, *args):
        return self.ln_text.bind(*args)

    def see(self, *args):
        return self.ln_text.see(*args)

# ----------------------------
# Terminal
# ----------------------------
class RealTerminal(tk.Frame):
    def __init__(self, master, project_dir, root, height=10):
        super().__init__(master, bg="#1e1e1e")
        self.root = root
        self.project_dir = project_dir if project_dir else os.path.expanduser("~")
        self._running = True

        # Configure the main frame to expand properly
        self.pack_propagate(False)

        # Terminal header - part of the same resizable element
        header_frame = tk.Frame(self, bg="#1e1e1e", height=25)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        terminal_label = tk.Label(header_frame, text="TERMINAL", bg="#1e1e1e", fg="#888888",
                                 font=("Segoe UI", 9, "bold"), anchor='w')
        terminal_label.pack(fill=tk.X, padx=8, pady=6)

        # Main content area that contains both output and input
        content_frame = tk.Frame(self, bg="#1e1e1e")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Grid inside content_frame so we can reserve space for the input row
        content_frame.grid_rowconfigure(0, weight=8)   
        content_frame.grid_rowconfigure(1, weight=1, minsize=30)  
        content_frame.grid_columnconfigure(0, weight=1)

        self.output = DarkScrolledText(content_frame, height=height, wrap="word")
        self.output.grid(row=0, column=0, sticky="nsew", padx=4, pady=(0, 2))

        # Make output text read-only
        self.output.text.config(state='disabled')

        # Input area - connected visually and functionally
        input_frame = tk.Frame(content_frame, bg="#1e1e1e", height=30)
        # place input_frame in row 1
        input_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))
        input_frame.grid_propagate(False)  # allow explicit minsize to hold

        tk.Label(input_frame, text=">", bg="#1e1e1e", fg="#00ff00",
                font=("Consolas", 10)).pack(side=tk.LEFT, padx=(0, 5))

        self.input_entry = tk.Entry(input_frame, bg="#1e1e1e", fg="#ffffff",
                                    insertbackground="white", relief=tk.FLAT,
                                    font=("Consolas", 10))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", self._on_enter)
        self.input_entry.focus_set()

        self._content_frame = content_frame
        self._input_frame = input_frame
        self._output_widget = self.output

        def _on_content_configure(event):
            # Make input be about ~12% of the terminal height but at least 28 pixels
            total_h = max(1, event.height)
            desired = max(28, int(total_h * 0.12))
            # Update minsize for the input row so it scales proportionally but never disappears
            try:
                content_frame.grid_rowconfigure(1, minsize=desired)
            except Exception:
                pass

        content_frame.bind("<Configure>", _on_content_configure)

        # Start real terminal process
        self.start_terminal_process()

    def start_terminal_process(self):
        """Start a real terminal process"""
        try:
            encoding = 'utf-8'
            if os.name == 'nt':
                oem_cp = ctypes.windll.kernel32.GetOEMCP()
                encoding = f'cp{oem_cp}'
            if os.name == 'nt':  # Windows
                # Use wrapper that prevents creating a separate visible console window
                self.process = _subprocess_popen(
                    ['cmd.exe'],
                    cwd=self.project_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding=encoding,
                    errors='replace',
                    bufsize=1
                )
            else:  # Linux/Mac
                self.process = _subprocess_popen(
                    ['bash'],
                    cwd=self.project_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding=encoding,
                    errors='replace',
                    bufsize=1
                )

            # Start threads to read output
            self._stdout_t = threading.Thread(target=self._read_stdout, daemon=True)
            self._stderr_t = threading.Thread(target=self._read_stderr, daemon=True)
            self._stdout_t.start()
            self._stderr_t.start()

            self._print(f"Terminal started in: {self.project_dir}\n")
            self._print(f"Type commands below...\n{'='*50}\n")
        except Exception as e:
            # If starting the shell failed, print error to embedded terminal area
            self._print(f"Failed to start terminal process: {e}\n")

    def _read_stdout(self):
        """Read stdout from terminal process"""
        while self._running:
            try:
                char = self.process.stdout.read(1)
                if char:
                    self.root.after(0, self._print, char)
            except:
                break

    def _read_stderr(self):
        """Read stderr from terminal process"""
        while self._running:
            try:
                char = self.process.stderr.read(1)
                if char:
                    self.root.after(0, self._print, char)
            except:
                break

    def _print(self, text):
        """Print text to terminal output"""
        try:
            # Enable text widget to insert, then disable again
            self.output.text.config(state='normal')
            self.output.text.insert(tk.END, text)
            self.output.text.config(state='disabled')
            self.output.text.see(tk.END)
        except tk.TclError:
            pass

    def _on_enter(self, event):
        """Handle command input"""
        cmd = self.input_entry.get().strip()
        if not cmd:
            return

        # Echo the command
        self._print(f"> {cmd}\n")

        # Send to process
        try:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
        except Exception as e:
            self._print(f"Error sending command: {e}\n")

        self.input_entry.delete(0, tk.END)

    def send_command(self, cmd):
        """Send a command to the terminal"""
        try:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
            self._print(f"> {cmd}\n")
        except Exception as e:
            self._print(f"Error sending command: {e}\n")

    def shutdown(self):
        """Shutdown terminal process"""
        self._running = False
        try:
            if self.process and (self.process.poll() is None):
                self.process.terminate()
        except:
            pass


# ----------------------------
# Advanced Debugger
# ----------------------------
class AdvancedDebugger:
    def __init__(self, ide):
        self.ide = ide
        self.breakpoints = set()
        self.is_debugging = False
        self.current_frame = None
        self.call_stack = []
        self.variables = {}
        
    def toggle_breakpoint(self, file_path, line_number):
        """Toggle breakpoint at specified line"""
        bp_key = (file_path, line_number)
        if bp_key in self.breakpoints:
            self.breakpoints.remove(bp_key)
            self.ide.terminal._print(f"Breakpoint removed at {file_path}:{line_number}\n")
        else:
            self.breakpoints.add(bp_key)
            self.ide.terminal._print(f"Breakpoint set at {file_path}:{line_number}\n")
        
        # Update UI to show breakpoints
        self._update_breakpoint_display()
    
    def _update_breakpoint_display(self):
        """Update breakpoint display in debug panel"""
        if hasattr(self.ide, 'debug_panel'):
            self.ide.debug_panel.update_breakpoints(self.breakpoints)
    
    def start_debugging(self, file_path):
        """Start debugging session"""
        if not file_path.endswith('.py'):
            self.ide.terminal._print("Debugging only supported for Python files\n")
            return
        
        self.is_debugging = True
        self.ide.terminal._print(f"Starting debug session for {file_path}\n")
        
        # Set up debug environment
        python_executable = self.ide.get_current_interpreter('python')
        
        # Run with debug flags
        cmd = f'"{python_executable}" -m pdb {os.path.basename(file_path)}'
        self.ide.terminal.send_command(cmd)
    
    def step_over(self):
        """Step over current line"""
        if self.is_debugging:
            self.ide.terminal.send_command('next')
    
    def step_into(self):
        """Step into function call"""
        if self.is_debugging:
            self.ide.terminal.send_command('step')
    
    def step_out(self):
        """Step out of current function"""
        if self.is_debugging:
            self.ide.terminal.send_command('return')
    
    def continue_execution(self):
        """Continue execution until next breakpoint"""
        if self.is_debugging:
            self.ide.terminal.send_command('continue')
    
    def inspect_variables(self):
        """Inspect current variables"""
        if self.is_debugging:
            self.ide.terminal.send_command('args')
            self.ide.terminal.send_command('p locals()')
    
    def show_call_stack(self):
        """Show current call stack"""
        if self.is_debugging:
            self.ide.terminal.send_command('where')
    
    def stop_debugging(self):
        """Stop debugging session"""
        self.is_debugging = False
        self.ide.terminal._print("Debugging session stopped\n")

# ----------------------------
# Debug Panel
# ----------------------------
class DebugPanel(tk.Frame):
    def __init__(self, master, debugger):
        super().__init__(master, bg="#1e1e1e")
        self.debugger = debugger
        
        # Create debug controls
        self._create_controls()
        
        # Create breakpoints list
        self._create_breakpoints_list()
        
        # Create variables watch
        self._create_variables_watch()
        
        # Create call stack
        self._create_call_stack()
    
    def _create_controls(self):
        """Create debug control buttons"""
        controls_frame = tk.Frame(self, bg="#1e1e1e")
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(controls_frame, text="Start Debug", command=self.debugger.start_debugging, 
                 bg="#2d2d2d", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="Step Over", command=self.debugger.step_over,
                 bg="#2d2d2d", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="Step Into", command=self.debugger.step_into,
                 bg="#2d2d2d", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="Step Out", command=self.debugger.step_out,
                 bg="#2d2d2d", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="Continue", command=self.debugger.continue_execution,
                 bg="#2d2d2d", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="Inspect Vars", command=self.debugger.inspect_variables,
                 bg="#2d2d2d", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="Call Stack", command=self.debugger.show_call_stack,
                 bg="#2d2d2d", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="Stop", command=self.debugger.stop_debugging,
                 bg="#d32f2f", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
    
    def _create_breakpoints_list(self):
        """Create breakpoints list display"""
        bp_frame = tk.Frame(self, bg="#1e1e1e")
        bp_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(bp_frame, text="Breakpoints", bg="#1e1e1e", fg="white").pack(anchor='w')
        self.bp_listbox = tk.Listbox(bp_frame, bg="#2d2d2d", fg="white", height=4)
        self.bp_listbox.pack(fill=tk.X, pady=(5,0))
    
    def _create_variables_watch(self):
        """Create variables watch display"""
        var_frame = tk.Frame(self, bg="#1e1e1e")
        var_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(var_frame, text="Variables", bg="#1e1e1e", fg="white").pack(anchor='w')
        self.var_text = DarkScrolledText(var_frame, height=6)
        self.var_text.pack(fill=tk.X, pady=(5,0))
    
    def _create_call_stack(self):
        """Create call stack display"""
        stack_frame = tk.Frame(self, bg="#1e1e1e")
        stack_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(stack_frame, text="Call Stack", bg="#1e1e1e", fg="white").pack(anchor='w')
        self.stack_text = DarkScrolledText(stack_frame, height=6)
        self.stack_text.pack(fill=tk.BOTH, expand=True, pady=(5,0))
    
    def update_breakpoints(self, breakpoints):
        """Update breakpoints list"""
        self.bp_listbox.delete(0, tk.END)
        for bp in breakpoints:
            file_path, line_num = bp
            self.bp_listbox.insert(tk.END, f"{os.path.basename(file_path)}:{line_num}")

# ----------------------------
# IceIDE with Terminal
# ----------------------------
class IceIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Ice IDE")
        self.root.geometry("1280x860")

        # Set taskbar icon ID (Windows-specific)
        try:
            myappid = 'com.xai.iceide.1.0'  # Arbitrary string, use reverse-domain format
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass  # Ignore if not on Windows

        # Load icons and set early
        self._load_icons()
        self._set_window_icon()

        # default project dir
        self.project_dir = None
        self.current_file = None
        
        # Language interpreters configuration (will be loaded from config)
        self.interpreters = {
            'python': sys.executable,
            'javascript': 'node',
            'java': 'javac',
            'cpp': 'g++',
            'c': 'gcc',
            'rust': 'rustc',
            'go': 'go',
            'ruby': 'ruby',
            'php': 'php',
            'lua': 'lua'
        }

        # AI context storage
        self.ai_context = {}
        
        # Config setup (replaces .env)
        self.setup_config()
        
        # Initialize debugger
        self.debugger = AdvancedDebugger(self)
        self.debug_panel_visible = False

        # File system monitoring
        self._file_monitor_running = False
        self._last_tree_state = set()

        # theme
        self.style = ttkb.Style(theme="darkly")
        self._setup_styles()

        # main UI
        self._create_topbar()
        self._create_main_area()

        # REAL terminal with resizable paned window
        self.main_paned.add(self._create_terminal_area(), weight=1)
        
        # load tree (will be empty)
        self._load_project_tree()
        
        # Start file system monitoring
        self._start_file_monitor()

        # keybindings
        self.root.bind_all("<Control-s>", self._on_ctrl_s)
        self.root.bind_all("<F5>", self._on_f5)
        self.root.bind_all("<F4>", self._on_f4)
        self.root.bind_all("<F9>", self._toggle_breakpoint)
        
        # Load config and initialize Groq (after UI elements are created)
        self.load_config()
        self.auto_detect_interpreters()
        
        # Check if API key is available
        if not self.groq_api_key:
            self.open_settings()

        # Initialize Groq client
        try:
            self.groq_client = Groq(api_key=self.groq_api_key)
        except Exception as e:
            messagebox.showerror("Groq Client Error", f"Failed to initialize Groq client: {e}")

    def setup_config(self):
        """Setup config directory and path"""
        if WINDOWS:
            self.config_dir = os.path.expanduser("~\\AppData\\Roaming\\IceIDE")
        else:
            self.config_dir = os.path.expanduser("~/.config/iceide")
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, "config.json")

    def load_config(self):
        """Load configuration from JSON"""
        self.groq_api_key = ""
        self.ai_model_name = "moonshotai/kimi-k2-instruct-0905"  # Default
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    self.groq_api_key = config.get("GROQ_API_KEY", "")
                    self.ai_model_name = config.get("AI_MODEL_NAME", self.ai_model_name)
                    self.interpreters = config.get("interpreters", self.interpreters)
            except Exception as e:
                print(f"Error loading config: {e}")
        self.update_interpreter_display()

    def save_config(self):
        """Save configuration to JSON"""
        config = {
            "GROQ_API_KEY": self.groq_api_key,
            "AI_MODEL_NAME": self.ai_model_name,
            "interpreters": self.interpreters
        }
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def auto_detect_interpreters(self):
        languages = [
            ('Python', 'python', ['python', 'python3', 'py']),
            ('JavaScript', 'javascript', ['node', 'nodejs']),
            ('Java', 'java', ['javac', 'java']),
            ('C++', 'cpp', ['g++', 'clang++', 'c++']),
            ('C', 'c', ['gcc', 'clang', 'cc']),
            ('Rust', 'rust', ['rustc', 'cargo']),
            ('Go', 'go', ['go']),
            ('Ruby', 'ruby', ['ruby']),
            ('PHP', 'php', ['php']),
            ('Lua', 'lua', ['lua', 'luac'])
        ]
        for _, lang_key, common_commands in languages:
            if lang_key not in self.interpreters or shutil.which(self.interpreters[lang_key]) is None:
                for cmd in common_commands:
                    if shutil.which(cmd):
                        self.interpreters[lang_key] = cmd
                        break
        self.save_config()
        self.update_interpreter_display()

    def open_settings(self):
        """Open settings dialog for API key and model"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x200")
        settings_window.configure(bg="#1e1e1e")
        self._set_window_icon(settings_window)

        tk.Label(settings_window, text="Groq API Key:", bg="#1e1e1e", fg="white").pack(pady=5)
        key_entry = tk.Entry(settings_window, bg="#2d2d2d", fg="white", width=50)
        key_entry.insert(0, self.groq_api_key)
        key_entry.pack(pady=5)

        tk.Label(settings_window, text="AI Model Name:", bg="#1e1e1e", fg="white").pack(pady=5)
        model_entry = tk.Entry(settings_window, bg="#2d2d2d", fg="white", width=50)
        model_entry.insert(0, self.ai_model_name)
        model_entry.pack(pady=5)

        def save_settings():
            self.groq_api_key = key_entry.get().strip()
            self.ai_model_name = model_entry.get().strip()
            self.save_config()
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                messagebox.showinfo("Settings Saved", "Settings updated successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update Groq client: {e}")
            settings_window.destroy()

        tk.Button(settings_window, text="Save", command=save_settings, bg="#2d2d2d", fg="white").pack(pady=10)

    def _create_terminal_area(self):
        """Create terminal area that's resizable like other panes"""
        terminal_frame = ttk.Frame(self.main_paned)
        
        # The entire terminal (including header) is now one resizable unit
        self.terminal = RealTerminal(terminal_frame, self.project_dir, self.root)
        self.terminal.pack(fill=tk.BOTH, expand=True)
        
        return terminal_frame

    def _load_icons(self):
        """Load icons for the application"""
        # Use resource_path for bundled icons
        self.icons = {}
        icon_paths = {
            'ico': resource_path("ice.ico"),
            'png': resource_path("ice.png"),
            'icelogo': resource_path("icelogo.ico"),
            'icelogo_png': resource_path("icelogo.png")
        }
        
        # Try to create icon from PNG if ICO doesn't exist
        if not os.path.exists(icon_paths['ico']) and os.path.exists(icon_paths['png']):
            try:
                from PIL import Image
                img = Image.open(icon_paths['png'])
                img.save(icon_paths['ico'], format="ICO")
            except:
                pass
        
        # Similar for icelogo
        if not os.path.exists(icon_paths['icelogo']) and os.path.exists(icon_paths['icelogo_png']):
            try:
                from PIL import Image
                img = Image.open(icon_paths['icelogo_png'])
                img.save(icon_paths['icelogo'], format="ICO")
            except:
                pass

    def _set_window_icon(self, window=None):
        """Set window icon for all dialogs"""
        if window is None:
            window = self.root
            
        # Use resource_path for icon files, prioritize icelogo.ico
        icon_paths = [
            resource_path("icelogo.ico"),
            resource_path("ice.ico"),
            resource_path("icelogo.png"),
            resource_path("ice.png")
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    if icon_path.endswith('.ico'):
                        window.iconbitmap(icon_path)
                    else:
                        photo = tk.PhotoImage(file=icon_path)
                        window.iconphoto(True, photo)
                        if window == self.root:  # Only keep reference for main window
                            self._title_icon = photo
                    break
                except:
                    continue

    def _start_file_monitor(self):
        """Start monitoring file system for changes"""
        self._file_monitor_running = True
        self._monitor_files()

    def _monitor_files(self):
        """Monitor files for changes and update treeview"""
        if not self._file_monitor_running:
            return
            
        try:
            current_files = set()
            if self.project_dir:
                for root_dir, dirs, files in os.walk(self.project_dir):
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root_dir, file), self.project_dir)
                        current_files.add(rel_path)
                    for dir_name in dirs:
                        rel_path = os.path.relpath(os.path.join(root_dir, dir_name), self.project_dir)
                        current_files.add(rel_path + os.sep)  # Mark directories with separator

            # Check if tree needs updating
            if current_files != self._last_tree_state:
                self._load_project_tree()
                self._last_tree_state = current_files
                
        except Exception as e:
            print(f"File monitoring error: {e}")
            
        # Schedule next check
        if self._file_monitor_running:
            self.root.after(1000, self._monitor_files)

    def _setup_styles(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass
        
        # Configure consistent dark scrollbars for all widgets
        s.configure("Vertical.TScrollbar",
                   background="#2d2d2d",
                   troughcolor="#1e1e1e", 
                   bordercolor="#1e1e1e",
                   arrowcolor="#ffffff",
                   relief="flat")
        
        s.configure("Horizontal.TScrollbar",
                   background="#2d2d2d",
                   troughcolor="#1e1e1e",
                   bordercolor="#1e1e1e",
                   arrowcolor="#ffffff",
                   relief="flat")
        
        s.map("Vertical.TScrollbar",
              background=[("active", "#3d3d3d")])
        
        s.map("Horizontal.TScrollbar",
              background=[("active", "#3d3d3d")])
        
        s.configure("Topbar.TFrame", background="#1e1e1e")
        s.configure("Topbar.TButton", background="#1e1e1e", foreground="#ffffff", borderwidth=0)
        s.map("Topbar.TButton", background=[("active", "#2b2b2b")], foreground=[("active", "#ffffff")])
        s.configure("Custom.Treeview", 
                    background="#232323", 
                    foreground="#d4d4d4", 
                    fieldbackground="#232323",
                    borderwidth=0)
        s.map("Custom.Treeview", 
              background=[("selected", "#2d2d2d"), ("!focus", "#232323")],
              foreground=[("selected", "#ffffff"), ("!focus", "#d4d4d4")])
        s.configure("Custom.Treeview.Heading", 
                    background="#232323", 
                    foreground="#d4d4d4")
        s.map("Custom.Treeview.Heading",
              background=[("active", "#2b2b2b")],
              foreground=[("active", "#ffffff")])

    def _create_topbar(self):
        self.topbar = ttk.Frame(self.root, style="Topbar.TFrame")
        self.topbar.pack(side=tk.TOP, fill=tk.X)

        # File / Tools / Settings buttons
        self.file_btn = ttk.Button(self.topbar, text="File", style="Topbar.TButton", command=self._show_file_menu)
        self.file_btn.pack(side=tk.LEFT, padx=(8,4), pady=6)

        self.tools_btn = ttk.Button(self.topbar, text="Tools", style="Topbar.TButton", command=self._show_tools_menu)
        self.tools_btn.pack(side=tk.LEFT, padx=4, pady=6)

        self.settings_btn = ttk.Button(self.topbar, text="Settings", style="Topbar.TButton", command=self.open_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=4, pady=6)

        # Run button
        self.run_btn = ttk.Button(self.topbar, text="Run", style="Topbar.TButton", command=self.run_code)
        self.run_btn.pack(side=tk.RIGHT, padx=8, pady=6)

        # Interpreter selector
        self.interpreter_btn = ttk.Button(self.topbar, text="Python: System", style="Topbar.TButton", 
                                         command=self.select_interpreter)
        self.interpreter_btn.pack(side=tk.RIGHT, padx=4, pady=6)

        # indicator: venv path + Ice 1.0
        self.indicator_var = tk.StringVar()
        self.indicator = tk.Label(self.topbar, textvariable=self.indicator_var, bg="#1e1e1e", fg="#bdbdbd")
        self.indicator.pack(side=tk.RIGHT, padx=8)
        self.update_indicator()

        # file menu
        self.file_menu = tk.Menu(self.root, tearoff=0, bg="#1e1e1e", fg="#ffffff",
                                 activebackground="#333333", activeforeground="#ffffff")
        self.file_menu.add_command(label="New File", command=self.new_file_dialog)
        self.file_menu.add_command(label="Open File...", command=self.open_file_dialog)
        self.file_menu.add_command(label="Save", command=self.save_current_tab)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Open Folder...", command=self.open_folder_dialog)
        self.file_menu.add_command(label="New Folder (Switch To)...", command=self.new_folder_dialog)
        self.file_menu.add_command(label="Close Folder", command=self.close_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Close Tab", command=self.close_current_tab)
        self.file_menu.add_command(label="Close All Tabs", command=self.close_all_tabs)

        # tools menu
        self.tools_menu = tk.Menu(self.root, tearoff=0, bg="#1e1e1e", fg="#ffffff",
                                  activebackground="#333333", activeforeground="#ffffff")
        self.tools_menu.add_command(label="Create Venv", command=self.create_venv)
        self.tools_menu.add_command(label="Select Interpreter", command=self.select_interpreter)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="Toggle Debug Panel", command=self.toggle_debug_panel)
        self.tools_menu.add_command(label="Advanced Debug Tools", command=self.show_advanced_debug)

    def _show_file_menu(self):
        x = self.file_btn.winfo_rootx()
        y = self.file_btn.winfo_rooty() + self.file_btn.winfo_height()
        self.file_menu.tk_popup(x, y)

    def _show_tools_menu(self):
        x = self.tools_btn.winfo_rootx()
        y = self.tools_btn.winfo_rooty() + self.tools_btn.winfo_height()
        self.tools_menu.tk_popup(x, y)

    def _create_main_area(self):
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # Editor and explorer area
        self.editor_paned = ttk.PanedWindow(self.main_paned, orient=tk.HORIZONTAL)
        self.main_paned.add(self.editor_paned, weight=3)

        # Left pane for file explorer and debug panel
        self.left_paned = ttk.PanedWindow(self.editor_paned, orient=tk.VERTICAL)
        self.editor_paned.add(self.left_paned, weight=1)

        # file explorer frame
        self.file_frame = ttk.Frame(self.left_paned, width=280, style="Topbar.TFrame")
        self.left_paned.add(self.file_frame, weight=2)
        
        # Explorer label
        explorer_label = tk.Label(self.file_frame, text="EXPLORER", bg="#1e1e1e", fg="#888888", 
                                 font=("Segoe UI", 9, "bold"), anchor='w')
        explorer_label.pack(fill=tk.X, padx=8, pady=(8,4))
        
        self.tree = ttk.Treeview(self.file_frame, style="Custom.Treeview", show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.tree.bind("<Double-1>", self._on_tree_double)
        self.tree.bind("<Button-1>", self._on_tree_click)

        # add right-click menu for tree
        self.tree_menu = tk.Menu(self.root, tearoff=0, bg="#1e1e1e", fg="#ffffff")
        self.tree_menu.add_command(label="Open", command=self._open_tree_selection)
        self.tree_menu.add_command(label="Refresh", command=self._load_project_tree)
        self.tree_menu.add_command(label="Delete", command=self._delete_tree_selection)
        self.tree.bind("<Button-3>", self._on_tree_right_click)

        # Debug panel (initially hidden)
        self.debug_panel_frame = ttk.Frame(self.left_paned, style="Topbar.TFrame")
        self.debug_panel = DebugPanel(self.debug_panel_frame, self.debugger)
        self.debug_panel.pack(fill=tk.BOTH, expand=True)

        # notebook for tabs
        self.notebook = ttk.Notebook(self.editor_paned)
        self.editor_paned.add(self.notebook, weight=4)
        self.tab_files = {}
        self.tab_widgets = {}
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tree_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree_menu.tk_popup(event.x_root, event.y_root)

    def _delete_tree_selection(self):
        sel = self.tree.selection()
        if not sel:
            return
        path = self.tree.item(sel[0], "values")[0]
        if messagebox.askyesno("Delete", f"Are you sure you want to delete {os.path.basename(path)}?"):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                self._load_project_tree()
            except Exception as e:
                messagebox.showerror("Delete Error", str(e))

    def _load_project_tree(self):
        """Load project tree with real-time updates"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.project_dir:
            return
        try:
            self._populate_folder("", self.project_dir)
            # Store current state for monitoring
            self._last_tree_state = self._get_current_tree_state()
        except Exception as e:
            print(f"Error loading project tree: {e}")

    def _get_current_tree_state(self):
        """Get current tree state for monitoring"""
        current_state = set()
        for root_dir, dirs, files in os.walk(self.project_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root_dir, file), self.project_dir)
                current_state.add(rel_path)
            for dir_name in dirs:
                rel_path = os.path.relpath(os.path.join(root_dir, dir_name), self.project_dir)
                current_state.add(rel_path + os.sep)
        return current_state

    def _populate_folder(self, parent_iid, folder_path):
        """Populate folder in treeview"""
        try:
            for entry in sorted(os.listdir(folder_path)):
                # Skip venv directory unless specifically requested
                if entry == 'venv' and parent_iid == "":
                    continue
                    
                full = os.path.join(folder_path, entry)
                iid = f"{parent_iid}/{entry}" if parent_iid else entry
                self.tree.insert(parent_iid, tk.END, iid=iid, text=entry, values=(full,))
                if os.path.isdir(full) and entry != 'venv':  # Don't auto-expand venv
                    self.tree.insert(iid, tk.END)  # Add dummy to make expandable
        except Exception as e:
            print(f"Error populating folder: {e}")

    def _on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        path = self.tree.item(item, "values")[0]
        if os.path.isdir(path):
            self._populate_folder(item, path)

    def _on_tree_double(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        vals = self.tree.item(iid, "values")
        if not vals:
            return
        path = vals[0]
        if os.path.isdir(path):
            self._populate_folder(iid, path)
        else:
            self.open_file_in_tab(path)

    def _open_tree_selection(self):
        sel = self.tree.selection()
        if not sel:
            return
        path = self.tree.item(sel[0], "values")[0]
        if os.path.isfile(path):
            self.open_file_in_tab(path)

    def open_file_in_tab(self, path):
        abs_path = os.path.abspath(path)
        for tab_id, fp in self.tab_files.items():
            if os.path.abspath(fp) == abs_path:
                try:
                    self.notebook.select(tab_id)
                except Exception:
                    pass
                return

        tab_frame = ttk.Frame(self.notebook)
        
        # Create editor with line numbers
        ds = DarkScrolledText(tab_frame, wrap="word")
        ds.pack(fill=tk.BOTH, expand=True)
        
        # syntax highlighting
        ds.text.tag_configure("parentheses", foreground="#87cefa")   # light sky blue
        ds.text.tag_configure("number", foreground="#1e90ff")        # dodger blue
        ds.text.tag_configure("string", foreground="#b0e0e6")        # powder blue
        ds.text.tag_configure("true", foreground="#90ee90")          # light green
        ds.text.tag_configure("false", foreground="#ff7f7f")         # light red
        ds.text.tag_configure("breakpoint", background="#3a1f1f", foreground="#ff6b6b")

# New ones
        ds.text.tag_configure("keyword", foreground="#569cd6")       # blue (VSCode keyword)
        ds.text.tag_configure("datatype", foreground="#4ec9b0")      # aqua (types)
        ds.text.tag_configure("function", foreground="#dcdcaa")      # yellow-ish (functions)
        ds.text.tag_configure("comment", foreground="#6a9955")       # green (comments)

# Re-run highlighting on typing and clicking
        ds.text.bind("<KeyRelease>", lambda e, tw=ds.text: self._apply_syntax_highlighting_for_widget(tw))
        ds.text.bind("<Button-1>", self._on_text_click)

        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Open file error", str(e))
            return
        ds.text.insert("1.0", content)

        tab_text = os.path.basename(path)
        self.notebook.add(tab_frame, text=tab_text)
        tabs = self.notebook.tabs()
        if not tabs:
            return
        tab_id = tabs[-1]
        self.tab_files[tab_id] = abs_path
        self.tab_widgets[tab_id] = tab_frame
        tab_frame._ds = ds
        self.notebook.select(tab_id)
        self._apply_syntax_highlighting_for_widget(ds.text)
        self._load_project_tree()  # Refresh tree to show any new files
        self.update_interpreter_button()

    def _on_text_click(self, event):
        """Handle text click for breakpoint toggling"""
        text_widget = event.widget
        index = text_widget.index(f"@{event.x},{event.y}")
        line_start = index.split('.')[0] + '.0'
        
        # Toggle breakpoint visual
        current_tags = text_widget.tag_names(line_start)
        if "breakpoint" in current_tags:
            text_widget.tag_remove("breakpoint", line_start, line_start + " lineend")
        else:
            text_widget.tag_add("breakpoint", line_start, line_start + " lineend")

    def _toggle_breakpoint(self, event=None):
        """Toggle breakpoint at current line"""
        sel = self.notebook.select()
        if not sel or sel not in self.tab_files:
            return
            
        file_path = self.tab_files[sel]
        frame = self.tab_widgets.get(sel)
        if not frame or not hasattr(frame, "_ds"):
            return
            
        text_widget = frame._ds.text
        current_index = text_widget.index(tk.INSERT)
        line_number = int(current_index.split('.')[0])
        
        self.debugger.toggle_breakpoint(file_path, line_number)

    def new_file_dialog(self):
        if not self.project_dir:
            messagebox.showerror("No Folder", "Please open a folder first.")
            return
        p = filedialog.asksaveasfilename(initialdir=self.project_dir, defaultextension=".gust",
                                         filetypes=[("Gust files", "*.gust"), ("All files", "*.*")])
        if p:
            open(p, "w").close()
            self._load_project_tree()  # Refresh to show new file
            self.open_file_in_tab(p)

    def open_file_dialog(self):
        p = filedialog.askopenfilename(initialdir=self.project_dir or os.path.expanduser("~"), filetypes=[("All files", "*.*")])
        if p:
            self.open_file_in_tab(p)

    def save_current_tab(self):
        sel = self.notebook.select()
        if not sel:
            messagebox.showinfo("Save", "No tab selected")
            return
        tab_id = sel
        if tab_id not in self.tab_files:
            messagebox.showerror("Save", "Tab is not associated with a file")
            return
        path = self.tab_files[tab_id]
        frame = self.tab_widgets.get(tab_id)
        if not frame or not hasattr(frame, "_ds"):
            messagebox.showerror("Save", "Editor not found")
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(frame._ds.text.get("1.0", tk.END).rstrip() + "\n")
            self._flash_status(f"Saved {os.path.basename(path)}")
            self._load_project_tree()  # Refresh tree after save
        except Exception as e:
            messagebox.showerror("Save error", str(e))

    def close_current_tab(self):
        sel = self.notebook.select()
        if not sel:
            return
        tab_id = sel
        self._close_tab_by_id(tab_id)

    def _close_tab_by_id(self, tab_id):
        if tab_id in self.tab_files:
            del self.tab_files[tab_id]
        if tab_id in self.tab_widgets:
            del self.tab_widgets[tab_id]
        try:
            self.notebook.forget(tab_id)
        except Exception:
            pass

    def close_all_tabs(self):
        for tab_id in list(self.notebook.tabs()):
            self._close_tab_by_id(tab_id)

    def _on_tab_changed(self, event):
        sel = self.notebook.select()
        if not sel:
            self.current_file = None
            self.update_interpreter_button()
            return
        tab_id = sel
        self.current_file = self.tab_files.get(tab_id, None)
        frame = self.tab_widgets.get(tab_id)
        if frame and hasattr(frame, "_ds"):
            self._apply_syntax_highlighting_for_widget(frame._ds.text)
        self.update_interpreter_button()

    def _apply_syntax_highlighting_for_widget(self, text_widget):
        content = text_widget.get("1.0", tk.END)

    # Clear all old tags
        for tag in ("parentheses", "number", "string", "true", "false", 
                    "breakpoint", "keyword", "datatype", "function", "comment"):
            text_widget.tag_remove(tag, "1.0", tk.END)

    # Parentheses, brackets, braces
        for m in re.finditer(r'[\(\)\<\>\[\]\{\}]', content):
            text_widget.tag_add("parentheses", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    # Numbers
        for m in re.finditer(r'\b\d+(\.\d+)?\b', content):
            text_widget.tag_add("number", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    # Strings
        for m in re.finditer(r'"[^"]*"|\'[^\']*\'', content):
            text_widget.tag_add("string", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    # Booleans
        for m in re.finditer(r'\bTrue\b', content):
            text_widget.tag_add("true", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for m in re.finditer(r'\bFalse\b', content):
            text_widget.tag_add("false", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    # Keywords
        keywords = r"\b(def|class|if|else|elif|for|while|break|continue|return|yield|try|except|finally|with|as|import|from|pass|in|not|and|or|async|await|switch|case|default|throw|catch)\b"
        for m in re.finditer(keywords, content):
            text_widget.tag_add("keyword", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    # Data types
        datatypes = r"\b(int|float|double|char|bool|boolean|string|str|list|array|dict|map|set|tuple|object|null|None|undefined|NaN|void)\b"
        for m in re.finditer(datatypes, content):
            text_widget.tag_add("datatype", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    # Common functions
        functions = r"\b(print|input|len|range|open|read|write|append|insert|remove|replace|sort|filter|map|reduce|push|pop|join|split|format)\b"
        for m in re.finditer(functions, content):
            text_widget.tag_add("function", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    # Comments
        for m in re.finditer(r"#.*|//.*|/\*[\s\S]*?\*/", content):
            text_widget.tag_add("comment", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    def new_folder_dialog(self):
        folder = filedialog.askdirectory(initialdir=os.path.expanduser("~"))
        if not folder:
            return
        self.project_dir = folder
        os.makedirs(self.project_dir, exist_ok=True)
        self._load_project_tree()
        self._reset_terminal()
        self._check_and_activate_venv()

    def open_folder_dialog(self):
        folder = filedialog.askdirectory(initialdir=os.path.expanduser("~"))
        if not folder:
            return
        self.project_dir = folder
        os.makedirs(self.project_dir, exist_ok=True)
        self._load_project_tree()
        self._reset_terminal()
        self._check_and_activate_venv()

    def close_folder(self):
        if not messagebox.askyesno("Close folder", "Close current folder?"):
            return
        self.current_file = None
        self.project_dir = None
        self.interpreters['python'] = sys.executable  # Reset to system python
        self.save_config()
        self._load_project_tree()
        self.close_all_tabs()
        self._reset_terminal()

    def _check_and_activate_venv(self):
        if not self.project_dir:
            return
        venv_path = os.path.join(self.project_dir, "venv")
        if os.path.exists(venv_path):
            python_bin = 'Scripts' if WINDOWS else 'bin'
            python_exe = 'python.exe' if WINDOWS else 'python'
            venv_python = os.path.join(venv_path, python_bin, python_exe)
            if os.path.exists(venv_python):
                self.interpreters['python'] = venv_python
                self.save_config()
                # Activate in terminal
                if WINDOWS:
                    self.terminal.send_command(r'venv\Scripts\activate.bat')
                else:
                    self.terminal.send_command('source venv/bin/activate')
                self.terminal._print("Virtual environment activated.\n")
            self.update_interpreter_display()
            self.update_indicator()

    def _reset_terminal(self):
        """Reset terminal with the new project directory"""
        try:
            # Shutdown old terminal if it exists
            if hasattr(self, 'terminal'):
                try:
                    self.terminal.shutdown()
                except:
                    pass
            
            # Find the terminal pane in the main paned window
            panes = self.main_paned.panes()
            terminal_pane_index = None
            
            for i, pane in enumerate(panes):
                pane_widget = self.root.nametowidget(pane)
                # Check if this pane contains a terminal
                if hasattr(pane_widget, 'winfo_children') and pane_widget.winfo_children():
                    for child in pane_widget.winfo_children():
                        if hasattr(child, 'shutdown'):
                            # Found the terminal pane
                            terminal_pane_index = i
                            break
                if terminal_pane_index is not None:
                    break
            
            # If we found a terminal pane, remove it
            if terminal_pane_index is not None:
                # Get the terminal frame before removing
                terminal_frame = self.root.nametowidget(panes[terminal_pane_index])
                
                # Remove the terminal pane
                self.main_paned.remove(terminal_frame)
                
                # Destroy the old terminal frame
                terminal_frame.destroy()
            
            # Create new terminal area
            new_terminal_frame = self._create_terminal_area()
            
            # Add the new terminal to the main paned window
            self.main_paned.add(new_terminal_frame, weight=1)
            
            # Update the terminal reference
            self.terminal = new_terminal_frame.winfo_children()[0]
            
            self.update_indicator()
            
        except Exception as e:
            print(f"Error resetting terminal: {e}")

    def create_venv(self):
        """Create virtual environment only when explicitly requested"""
        if not self.project_dir:
            messagebox.showerror("No Folder", "Please open a folder first.")
            return
        venv_path = os.path.join(self.project_dir, "venv")
        if os.path.exists(venv_path):
            if messagebox.askyesno("Venv Exists", "Virtual environment already exists. Recreate?"):
                shutil.rmtree(venv_path)
            else:
                return
        try:
            python_exec = self.get_current_interpreter('python')
            # Use check_call wrapper to avoid showing a console on Windows
            _subprocess_check_call([python_exec, "-m", "venv", "venv"], cwd=self.project_dir)
            # Set interpreter to venv python
            python_bin = 'Scripts' if WINDOWS else 'bin'
            python_exe = 'python.exe' if WINDOWS else 'python'
            self.interpreters['python'] = os.path.join(venv_path, python_bin, python_exe)
            self.save_config()
            # Activate the venv in the terminal
            if WINDOWS:
                self.terminal.send_command(r'venv\Scripts\activate.bat')
            else:
                self.terminal.send_command('source venv/bin/activate')
            self.update_interpreter_display()
            messagebox.showinfo("Venv Created", "Virtual environment created and activated successfully!")
            self._load_project_tree()  # Refresh to show venv folder
        except Exception as e:
            messagebox.showerror("Venv error", str(e))

    def detect_language_from_file(self, file_path):
        """Detect programming language from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.c': 'c',
            '.rs': 'rust',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.lua': 'lua',
            '.html': 'html',
            '.css': 'css',
            '.gust': 'gust'
        }
        return language_map.get(ext, 'unknown')

    def get_current_interpreter(self, language):
        """Get the current interpreter for a specific language"""
        interp = self.interpreters.get(language, language)  # Default to command name if not found
        if language == 'python' and getattr(sys, 'frozen', False) and interp == sys.executable:
            system_python = shutil.which('python') or shutil.which('python3')
            if system_python:
                interp = system_python
            else:
                messagebox.showerror("Error", "No system Python interpreter found.")
                return None
        # Resolve to absolute path if possible
        abs_interp = shutil.which(interp)
        return abs_interp if abs_interp else interp

    def select_interpreter(self):
        """Select interpreter for any programming language"""
        # Create selection dialog
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Select Language Interpreter")
        selection_window.geometry("600x400")
        selection_window.configure(bg="#1e1e1e")
        self._set_window_icon(selection_window)  # Set icon for this window too
        
        tk.Label(selection_window, text="Select Language Interpreters:", 
                bg="#1e1e1e", fg="white", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Create notebook for different languages
        notebook = ttk.Notebook(selection_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Common languages
        languages = [
            ('Python', 'python', ['python', 'python3', 'py']),
            ('JavaScript', 'javascript', ['node', 'nodejs']),
            ('Java', 'java', ['javac', 'java']),
            ('C++', 'cpp', ['g++', 'clang++', 'c++']),
            ('C', 'c', ['gcc', 'clang', 'cc']),
            ('Rust', 'rust', ['rustc', 'cargo']),
            ('Go', 'go', ['go']),
            ('Ruby', 'ruby', ['ruby']),
            ('PHP', 'php', ['php']),
            ('Lua', 'lua', ['lua', 'luac'])
        ]
        
        interpreter_vars = {}
        custom_entries = {}
        
        for lang_name, lang_key, common_commands in languages:
            # Create frame for each language
            lang_frame = ttk.Frame(notebook)
            notebook.add(lang_frame, text=lang_name)
            
            tk.Label(lang_frame, text=f"Select {lang_name} interpreter:", 
                    bg="#1e1e1e", fg="white").pack(anchor='w', pady=5)
            
            # Current interpreter info
            current_interpreter = self.interpreters.get(lang_key, common_commands[0])
            current_var = tk.StringVar(value=current_interpreter if current_interpreter in common_commands else "custom")
            interpreter_vars[lang_key] = current_var
            
            # Common interpreters frame
            common_frame = tk.Frame(lang_frame, bg="#1e1e1e")
            common_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(common_frame, text="Common:", bg="#1e1e1e", fg="white").pack(anchor='w')
            
            # Radio buttons for common interpreters
            for cmd in common_commands:
                # Check if command exists
                try:
                    _subprocess_run([cmd, '--version'], capture_output=True, timeout=2)
                    exists = True
                except:
                    exists = False
                
                if exists:
                    rb = tk.Radiobutton(common_frame, text=cmd, variable=current_var, value=cmd,
                                      bg="#1e1e1e", fg="white", selectcolor="#2d2d2d")
                    rb.pack(anchor='w', padx=20)
            
            # Custom interpreter
            custom_frame = tk.Frame(lang_frame, bg="#1e1e1e")
            custom_frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Radiobutton(custom_frame, text="Custom path:", variable=current_var, value="custom",
                          bg="#1e1e1e", fg="white", selectcolor="#2d2d2d").pack(anchor='w')
            
            custom_entry = tk.Entry(custom_frame, bg="#2d2d2d", fg="white", width=50)
            custom_entry.pack(fill=tk.X, pady=5)
            custom_entries[lang_key] = custom_entry
            
            # Set custom entry if current is not a common command
            if current_var.get() == "custom":
                custom_entry.insert(0, current_interpreter)
            
            def create_browse_handler(entry, var):
                def handler():
                    path = filedialog.askopenfilename(title=f"Select {lang_name} Interpreter")
                    if path:
                        entry.delete(0, tk.END)
                        entry.insert(0, path)
                        var.set("custom")
                return handler
            
            tk.Button(custom_frame, text="Browse", 
                     command=create_browse_handler(custom_entry, current_var),
                     bg="#2d2d2d", fg="white").pack(anchor='w')
        
        def on_ok():
            # Update all interpreters
            for lang_key, var in interpreter_vars.items():
                if var.get() == "custom":
                    custom_value = custom_entries[lang_key].get().strip()
                    if custom_value:
                        self.interpreters[lang_key] = custom_value
                else:
                    self.interpreters[lang_key] = var.get()
            
            self.save_config()
            # Update UI
            self.update_interpreter_display()
            selection_window.destroy()
        
        # Control buttons
        btn_frame = tk.Frame(selection_window, bg="#1e1e1e")
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(btn_frame, text="OK", command=on_ok, 
                 bg="#2d2d2d", fg="white").pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=selection_window.destroy,
                 bg="#2d2d2d", fg="white").pack(side=tk.RIGHT, padx=5)

    def update_interpreter_display(self):
        """Update the interpreter button display"""
        self.update_interpreter_button()

    def update_interpreter_button(self):
        """Update interpreter button based on current file"""
        if self.current_file:
            language = self.detect_language_from_file(self.current_file)
            interpreter = self.get_current_interpreter(language)
            if interpreter:
                interp_name = os.path.basename(interpreter)
                self.interpreter_btn.config(text=f"{language.capitalize()}: {interp_name}")
            else:
                self.interpreter_btn.config(text=f"{language.capitalize()}: Not Found")
        else:
            self.interpreter_btn.config(text="Interpreter: None")

    def update_indicator(self):
        """Update status indicator with current interpreter info"""
        python_interpreter = self.interpreters.get('python', 'python')
        python_name = os.path.basename(python_interpreter)
        if self.project_dir:
            venv_path = os.path.join(self.project_dir, "venv")
        else:
            venv_path = ""
        
        if venv_path and os.path.exists(venv_path) and "venv" in python_interpreter.lower():
            indicator = f"venv: {python_name} | Ice 1.0"
        else:
            indicator = f"system: {python_name} | Ice 1.0"
        self.indicator_var.set(indicator)

    def toggle_debug_panel(self):
        """Toggle debug panel visibility"""
        if self.debug_panel_visible:
            self.left_paned.forget(self.debug_panel_frame)
            self.debug_panel_visible = False
        else:
            self.left_paned.add(self.debug_panel_frame, weight=1)
            self.debug_panel_visible = True

    def show_advanced_debug(self):
        """Show advanced debug tools"""
        self.toggle_debug_panel()
        self.terminal._print("Advanced debug tools activated. Use F9 to toggle breakpoints.\n")

    # -------------------- ENHANCED AI FEATURES WITH CONFIG --------------------
    
    def _call_groq_api(self, messages, temperature=0.7, max_tokens=2048):
        """Enhanced Groq API call with error handling using config"""
        try:
            completion = self.groq_client.chat.completions.create(
                model=self.ai_model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            content = completion.choices[0].message.content.strip()
            # Clean markdown code blocks
            content = re.sub(r'^```(?:\w+)?\s*', '', content, flags=re.I)
            content = re.sub(r'\s*```$', '', content, flags=re.I)
            return content
        except Exception as e:
            if "rate limit" in str(e).lower() or "server" in str(e).lower():
                return "Temporary Server Down: Come back later or use another IDE!"
            else:
                return f"ERROR: {str(e)}"

    def process_gust_file(self, content, file_path):
        """Process .gust file with AI translation"""
        lines = content.split('\n')
        
        # Extract target language from first line
        target_language = "python"
        if lines and lines[0].startswith('<') and lines[0].endswith('>'):
            target_language = lines[0][1:-1].lower()
            content = '\n'.join(lines[1:])
        
        # Extract ice.prompt() context
        prompt_text = None
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('ice.prompt(') and stripped.endswith(')'):
                try:
                    prompt_text = stripped[11:-2].strip('"\'')
                except:
                    pass
            else:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
        
        # Prepare AI messages
        system_msg = f"Translate this pseudocode to {target_language}. Return only the corrected code without explanations, comments, backticks, or markdown."
        if prompt_text:
            system_msg += f"The user's intent: {prompt_text}"
        else:
            system_msg += "The user's intent: No specific prompt provided"
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": content}
        ]
        
        result = self._call_groq_api(messages)
        
        if result.startswith("ERROR") or "Server Down" in result:
            self.terminal._print(result)
            return None
        
        # Save translated file
        base_name = file_path.replace('.gust', '')
        target_ext = self.get_file_extension(target_language)
        output_file = f"{base_name}{target_ext}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        # Refresh tree to show new file
        self._load_project_tree()
        
        return output_file, target_language

    def debug_with_ai(self, content, file_path):
        """Universal debugging with ice.gust()"""
        lines = content.split('\n')
        actual_code = '\n'.join(lines[1:])  # Remove ice.gust() line
        
        messages = [
            {"role": "system", "content": "Fix all bugs, errors, and syntax issues in this code. Return only the corrected code without explanations, comments, backticks, or markdown."},
            {"role": "user", "content": actual_code}
        ]
        
        result = self._call_groq_api(messages, temperature=0.3)
        
        if result.startswith("ERROR") or "Server Down" in result:
            self.terminal._print(result)
            return None
        
        return result

    def get_file_extension(self, language):
        extensions = {
            'python': '.py', 'py': '.py',
            'javascript': '.js', 'js': '.js',
            'html': '.html',
            'css': '.css',
            'ruby': '.rb', 'rb': '.rb',
            'lua': '.lua',
            'c#': '.cs', 'cs': '.cs',
            'c++': '.cpp', 'cpp': '.cpp',
            'java': '.java',
            'php': '.php',
            'rust': '.rs',
            'go': '.go',
            'swift': '.swift'
        }
        return extensions.get(language.lower(), '.txt')

    def run_code(self):
        """Enhanced run code with Gust and AI features"""
        sel = self.notebook.select()
        if not sel:
            messagebox.showerror("No file", "Open a file in a tab first.")
            return
        
        tab_id = sel
        if tab_id not in self.tab_files:
            messagebox.showerror("Run", "Selected tab is not associated with a file.")
            return
        
        file_path = self.tab_files[tab_id]
        abs_file_path = os.path.abspath(file_path)
        frame = self.tab_widgets.get(tab_id)
        if not frame or not hasattr(frame, "_ds"):
            messagebox.showerror("Run", "Editor widget missing.")
            return
        
        # Save current content
        try:
            content = frame._ds.text.get("1.0", tk.END).rstrip() + "\n"
            with open(abs_file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            messagebox.showerror("Save error", str(e))
            return

        # Detect language from file extension
        language = self.detect_language_from_file(file_path)
        interpreter = self.get_current_interpreter(language)

        if not interpreter and language not in ['html', 'css']:
            self.terminal._print(f"Error: Interpreter for {language} not found.\n")
            return

        # Check for Gust file
        if file_path.endswith('.gust'):
            self.terminal._print("Processing Gust file with AI...")
            result = self.process_gust_file(content, abs_file_path)
            if result:
                output_file, target_language = result
                abs_output_file = os.path.abspath(output_file)
                self.terminal._print(f"Translated to {target_language}. Saved as: {output_file}")
                # Execute the translated code
                target_interpreter = self.get_current_interpreter(target_language)
                if not target_interpreter:
                    self.terminal._print(f"Error: Interpreter for {target_language} not found.\n")
                    return
                if target_language in ['python', 'py']:
                    self.terminal.send_command(f'"{target_interpreter}" "{abs_output_file}"')
                elif target_language in ['javascript', 'js']:
                    self.terminal.send_command(f'"{target_interpreter}" "{abs_output_file}"')
                elif target_language in ['java']:
                    self.terminal.send_command(f'"{target_interpreter}" "{abs_output_file}"')
                return

        # Check for ice.gust() debugging
        lines = content.split('\n')
        if lines and lines[0].strip() == 'ice.gust()':
            self.terminal._print("AI debugging and fixing code...")
            fixed_code = self.debug_with_ai(content, abs_file_path)
            if fixed_code:
                # Replace editor content
                frame._ds.delete("1.0", tk.END)
                frame._ds.insert("1.0", fixed_code)
                # Save the fixed code
                with open(abs_file_path, "w", encoding="utf-8") as f:
                    f.write(fixed_code)
                self.terminal._print("Code fixed successfully!")
                content = fixed_code  # Use fixed code for execution
                self._load_project_tree()  # Refresh tree

        # Regular code execution based on file type
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.py':
            self.terminal.send_command(f'"{interpreter}" "{abs_file_path}"')
        elif ext == '.js':
            self.terminal.send_command(f'"{interpreter}" "{abs_file_path}"')
        elif ext == '.java':
            # Compile then run
            class_name = os.path.basename(file_path).replace('.java', '')
            self.terminal.send_command(f'"{interpreter}" "{abs_file_path}"')
            self.terminal.send_command(f'java "{class_name}"')
        elif ext in ['.cpp', '.cc', '.c']:
            # Compile C/C++ then run
            output_name = os.path.basename(file_path).replace(ext, '')
            self.terminal.send_command(f'"{interpreter}" "{abs_file_path}" -o "{output_name}"')
            self.terminal.send_command(f'./"{output_name}"')
        elif ext == '.rs':
            # Compile Rust then run
            output_name = os.path.basename(file_path).replace('.rs', '')
            self.terminal.send_command(f'"{interpreter}" "{abs_file_path}" -o "{output_name}"')
            self.terminal.send_command(f'./"{output_name}"')
        elif ext == '.go':
            self.terminal.send_command(f'"{interpreter}" run "{abs_file_path}"')
        elif ext == '.rb':
            self.terminal.send_command(f'"{interpreter}" "{abs_file_path}"')
        elif ext == '.php':
            self.terminal.send_command(f'"{interpreter}" "{abs_file_path}"')
        elif ext == '.lua':
            self.terminal.send_command(f'"{interpreter}" "{abs_file_path}"')
        elif ext in ['.html', '.css']:
            if os.name == 'nt':
                self.terminal.send_command(f'start "" "{abs_file_path}"')
            elif sys.platform == 'darwin':
                self.terminal.send_command(f'open "{abs_file_path}"')
            else:
                self.terminal.send_command(f'xdg-open "{abs_file_path}"')
        else:
            self.terminal._print(f"Unsupported file type: {ext}")

    def _flash_status(self, text, duration=1000):
        old = self.indicator_var.get()
        self.indicator_var.set(text)
        self.root.after(duration, lambda: self.indicator_var.set(old))

    def _on_ctrl_s(self, event=None):
        self.save_current_tab()
        return "break"

    def _on_f5(self, event=None):
        self.run_code()
        return "break"

    def _on_f4(self, event=None):
        self.close_current_tab()
        return "break"

    def __del__(self):
        """Cleanup when IDE is closed"""
        self._file_monitor_running = False
        if hasattr(self, 'terminal'):
            self.terminal.shutdown()

# ----------------------------
# Run Ice IDE
# ----------------------------
if __name__ == "__main__":
    root = ttkb.Window(themename="darkly")
    app = IceIDE(root)
    root.mainloop()
